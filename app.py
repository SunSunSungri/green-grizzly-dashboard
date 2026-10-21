import base64
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image
import metrics as m

ASSETS = Path(__file__).parent / "assets"
PLACES = ["Soccer field", "Cafeteria", "Basketball hub"]
ORDER = {"Snack": 0, "Lunch": 1}
BG = {"G": "#DCEEDB", "Y": "#FFF0C2", "R": "#FCE2DB"}
FG = {"G": "#205C3B", "Y": "#6F4D00", "R": "#963B2C"}
REC, ORG = m.BIN
PERIOD = "28 September–2 October 2026"
# Auditor observations from Audit records.pdf. They are notes, not proven causes.
NOTES = {
    "Soccer field": "Soccer tournaments ran at lunch. Student council collected litter where games were played, but other parts of the field, like the small field at the end, sometimes had litter piled up. Auditors sometimes found a white bag in the non-recycling bin and a black bag in the recycling bin.",
    "Cafeteria": "Litter was usually food on the floor. Green bins had plastic wraps in them and white bins had food in them. Wednesday lunch was all Green because everyone had left for a student-council soccer tournament.",
    "Basketball hub": "Recycling bins usually held mixed items, often food and wrappers. A Green rating on the organic bin usually meant the bin was empty. When the organic bin had trash, it was often wrappers or water bottles as well as food. Yellow litter ratings were usually food on the ground."}
EXPLAIN = {"Soccer field": "What students wrote in the 2025 survey, not proven: some comments said bins are too far away, or missing, near the soccer field."}

