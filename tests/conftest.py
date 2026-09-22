import gzip
import json
import shutil
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"

# Real FotMob matchDetails responses, one per season, saved verbatim (gzipped).
FOTMOB_MATCHES = {"2024-25": "4506263", "2025-26": "4813374", "2026-27": "5795459"}


def load(name: str) -> dict:
    with gzip.open(FIX / name, "rt", encoding="utf-8") as f:
        return json.load(f)


class NoNetworkClient:
    """Fails the test if an adapter tries to hit the network."""

    def get(self, *a, **k):
        raise AssertionError(f"unexpected network call: {a} {k}")


@pytest.fixture
def raw_dir(tmp_path):
    """A raw cache pre-populated with the saved real responses."""
    d = tmp_path / "raw"
    for season, mid in FOTMOB_MATCHES.items():
        p = d / "fotmob" / season / f"{mid}.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps(load(f"fotmob_{mid}.json.gz")), encoding="utf-8")
    p = d / "fotmob" / "2025-26" / "_fixtures.json"
    p.write_text(json.dumps(load("fotmob_fixtures_2025-26.json.gz")), encoding="utf-8")
    p = d / "premierleague" / "2025-26" / "124791.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(load("premierleague_124791.json.gz")), encoding="utf-8")
    return d
