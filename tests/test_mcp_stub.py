from gemini_data_agent.mcp_stub import (
    _USERS,
    _ORDERS,
    list_databases_response,
    list_collections_response,
    collection_schema_response,
    find_response,
    count_response,
    aggregate_response,
)


def test_data_seeded():
    assert len(_USERS) == 500
    assert len(_ORDERS) == 1200


def test_list_databases_returns_two():
    payload = list_databases_response()
    names = [d["name"] for d in payload["databases"]]
    assert "acme_prod" in names
    assert "acme_analytics" in names


def test_list_collections_acme_prod():
    payload = list_collections_response("acme_prod")
    assert "users" in payload["collections"]
    assert "orders" in payload["collections"]


def test_collection_schema_users_has_plan_enum():
    payload = collection_schema_response("acme_prod", "users")
    assert "plan" in payload["fields"]
    assert "enum" in payload["fields"]["plan"]


def test_find_users_by_plan_pro():
    payload = find_response("acme_prod", "users", {"plan": "pro"}, limit=5)
    assert payload["matched_count"] > 0
    assert all(u["plan"] == "pro" for u in payload["returned"])


def test_count_orders_paid():
    payload = count_response("acme_prod", "orders", {"status": "paid"})
    assert payload["count"] > 0


def test_aggregate_users_group_by_plan():
    payload = aggregate_response("acme_prod", "users", [{"$group": {"_id": "$plan"}}])
    plan_counts = {r["_id"]: r["count"] for r in payload["results"]}
    assert sum(plan_counts.values()) == 500


def test_aggregate_orders_returns_per_status_total():
    payload = aggregate_response("acme_prod", "orders", [{"$group": {"_id": "$status"}}])
    statuses = {r["_id"] for r in payload["results"]}
    assert {"paid", "shipped", "delivered"}.issubset(statuses)
    assert all("total_usd" in r for r in payload["results"])
