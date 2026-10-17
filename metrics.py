"""Validated loading, and the single place where headline metrics are computed."""
import json
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data"
ZONES = {1: "Basketball hub", 2: "Cafeteria", 3: "Soccer field"}
BIN = ["Recycling (white bin)", "Organic (green bin)"]
LITTER = "Litter"
METRICS = BIN + [LITTER]
COLS = ["date", "weekday", "session", "zone_id", "zone_name", "metric", "grade",
        "source_file", "source_page", "method_note_id"]

def validate_audit(df):
    if list(df.columns) != COLS:
        raise ValueError("unexpected audit columns")
    if not df["grade"].isin(["G", "Y", "R"]).all():
        raise ValueError("grade must be G, Y or R; missing grades are never imputed")
    if not df["metric"].isin(METRICS).all():
        raise ValueError("unknown metric")
    if df.duplicated(["date", "session", "zone_id", "metric"]).any():
        raise ValueError("duplicate observation key")
    if (df["zone_id"].astype(int).map(ZONES) != df["zone_name"]).any():
        raise ValueError("zone id and name do not match")
    if not df.groupby(["date", "session", "zone_id"])["metric"].nunique().eq(3).all():
        raise ValueError("every zone visit needs recycling, organic and litter grades")
    return df

def load_audit(path=DATA / "audit.csv"):
    return validate_audit(pd.read_csv(path, dtype=str, keep_default_na=False))

def load_survey(path=DATA / "survey_aggregates.csv"):
    df = pd.read_csv(path)
    for q, g in df[df["question_id"] != "location"].groupby("question_id"):
        if g["count"].sum() != g["denominator"].iloc[0]:
            raise ValueError(f"{q}: counts do not sum to the denominator")
    return df

def load_methods(path=DATA / "methods.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def audit_share(df, kind, zone=None, session=None):
    """Return (n, N, percent) or None when the selection has no observations.
    kind='bin': checks rated Yellow or Red. kind='litter': checks rated Red."""
    d = df[df["metric"].isin(BIN)] if kind == "bin" else df[df["metric"] == LITTER]
    if zone:
        d = d[d["zone_name"] == zone]
    if session:
        d = d[d["session"] == session]
    if len(d) == 0:
        return None
    hit = d["grade"].isin(["Y", "R"]) if kind == "bin" else d["grade"].eq("R")
    n = int(hit.sum())
    return n, len(d), round(100 * n / len(d), 1)

def pct(s):
    return f"{s[2]:g}%"
