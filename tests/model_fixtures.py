"""Real-data extract for model tests (built from the DB by tests/make_model_fixture.py)."""
import gzip
from pathlib import Path

import pandas as pd

FIX = Path(__file__).parent / "fixtures" / "appearances_liv_bou.csv.gz"


def load_app() -> pd.DataFrame:
    df = pd.read_csv(FIX, dtype={"match_id": str, "player_id": str})
    df["kickoff"] = pd.to_datetime(df["kickoff"])
    df["is_home"] = df["is_home"].astype(bool)
    df["started"] = df["started"].astype(bool)
    return df
