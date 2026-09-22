"""Red-card handling: verified codes map to True/False, anything unverified becomes NULL + reason."""
import copy

from peanut_soccer.sources.fotmob import FotMobAdapter
from peanut_soccer.sources.premierleague import PremierLeagueAdapter

from .conftest import NoNetworkClient, load


def test_fotmob_real_red_card():
    # Aston Villa v Newcastle, 16 Aug 2025: Ezri Konsa sent off 66'.
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(load("fotmob_4813375.json.gz"), "2025-26")
    konsa = next(r for r in rows if r.player_name == "Ezri Konsa")
    assert konsa.red_card is True
    assert sum(1 for r in rows if r.red_card) == 1
    assert all(r.red_card is False for r in rows if r.player_name != "Ezri Konsa")


def test_fotmob_unknown_card_value_is_null():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    ev = next(e for e in raw["content"]["matchFacts"]["events"]["events"] if e["type"] == "Card")
    ev["card"] = "SomethingNew"
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = next(r for r in rows if r.player_id == str(ev["playerId"]))
    assert r.red_card is None and r.null_reasons["red_card"] == "unrecognized_card_code"


def _pl_with_first_booking(code):
    raw = copy.deepcopy(load("premierleague_124791.json.gz"))
    ev = next(e for e in raw["fixture"]["events"] if e["type"] == "B")
    ev["description"] = code
    _, rows = PremierLeagueAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    return next(r for r in rows if r.player_id == str(int(ev["personId"])))


def test_premierleague_cards():
    _, rows = PremierLeagueAdapter(NoNetworkClient()).parse_match(load("premierleague_124791.json.gz"), "2025-26")
    assert not any(r.red_card for r in rows)  # only yellows in this match
    assert _pl_with_first_booking("R").red_card is True
    r = _pl_with_first_booking("ZZ")
    assert r.red_card is None and r.null_reasons["red_card"] == "unrecognized_card_code"