st.set_page_config(page_title="Students flagged the field. We checked.", layout="wide")
M = '[data-testid="stMarkdownContainer"] '
st.markdown(f"""<style>
[data-testid="stMainBlockContainer"]{{max-width:1160px;padding:72px 24px 48px}}
{M}.gg-credit{{font-size:15px;margin:0 0 16px}}
{M}.gg-h1{{font-size:clamp(34px,5.5vw,56px);line-height:1.08;margin:0 0 16px;font-weight:700;padding:0}}
{M}.gg-h2{{font-size:26px;line-height:1.2;margin:56px 0 16px;font-weight:700;padding:0;scroll-margin-top:72px}}
[data-testid="stHeading"] h2{{font-size:26px;line-height:1.2;font-weight:700;margin:0;padding:56px 0 16px;scroll-margin-top:72px}}
{M}.gg-h3{{font-size:22px;line-height:1.2;margin:24px 0 8px;font-weight:700;padding:0}}
{M}.gg-h4{{font-size:17px;margin:16px 0 4px;font-weight:700;padding:0}}
{M}.gg-lede{{font-size:19px;line-height:1.45;max-width:34rem;margin:0 0 24px}}
{M}.gg-label{{font-size:15px;font-weight:700;margin:0 0 4px}}
{M}.gg-fig{{font-size:clamp(48px,8vw,72px);line-height:1;font-weight:700;font-variant-numeric:tabular-nums;color:#963B2C;margin:0}}
{M}.gg-fig2{{font-size:44px;line-height:1;font-weight:700;font-variant-numeric:tabular-nums;color:#963B2C;margin:4px 0 0}}
{M}.gg-note{{font-size:17px;line-height:1.45;max-width:34rem;margin:8px 0 0}}
{M}.gg-small{{font-size:15px;line-height:1.4;max-width:34rem;margin:8px 0 0}}
{M}a.gg-cta{{display:inline-flex;align-items:center;min-height:44px;margin-top:20px;padding:8px 16px;background:#2D6A43;color:#FAF8F3;border-radius:4px;font-weight:700;text-decoration:none}}
.gg-img{{position:relative;margin:0}}.gg-img img{{display:block;width:auto;height:auto;max-width:100%;max-height:560px;border-radius:4px}}
{M}.gg-cap{{font-size:15px;line-height:1.4;margin:8px 0 0;max-width:34rem}}
{M}.gg-badge{{position:absolute;top:8px;left:8px;background:#173B2A;color:#FAF8F3;padding:4px 8px;border-radius:4px;font-weight:700;font-size:15px}}
{M}.gg-date{{display:inline-block;font-weight:700;background:#173B2A;color:#FAF8F3;padding:4px 8px;border-radius:4px;font-size:15px}}
{M}table.gg-t{{width:100%;border-collapse:collapse;font-size:16px}}
{M}table.gg-t caption{{text-align:left;font-size:15px;padding:0 0 8px}}
{M}table.gg-t th,{M}table.gg-t td{{text-align:left;vertical-align:top;padding:12px 12px 12px 0;border-top:1px solid #C9D8BC}}
{M}table.gg-t thead th{{border-top:2px solid #2D6A43;font-size:15px}}
.gg-track{{height:10px;background:#E8F2DE;border-radius:2px;margin-top:4px}}.gg-fill{{height:10px;border-radius:2px}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;animation:none!important}}}}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load():
    return m.load_audit(), m.load_survey(), m.load_methods()

@st.cache_data
def figure(file, alt, caption, badge=""):
    try:
        p = ASSETS / file
        w, h = Image.open(p).size
        b64 = base64.b64encode(p.read_bytes()).decode()
    except OSError:
        return ""
    tag = f'<span class="gg-badge">{badge}</span>' if badge else ""
    return (f'<figure class="gg-img">{tag}<img src="data:image/jpeg;base64,{b64}" alt="{alt}" width="{w}" height="{h}" style="aspect-ratio:{w}/{h}">'
            f'<figcaption class="gg-cap">{caption}</figcaption></figure>')

def frac(s): return f"{s[0]} of {s[1]}"
def bar(n, total, color): return f'<div class="gg-track"><div class="gg-fill" style="width:{n / total * 100:.1f}%;background:{color}"></div></div>'

def boxes(zone):
    d = audit[(audit["zone_name"] == zone) & (audit["metric"] == m.LITTER)]
    d = d.sort_values(["date", "session"], key=lambda c: c.map(ORDER) if c.name == "session" else c)
    cells = "".join(f'<span title="{r.weekday} {r.session.lower()}: {r.grade}" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;'
                    f'margin:0 4px 4px 0;border-radius:4px;font-weight:700;background:{BG[r.grade]};color:{FG[r.grade]};border:1px solid {FG[r.grade]}">{r.grade}</span>' for r in d.itertuples())
    return f"<div>{cells}</div>"

def matrix(zones):
    v = audit[audit["zone_name"].isin(zones)].assign(col=lambda d: d["zone_name"] + " | " + d["metric"])
    order = [f"{z} | {t}" for z in zones for t in m.METRICS]
    g = v.pivot(index=["date", "weekday", "session"], columns="col", values="grade")[order].reset_index()
    g = g.sort_values(["date", "session"], key=lambda c: c.map(ORDER) if c.name == "session" else c)
    g = g.rename(columns={"date": "Date", "weekday": "Day", "session": "Session"})
    return g.style.map(lambda x: f"background-color:{BG[x]};color:{FG[x]};font-weight:600;text-align:center" if x in BG else "", subset=order)

audit, survey, meth = load()
lr = survey[survey["question_id"] == "location"].set_index("category")
SN = int(lr.loc["Soccer field", "denominator"]); sf_n = int(lr.loc["Soccer field", "count"])
sf_lit = m.audit_share(audit, "litter", "Soccer field")

# 1. First screen
a, b = st.columns([6, 5], gap="large")
with a:
    st.markdown(f'<p class="gg-credit">Green Grizzly, the student eco-club research team, Colegio Interamericano</p>'
                f'<h1 class="gg-h1">Students flagged the field. We checked.</h1>'
                f'<p class="gg-lede">In October 2025, {SN} students told us where they usually saw trash. From 28 September to 2 October 2026, six of us checked three campus spots over one school week.</p>'
                f'<p class="gg-label">What we saw at the soccer field</p>'
                f'<p class="gg-fig">{frac(sf_lit)}</p><p class="gg-note" style="margin-top:4px"><b>litter checks were rated Red.</b> A check is one quick scan of the whole area at snack or lunch. Red means 16 or more visible pieces, or a concentrated pile.</p>'
                f'<a class="gg-cta" href="#check-your-spot">Check your usual spot</a>', unsafe_allow_html=True)
with b:
    st.markdown(figure("soccer-field-2025-11-06.jpg",
                       "Wet artificial-turf soccer field with a few scattered pieces of litter on the turf, mostly near the lower edge, with a painted wall and trees behind.",
                       "Soccer field, 6 November 2025. This photo is from before the audit week.", "November 2025 photo"), unsafe_allow_html=True)

# 2. Compact comparison
st.markdown('<h2 class="gg-h2">Students named the soccer field first. Our checks found the most litter there.</h2>', unsafe_allow_html=True)
rows = ""
for z in PLACES:
    lit = m.audit_share(audit, "litter", z)
    sv = f"<b>{int(lr.loc[z, 'count'])} of {SN}</b>{bar(int(lr.loc[z, 'count']), SN, '#2D6A43')}" if z in lr.index else "Not a survey option"
    rows += f"<tr><th scope='row'>{z}</th><td>{sv}</td><td><b>{frac(lit)}</b>{bar(lit[0], lit[1], '#963B2C')}</td></tr>"
st.markdown(f"<table class='gg-t'><caption><b>The same three places, measured two ways.</b><br>2025 column: students picked places where they usually saw trash ({SN} students, could pick more than one). 2026 column: litter checks rated Red, 10 checks per place, {PERIOD}.</caption><thead><tr><th scope='col'>Place</th>"
            "<th scope='col'>2025: what students reported</th>"
            "<th scope='col'>2026: what our team observed</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>", unsafe_allow_html=True)
st.markdown('<p class="gg-small"><b>Different measures, collected about a year apart.</b> They can show the same places standing out. They cannot show whether things got better or worse.</p>', unsafe_allow_html=True)

# 3. Check your usual spot
st.header("Check your usual spot", anchor="check-your-spot")
st.markdown('<p class="gg-note" style="margin-top:0">Pick a place. Only this section changes. The rest of the page stays the same.</p>', unsafe_allow_html=True)

@st.fragment
def spot():
    pick = st.segmented_control("Your spot", PLACES, default=PLACES[0], key="spot") or PLACES[0]
    st.markdown(f'<h3 class="gg-h3">{pick}: what we found</h3>', unsafe_allow_html=True)
    lit, sn, lu = (m.audit_share(audit, "litter", pick, s) for s in (None, "Snack", "Lunch"))
    gc = audit[(audit["zone_name"] == pick) & (audit["metric"] == m.LITTER)]["grade"].value_counts()
    G, Y, R = (int(gc.get(k, 0)) for k in "GYR")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(f'<p class="gg-h4">Litter on the ground</p><p class="gg-fig2">{frac(lit)}</p><p class="gg-note" style="margin-top:4px"><b>checks rated Red.</b> Snack: {frac(sn)}. Lunch: {frac(lu)}.</p>'
                    f'{boxes(pick)}<p class="gg-small">Each box is one check, Monday snack to Friday lunch. Friday was a half day. '
                    f'G Green: 0 to 5 pieces. Y Yellow: 6 to 15. R Red: 16 or more, or a pile.</p>'
                    f'<p class="gg-small">All ten ratings: {G} Green, {Y} Yellow, {R} Red. Green does not mean no litter, and no Reds does not mean a clean area.</p>', unsafe_allow_html=True)
    with right:
        body = '<p class="gg-h4">Sorting in the bins</p>'
        for label, metric in (("Recycling (white) bin", REC), ("Organic (green) bin", ORG)):
            s = m.audit_share(audit[audit["metric"] == metric], "bin", pick)
            body += f'<p class="gg-note" style="margin-top:8px"><b>{label}:</b> {frac(s)} checks rated Yellow or Red</p>{bar(s[0], s[1], "#6F4D00")}'
        body += ('<p class="gg-small">We checked the worst-looking bin cluster in each place, so this describes those bins, not average bins. '
                 'Yellow means 2 to 4 misplaced items. Red means 5 or more, or serious wet contamination. The organic bin is a bin type. Green is a rating.</p>')
        st.markdown(body, unsafe_allow_html=True)
    st.markdown(f'<p class="gg-h4">From our field notes</p><p class="gg-note" style="margin:0 0 16px">{NOTES[pick]}</p>'
                + (f'<p class="gg-small">{EXPLAIN[pick]}</p>' if pick in EXPLAIN else ""), unsafe_allow_html=True)
    with st.expander(f"Table: every rating at the {pick.lower()}"):
        st.dataframe(matrix([pick]), hide_index=True)
spot()

# 4. Inside the bins
st.markdown('<h2 class="gg-h2">What we found inside the bins</h2>', unsafe_allow_html=True)
p1, p2, p3 = st.columns([4, 4, 5], gap="large")
p1.markdown(figure("organic-bin-2026-09-30.jpg",
                   "Looking down into a bin lined with a dark green bag. At the bottom are snack wrappers, a crumpled white tissue, a white cup and clear plastic.",
                   "<b>Wrappers and plastic in an organic bin.</b><br>Soccer field organic bin, snack period, 30 September 2026."), unsafe_allow_html=True)
p2.markdown(figure("recycling-bin-2026-09-28.jpg",
                   "Looking down into a bin lined with a white bag. At the bottom are brown and yellow wrappers, a bottle with a blue label, crumpled white paper with food stains and an orange item in clear plastic.",
                   "<b>Food-stained paper and wrappers in a recycling bin.</b><br>Basketball hub recycling bin, 28 September 2026, as identified by our team."), unsafe_allow_html=True)
with p3:
    st.markdown('<p class="gg-h4" style="margin-top:0">What we noticed</p>'
                '<p class="gg-note" style="margin-top:4px">Auditors found mixed items in recycling bins, often food and wrappers. Green ratings on organic bins often meant the bin was empty. '
                'At the soccer field, auditors sometimes found a white bag in the non-recycling bin and a black bag in the recycling bin.</p>'
                '<p class="gg-small">These photos are single examples. They do not show how often sorting mistakes happen. We did not mark which item belongs where, because we have not yet confirmed the school\'s sorting rules for each item.</p>', unsafe_allow_html=True)

# 5. Practical next step
st.markdown('<h2 class="gg-h2">One thing you can do now</h2>', unsafe_allow_html=True)
n1, n2 = st.columns(2, gap="large")
n1.markdown('<p class="gg-h4" style="margin-top:0">You</p><p class="gg-note" style="margin-top:4px"><b>Take your rubbish with you.</b> Check the bin label before you leave. '
            'It speaks to what we saw: litter on the field and mixed items in bins.</p>', unsafe_allow_html=True)
n2.markdown('<p class="gg-h4" style="margin-top:0">Needs the school or the custodial team</p><p class="gg-note" style="margin-top:4px">'
            'Confirming the sorting rules for each bin, so they can be shared. Checking whether bag colors match the bin colors. Some 2025 survey comments said bins are hard to reach from the soccer field.</p>'
            '<p class="gg-small">We have not verified the school\'s official sorting rules, so this page does not say where specific items go. We are not promising any change.</p>', unsafe_allow_html=True)

# 6. Evidence
st.markdown('<h2 class="gg-h2">Check the evidence</h2>', unsafe_allow_html=True)
with st.expander("How we checked"):
    st.markdown("**Audit:** 28 September to 2 October 2026. Three places, with a snack check and a lunch check each day, so ten checks per place. Each check is a quick visual scan by a student auditor.")
    st.markdown("**Survey:** October 2025, 105 students. The dates printed on the exported survey pages (October 2026) are not collection dates.")
    st.markdown("\n".join(f"- {x}" for x in meth["limitations"]))
    st.markdown("- The survey describes the 105 students who answered. It may not represent every student.")
    st.markdown("**Why we did this:** we wanted to find out where litter and sorting mistakes still happen on campus and how serious they look in each place.")
with st.expander("Rating definitions"):
    st.markdown("| Rating | Recycling and organic-bin checks | Litter checks |\n|---|---|---|\n"
                f"| G Green | {meth['bin_rubric']['G']} | {meth['litter_rubric']['G']} |\n| Y Yellow | {meth['bin_rubric']['Y']} | {meth['litter_rubric']['Y']} |\n"
                f"| R Red | {meth['bin_rubric']['R']} | {meth['litter_rubric']['R']} |")
    st.markdown("Ratings are bands, not item counts, so we do not turn them into totals, weights or recycling rates. The organic bin is a bin type. Green is a rating.")
with st.expander("Data and downloads"):
    st.markdown("**Every rating, all three places** (Monday snack to Friday lunch)")
    st.dataframe(matrix(PLACES), hide_index=True)
    lo = lr.reset_index()[["category", "count", "denominator"]].rename(columns={"category": "Survey answer", "count": "Students", "denominator": "Total students"})
    st.markdown("**2025 survey: where students usually saw trash** (they could pick more than one)")
    st.dataframe(lo, hide_index=True)
    st.markdown(f"Sources: Audit records.pdf, pages 1-2; Survey responses.pdf, pages {', '.join(str(p) for p in sorted(set(survey['source_page'])))}. Data version {meth['version']}, updated {meth['updated']}.")
    st.download_button("Download audit data (CSV)", audit.to_csv(index=False), "audit.csv", "text/csv")
    st.download_button("Download survey counts (CSV)", survey.to_csv(index=False), "survey_aggregates.csv", "text/csv")
