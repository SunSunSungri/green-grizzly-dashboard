import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import metrics as m

def style(fig):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Atkinson Hyperlegible, sans-serif", size=15, color="#173B2A"))
    fig.update_xaxes(gridcolor="#D5E3C8"); fig.update_yaxes(gridcolor="#D5E3C8")
    return fig

st.set_page_config(page_title="Green Grizzly campus waste audit", layout="wide")

@st.cache_data
def load():
    return m.load_audit(), m.load_survey(), m.load_methods()

audit, survey, meth = load()
LOCS = ["Soccer field", "Cafeteria", "Basketball hub", "All audited locations"]
SESS = ["All sessions", "Snack", "Lunch"]
BG = {"G": "#DCEEDB", "Y": "#FFF0C2", "R": "#FCE2DB"}
FG = {"G": "#205C3B", "Y": "#6F4D00", "R": "#963B2C"}

def reset():
    st.session_state["loc"], st.session_state["sess"] = LOCS[0], SESS[0]

lr = survey[survey["question_id"] == "location"].set_index("category")
sf_n, sf_N = int(lr.loc["Soccer field", "count"]), int(lr.loc["Soccer field", "denominator"])
sf_lit = m.audit_share(audit, "litter", "Soccer field")

st.title("The soccer field is still a litter hotspot.")
st.caption("Green Grizzly, the student eco-club research team at Colegio Interamericano. "
           "Audit: 28 September to 2 October 2026. Survey: October 2025.")
st.markdown(f"**2025 survey:** {sf_n} of {sf_N} respondents selected the soccer field as a place they usually saw trash.  \n"
            f"**2026 audit:** {sf_lit[0]} of {sf_lit[1]} soccer-field litter checks were rated Red.")
st.caption("Red means 16 or more visible pieces or a concentrated pile. These are different measures, about a year apart. "
           "Both point to a continuing concern.")

loc = st.segmented_control("Location", LOCS, default=LOCS[0], key="loc") or LOCS[0]
sess = st.segmented_control("Audit session (changes audit figures only)", SESS, default=SESS[0], key="sess") or SESS[0]
st.button("Reset filters", on_click=reset)
zone = None if loc.startswith("All") else loc
session = None if sess.startswith("All") else sess
st.caption(f"Showing audit observations for: {loc}, {sess.lower()}. The 2025 survey is not filtered.")

NAMES = list(m.ZONES.values())
ORDER = {"Snack": 0, "Lunch": 1}

def boxes(zone_name, metric):
    d = audit[(audit["zone_name"] == zone_name) & (audit["metric"] == metric)]
    if session:
        d = d[d["session"] == session]
    d = d.sort_values(["date", "session"], key=lambda c: c.map(ORDER) if c.name == "session" else c)
    cells = "".join(
        f'<span title="{r.weekday} {r.session.lower()}: {r.grade}" style="display:inline-flex;align-items:center;'
        f'justify-content:center;width:36px;height:36px;margin:0 4px 4px 0;border-radius:4px;font-weight:700;'
        f'background:{BG[r.grade]};color:{FG[r.grade]};border:1px solid {FG[r.grade]}">{r.grade}</span>'
        for r in d.itertuples())
    return f'<div style="margin:8px 0 4px;font-weight:700">{zone_name}, {metric.lower()}</div><div>{cells}</div>'

def tally(col, kind, label, metrics):
    s_ = m.audit_share(audit, kind, zone, session)
    with col:
        if s_ is None:
            st.info("No observations for this selection.")
            return
        st.subheader(f"{s_[0]} of {s_[1]} {label}")
        st.caption(f"{m.pct(s_)} of {s_[1]} checks. Each box is one check, from Monday snack to Friday lunch.")
        st.markdown("".join(boxes(z, mt) for z in ([zone] if zone else NAMES) for mt in metrics), unsafe_allow_html=True)

c1, c2 = st.columns(2)
tally(c1, "litter", "litter checks rated Red", [m.LITTER])
tally(c2, "bin", "bin checks rated Yellow or Red", m.BIN)
st.caption("Bin checks combine the recycling (white) bin and the organic (green) bin. "
           "Green and Yellow here are grades, not bin colors.")

st.subheader("Make a guess")
guess = st.pills("Which location had the most Red litter checks in the whole audit?", NAMES, key="guess")
if guess:
    reds = {z: m.audit_share(audit, "litter", z) for z in NAMES}
    top = max(reds, key=lambda z: reds[z][0])
    st.markdown(f"**{top}** had the most, with {reds[top][0]} of {reds[top][1]} litter checks rated Red. "
                f"{guess} had {reds[guess][0]} of {reds[guess][1]}.")

