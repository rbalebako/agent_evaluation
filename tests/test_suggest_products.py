"""Contract tests for suggest_products, the additional Homework 1 tool."""

from __future__ import annotations

from agent import tools
from agent.agent import TOOLS_BY_ROLE
from agent.auth import AuthContext

SHOPPER_1 = AuthContext(user_id=1, role="shopper")


def test_suggest_products_finds_a_misspelled_title(world: dict) -> None:
    assert tools.search_products(SHOPPER_1, "bluetooth speeker")["count"] == 0

    result = tools.suggest_products(SHOPPER_1, "bluetooth speeker")
    assert result["ok"] is True
    assert result["count"] == len(result["suggestions"]) >= 1
    assert all("Bluetooth Speaker" in s["title"] for s in result["suggestions"])
    assert all(tools.MIN_SUGGESTION_SCORE <= s["score"] <= 100 for s in result["suggestions"])


def test_suggest_products_orders_by_score_then_price(world: dict) -> None:
    result = tools.suggest_products(SHOPPER_1, "teapots for camping", limit=25)
    keys = [(-s["score"], s["price_usd"], s["product_id"]) for s in result["suggestions"]]
    assert keys == sorted(keys)


def test_suggest_products_no_match_and_invalid_query(world: dict) -> None:
    empty = tools.suggest_products(SHOPPER_1, "zzzz qqqq")
    assert empty["ok"] is True
    assert empty["suggestions"] == []
    assert empty["count"] == 0

    assert tools.suggest_products(SHOPPER_1, "  ")["error"] == "invalid_argument"
    assert tools.suggest_products(SHOPPER_1, "mug", limit=999)["count"] <= tools.MAX_SEARCH_LIMIT


def test_suggest_products_is_registered_for_every_role() -> None:
    for role, role_tools in TOOLS_BY_ROLE.items():
        assert "suggest_products" in [tool.name for tool in role_tools], role
