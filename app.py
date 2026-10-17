import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import metrics as m

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

loc = st.radio("Location", LOCS, horizontal=True, key="loc")
sess = st.radio("Audit session (changes audit figures only)", SESS, horizontal=True, key="sess")
st.button("Reset filters", on_click=reset)
zone = None if loc.startswith("All") else loc
session = None if sess.startswith("All") else sess
st.caption(f"Showing audit observations for: {loc}, {sess.lower()}. The 2025 survey is not filtered.")

c1, c2 = st.columns(2)
for col, kind, label in [(c1, "litter", "Litter checks rated Red"), (c2, "bin", "Bin checks rated Yellow or Red")]:
    s = m.audit_share(audit, kind, zone, session)
    with col:
        if s is None:
            st.info("No observations for this selection.")
        else:
            st.metric(label, f"{s[0]} of {s[1]}")
            st.caption(f"{m.pct(s)} of {s[1]} checks")
st.caption("Bin checks combine the recycling (white) bin and the organic (green) bin. "
           "Green and Yellow here are grades, not bin colors.")

left, right = st.columns(2)
with left:
    st.subheader("What students reported")
    st.caption(f"October 2025 survey, {sf_N} respondents. Multiple selections allowed, so bars do not add to 100%.")
    lo = lr.drop(["everywhere", "Everywhere", "no"]).reset_index().sort_values("count")
    fig = go.Figure(go.Bar(x=lo["count"] / sf_N * 100, y=lo["category"], orientation="h", marker_color="#2D6A43",
                           text=[f"{c}/{sf_N} ({c / sf_N * 100:.1f}%)" for c in lo["count"]], textposition="outside"))
    fig.update_xaxes(range=[0, 130], tickvals=[0, 25, 50, 75, 100], title=f"% of {sf_N} respondents")
    fig.update_layout(title="Where students usually saw trash", margin=dict(l=8, r=8, t=48, b=8), height=360)
    st.plotly_chart(fig)
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
    st.plotly_chart(fig)
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
st.info("Take your rubbish with you. Check the bin label before you leave.")

with st.expander("How we measured"):
    st.markdown(f"**Audit:** {meth['audit_period']}.  \n**Survey:** {meth['survey_period']}")
    st.markdown("\n".join(f"- {x}" for x in meth["limitations"]))
    st.caption(f"Data version {meth['version']}, updated {meth['updated']}.")
    st.download_button("Download audit data (CSV)", audit.to_csv(index=False), "audit.csv", "text/csv")
    st.download_button("Download survey counts (CSV)", survey.to_csv(index=False), "survey_aggregates.csv", "text/csv")