left, right = st.columns(2)
with left:
    st.subheader("What students reported")
    st.caption(f"October 2025 survey, {sf_N} respondents. Multiple selections allowed, so bars do not add to 100%.")
    lo = lr.drop(["everywhere", "Everywhere", "no"]).reset_index().sort_values("count")
    fig = go.Figure(go.Bar(x=lo["count"] / sf_N * 100, y=lo["category"], orientation="h", marker_color="#2D6A43",
                           text=[f"{c}/{sf_N} ({c / sf_N * 100:.1f}%)" for c in lo["count"]], textposition="outside"))
    fig.update_xaxes(range=[0, 130], tickvals=[0, 25, 50, 75, 100], title=f"% of {sf_N} respondents")
    fig.update_layout(title="Where students usually saw trash", margin=dict(l=8, r=8, t=48, b=8), height=360)
    st.plotly_chart(style(fig))
    st.caption("Other entries kept in the data file: everywhere (3 respondents) and no (1). "
               "The basketball hub was not a survey option, so it has no survey figure.")
with right:
    st.subheader("What the audit observed")
    st.caption("2026 audit among the three audited locations. This chart keeps all locations and follows the session filter.")
    names, rows = list(m.ZONES.values()), []
    fig = go.Figure()
    for kind, name, color in [("litter", "Litter checks rated Red", "#963B2C"), ("bin", "Bin checks rated Yellow or Red", "#6F4D00")]:
        ss = [m.audit_share(audit, kind, z, session) for z in names]
        rows += [{"Location": z, "Measure": name, "n": s[0], "N": s[1], "Percent": s[2]} for z, s in zip(names, ss) if s]
        fig.add_bar(name=name, x=names, y=[s[2] if s else None for s in ss], marker_color=color, textposition="outside",
                    text=[f"{s[0]}/{s[1]} ({m.pct(s)})" if s else "no data" for s in ss])
    fig.update_yaxes(range=[0, 115], tickvals=[0, 25, 50, 75, 100], title="% of checks")
    fig.update_layout(barmode="group", margin=dict(l=8, r=8, t=24, b=8), height=360, legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(style(fig))
    bh = [m.audit_share(audit, k, "Basketball hub", session) for k in ("litter", "bin")]
    if all(bh):
        st.caption(f"Basketball hub: {bh[0][0]} of {bh[0][1]} litter checks Red, but {bh[1][0]} of {bh[1][1]} bin checks Yellow or Red.")
with st.expander("Chart data as a table"):
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.dataframe(lo[["category", "count", "denominator"]].rename(columns={"category": "Location option"}), hide_index=True)

st.subheader("Audit grid")
view = audit if not zone else audit[audit["zone_name"] == zone]
if session:
    view = view[view["session"] == session]
view = view.assign(col=view["zone_name"] + " | " + view["metric"])
order = [f"{z} | {t}" for z in (names if not zone else [zone]) for t in m.METRICS]
grid = view.pivot(index=["date", "weekday", "session"], columns="col", values="grade")[order].reset_index()
st.dataframe(grid.style.map(lambda v: f"background-color:{BG[v]};color:{FG[v]};font-weight:600;text-align:center" if v in BG else "", subset=order),
             hide_index=True)
st.caption("G, Y and R are shown as letters. Bin grades: G 0 to 1 misplaced items, Y 2 to 4, R 5 or more or serious wet contamination. "
           "Litter grades: G 0 to 5 pieces, Y 6 to 15, R 16 or more or a concentrated pile. Friday was a half day.")

st.subheader("Context from the auditors")
st.markdown("These are auditor notes, not proven causes. Lunch soccer tournaments and student-council cleanup on the field affected "
            "lunch conditions. The cafeteria was all Green on Wednesday lunch when students left for a tournament. "
            "Green organic-bin grades often meant the bin was empty. Auditors sometimes found white bags in the trash bin and black bags in the recycling bin.")
st.subheader("Take your rubbish with you.")
st.write("Check the bin label before you leave.")

with st.expander("How we measured"):
    st.markdown(f"**Audit:** {meth['audit_period']}.  \n**Survey:** {meth['survey_period']}")
    st.markdown("\n".join(f"- {x}" for x in meth["limitations"]))
    st.caption(f"Data version {meth['version']}, updated {meth['updated']}.")
    st.download_button("Download audit data (CSV)", audit.to_csv(index=False), "audit.csv", "text/csv")
    st.download_button("Download survey counts (CSV)", survey.to_csv(index=False), "survey_aggregates.csv", "text/csv")
