import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import metrics as m

# Edit this text if the team words its objective differently.
OBJECTIVE = ("Find out where litter and sorting mistakes still happen on campus, and how serious they look in each place, "
             "by counting them ourselves. We set what students told us in a 2025 survey next to what we saw in a one-week audit in 2026, "
             "so students and staff can see the problem clearly.")

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
NAMES = list(m.ZONES.values())
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ORDER = {"Snack": 0, "Lunch": 1}
BG = {"G": "#DCEEDB", "Y": "#FFF0C2", "R": "#FCE2DB"}
FG = {"G": "#205C3B", "Y": "#6F4D00", "R": "#963B2C"}
SERIES = [("litter", "Litter checks rated Red", "#963B2C"), ("bin", "Bin checks rated Yellow or Red", "#6F4D00")]

def reset():
    st.session_state["loc"], st.session_state["sess"] = LOCS[0], SESS[0]

lr = survey[survey["question_id"] == "location"].set_index("category")
SN = int(lr.loc["Soccer field", "denominator"])
sf_n = int(lr.loc["Soccer field", "count"])
sf_lit = m.audit_share(audit, "litter", "Soccer field")

def boxes(zone_name, metric, sess=None):
    d = audit[(audit["zone_name"] == zone_name) & (audit["metric"] == metric)]
    if sess:
        d = d[d["session"] == sess]
    d = d.sort_values(["date", "session"], key=lambda c: c.map(ORDER) if c.name == "session" else c)
    cells = "".join(
        f'<span title="{r.weekday} {r.session.lower()}: {r.grade}" style="display:inline-flex;align-items:center;'
        f'justify-content:center;width:36px;height:36px;margin:0 4px 4px 0;border-radius:4px;font-weight:700;'
        f'background:{BG[r.grade]};color:{FG[r.grade]};border:1px solid {FG[r.grade]}">{r.grade}</span>' for r in d.itertuples())
    return f'<div style="margin:8px 0 4px;font-weight:700">{zone_name}, {metric.lower()}</div><div>{cells}</div>'

def tile(col, label, value, note):
    with col:
        with st.container(border=True):
            st.metric(label, value)
            st.caption(note)

def bars(xs, getter):
    fig, rows = go.Figure(), []
    for kind, name, color in SERIES:
        ss = [getter(x, kind) for x in xs]
        rows += [{"Group": x, "Measure": name, "n": s[0], "N": s[1], "Percent": s[2]} for x, s in zip(xs, ss) if s]
        fig.add_bar(name=name, x=xs, y=[s[2] if s else None for s in ss], marker_color=color, textposition="outside",
                    text=[f"{s[0]}/{s[1]} ({m.pct(s)})" if s else "no data" for s in ss])
    fig.update_yaxes(range=[0, 115], tickvals=[0, 25, 50, 75, 100], title="% of checks")
    fig.update_layout(barmode="group", margin=dict(l=8, r=8, t=24, b=8), height=360, legend=dict(orientation="h", y=-0.2))
    return style(fig), rows

# 1. Attention first: the finding, drawn from the data
st.title("The soccer field is still a litter hotspot.")
st.markdown(boxes("Soccer field", m.LITTER), unsafe_allow_html=True)
st.markdown(f"**{sf_lit[0]} of {sf_lit[1]} soccer-field litter checks were rated Red** in our 2026 audit. "
            f"In the 2025 survey, **{sf_n} of {SN} students** said it is where they usually see trash.")
st.caption("Each box is one check, Monday snack to Friday lunch. Red means 16 or more visible pieces or a concentrated pile. "
           "The survey and the audit are different measures about a year apart. Both point to a continuing concern.")

# 2. Objective
st.subheader("Why we did this research")
st.write(OBJECTIVE)
st.caption("Green Grizzly, the student eco-club research team at Colegio Interamericano. Audit: 28 September to 2 October 2026. Survey: October 2025.")

# 3. Controls and tiles
st.subheader("Explore the results")
loc = st.segmented_control("Location", LOCS, default=LOCS[0], key="loc") or LOCS[0]
sess = st.segmented_control("Audit session (changes audit figures only)", SESS, default=SESS[0], key="sess") or SESS[0]
st.button("Reset filters", on_click=reset)
zone = None if loc.startswith("All") else loc
session = None if sess.startswith("All") else sess
st.caption(f"Showing audit observations for: {loc}, {sess.lower()}. The 2025 survey is not filtered.")

c1, c2, c3 = st.columns(3)
for col, kind, label, note in [(c1, "litter", "Litter checks rated Red", "of litter checks"), (c2, "bin", "Bin checks rated Yellow or Red", "of bin checks")]:
    s = m.audit_share(audit, kind, zone, session)
    tile(col, label, "No observations" if s is None else f"{s[0]} of {s[1]}", "No observations for this selection." if s is None else f"{m.pct(s)} {note}")
if zone in lr.index:
    n3 = int(lr.loc[zone, "count"])
    tile(c3, "Students who said they usually see trash here", f"{n3} of {SN}", f"{n3 / SN * 100:.1f}% of {SN} respondents, October 2025")
elif zone is None:
    tile(c3, "Most picked place in the 2025 survey", f"{sf_n} of {SN}", "Soccer field. Students could pick several places.")
else:
    tile(c3, "Students who said they usually see trash here", "Not asked", "The basketball hub was not a survey option.")
st.caption("Bin checks combine the recycling (white) bin and the organic (green) bin. Green and Yellow here are grades, not bin colors.")

zones_in = [zone] if zone else NAMES
la, lb = st.columns(2)
la.markdown("".join(boxes(z, m.LITTER, session) for z in zones_in), unsafe_allow_html=True)
lb.markdown("".join(boxes(z, mt, session) for z in zones_in for mt in m.BIN), unsafe_allow_html=True)
st.caption("Red bin means 5 or more misplaced items or serious wet contamination. Yellow means 2 to 4. Letters and colors show the grade.")

st.subheader("Make a guess")
guess = st.pills("Which location had the most Red litter checks in the whole audit?", NAMES, key="guess")
if guess:
    reds = {z: m.audit_share(audit, "litter", z) for z in NAMES}
    top = max(reds, key=lambda z: reds[z][0])
    st.markdown(f"**{top}** had the most, with {reds[top][0]} of {reds[top][1]} litter checks rated Red. "
                f"{guess} had {reds[guess][0]} of {reds[guess][1]}.")

# 4. Charts
left, right = st.columns(2)
with left:
    st.subheader("What students reported")
    st.caption(f"October 2025 survey, {SN} respondents. Multiple selections allowed, so bars do not add to 100%.")
    lo = lr.drop(["everywhere", "Everywhere", "no"]).reset_index().sort_values("count")
    fig = go.Figure(go.Bar(x=lo["count"] / SN * 100, y=lo["category"], orientation="h", marker_color="#2D6A43",
                           text=[f"{c}/{SN} ({c / SN * 100:.1f}%)" for c in lo["count"]], textposition="outside"))
    fig.update_xaxes(range=[0, 130], tickvals=[0, 25, 50, 75, 100], title=f"% of {SN} respondents")
    fig.update_layout(title="Where students usually saw trash", margin=dict(l=8, r=8, t=48, b=8), height=360)
    st.plotly_chart(style(fig))
    st.caption("Other entries kept in the data file: everywhere (3 respondents) and no (1). The basketball hub was not a survey option.")
with right:
    st.subheader("What the audit observed")
    st.caption("Among the three audited locations. This chart keeps all locations and follows the session filter.")
    zfig, zrows = bars(NAMES, lambda z, k: m.audit_share(audit, k, z, session))
    st.plotly_chart(zfig)
    bh = [m.audit_share(audit, k, "Basketball hub", session) for k in ("litter", "bin")]
    if all(bh):
        st.caption(f"Basketball hub: {bh[0][0]} of {bh[0][1]} litter checks Red, but {bh[1][0]} of {bh[1][1]} bin checks Yellow or Red.")

st.subheader("Day by day")
st.caption("Days within one audit week for the selected location and session. This is not a trend over the year. Friday was a half day.")
dfig, drows = bars(DAYS, lambda d, k: m.audit_share(audit[audit["weekday"] == d], k, zone, session))
dfig.update_xaxes(tickvals=DAYS, ticktext=[d if d != "Friday" else "Friday (half day)" for d in DAYS])
st.plotly_chart(dfig)
with st.expander("Chart data as a table"):
    st.dataframe(pd.DataFrame(zrows), hide_index=True)
    st.dataframe(pd.DataFrame(drows), hide_index=True)
    st.dataframe(lo[["category", "count", "denominator"]].rename(columns={"category": "Location option"}), hide_index=True)

# 5. Explanation
with st.container(border=True):
    st.subheader("How to read this")
    st.markdown("**The grades are bands, not counts.** G, Y and R are ranges set by our scoring key, so we cannot turn them into exact numbers of items or percentages of contamination.")
    st.markdown("**What we can say.** The soccer field was the place students picked most in 2025, and it had the most Red litter checks in 2026. Both point to a continuing concern.")
    st.markdown("**What we cannot say.** We cannot say whether things got better or worse, because the survey and the audit measure different things and there is no earlier audit. "
                "Auditors checked the worst-looking bin in each place, so the results describe those bins, not an average bin.")

st.subheader("Audit grid")
view = audit if not zone else audit[audit["zone_name"] == zone]
if session:
    view = view[view["session"] == session]
view = view.assign(col=view["zone_name"] + " | " + view["metric"])
order = [f"{z} | {t}" for z in zones_in for t in m.METRICS]
grid = view.pivot(index=["date", "weekday", "session"], columns="col", values="grade")[order].reset_index()
st.dataframe(grid.style.map(lambda v: f"background-color:{BG[v]};color:{FG[v]};font-weight:600;text-align:center" if v in BG else "", subset=order), hide_index=True)
st.caption("Litter grades: G 0 to 5 pieces, Y 6 to 15, R 16 or more or a concentrated pile.")

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
