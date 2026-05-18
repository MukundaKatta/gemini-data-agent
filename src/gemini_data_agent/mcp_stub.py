"""Stub MongoDB MCP server.

Exposes the same tool names as the official `mongodb-mcp-server` npm package
(`list_databases`, `list_collections`, `find`, `aggregate`, `count`,
`collection_schema`) but returns canned realistic responses so demos work
without a live MongoDB cluster.

Run with: python -m gemini_data_agent.mcp_stub
"""

from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


NOW = datetime.now(timezone.utc)
_RNG = random.Random(2026)


# ---------------------------------------------------------------------------
# Canned synthetic database. A small e-commerce shape: users, orders, products.
# Reviewers can read this to verify what the agent sees during the demo.
# ---------------------------------------------------------------------------

_DATABASES = ["acme_prod", "acme_analytics"]

_COLLECTIONS = {
    "acme_prod": ["users", "orders", "products", "carts", "sessions"],
    "acme_analytics": ["events", "funnels"],
}


def _make_users(n: int = 500) -> list[dict[str, Any]]:
    plans = ["free", "starter", "pro", "enterprise"]
    out = []
    for i in range(n):
        last_seen_offset = _RNG.choice([0, 0, 1, 3, 7, 14, 30, 60, 90, 180])
        plan = _RNG.choices(plans, weights=[55, 25, 15, 5])[0]
        out.append({
            "_id": f"u_{i:05d}",
            "email": f"user{i:05d}@example.com",
            "plan": plan,
            "created_at": (NOW - timedelta(days=_RNG.randint(1, 730))).isoformat(),
            "last_seen_at": (NOW - timedelta(days=last_seen_offset)).isoformat(),
            "lifetime_value_usd": round(_RNG.uniform(0, 4200), 2) if plan != "free" else 0,
        })
    return out


def _make_orders(n: int = 1200) -> list[dict[str, Any]]:
    statuses = ["paid", "refunded", "pending", "shipped", "delivered"]
    out = []
    for i in range(n):
        out.append({
            "_id": f"o_{i:06d}",
            "user_id": f"u_{_RNG.randint(0, 499):05d}",
            "status": _RNG.choices(statuses, weights=[40, 5, 10, 20, 25])[0],
            "total_usd": round(_RNG.uniform(8, 480), 2),
            "created_at": (NOW - timedelta(days=_RNG.randint(0, 365))).isoformat(),
        })
    return out


_USERS = _make_users()
_ORDERS = _make_orders()


def list_databases_response() -> dict[str, Any]:
    return {
        "databases": [
            {"name": db, "collections": _COLLECTIONS[db]} for db in _DATABASES
        ],
    }


def list_collections_response(database: str) -> dict[str, Any]:
    return {
        "database": database,
        "collections": _COLLECTIONS.get(database, []),
    }


def collection_schema_response(database: str, collection: str) -> dict[str, Any]:
    """Inferred schema for the canned collections."""
    schemas = {
        ("acme_prod", "users"): {
            "_id": "string",
            "email": "string",
            "plan": "enum: free | starter | pro | enterprise",
            "created_at": "iso datetime",
            "last_seen_at": "iso datetime",
            "lifetime_value_usd": "float",
        },
        ("acme_prod", "orders"): {
            "_id": "string",
            "user_id": "string (FK users._id)",
            "status": "enum: paid | refunded | pending | shipped | delivered",
            "total_usd": "float",
            "created_at": "iso datetime",
        },
    }
    return {
        "database": database,
        "collection": collection,
        "fields": schemas.get((database, collection), {"_id": "string"}),
    }


def _filter_users(filter_: dict[str, Any] | None) -> list[dict[str, Any]]:
    """A tiny subset of MongoDB filter semantics, enough for the demo."""
    rows = list(_USERS)
    if not filter_:
        return rows
    for key, value in filter_.items():
        if isinstance(value, dict):
            for op, op_v in value.items():
                if op == "$gte":
                    rows = [r for r in rows if (r.get(key) or "") >= op_v]
                elif op == "$lte":
                    rows = [r for r in rows if (r.get(key) or "") <= op_v]
                elif op == "$gt":
                    rows = [r for r in rows if (r.get(key) or "") > op_v]
                elif op == "$lt":
                    rows = [r for r in rows if (r.get(key) or "") < op_v]
                elif op == "$in":
                    rows = [r for r in rows if r.get(key) in op_v]
        else:
            rows = [r for r in rows if r.get(key) == value]
    return rows


def find_response(database: str, collection: str, filter_: dict[str, Any] | None,
                  limit: int = 10) -> dict[str, Any]:
    if database == "acme_prod" and collection == "users":
        rows = _filter_users(filter_)
        return {
            "database": database,
            "collection": collection,
            "filter": filter_ or {},
            "matched_count": len(rows),
            "returned": rows[:limit],
        }
    if database == "acme_prod" and collection == "orders":
        # naive: no filter understanding for orders beyond status
        rows = _ORDERS
        if filter_ and "status" in filter_:
            rows = [r for r in rows if r["status"] == filter_["status"]]
        return {
            "database": database,
            "collection": collection,
            "filter": filter_ or {},
            "matched_count": len(rows),
            "returned": rows[:limit],
        }
    return {"matched_count": 0, "returned": []}


def count_response(database: str, collection: str, filter_: dict[str, Any] | None) -> dict[str, Any]:
    payload = find_response(database, collection, filter_, limit=0)
    return {
        "database": database,
        "collection": collection,
        "filter": filter_ or {},
        "count": payload.get("matched_count", 0),
    }


def aggregate_response(database: str, collection: str, pipeline: list[dict[str, Any]]) -> dict[str, Any]:
    """Minimal aggregation support: $match then $group by plan for users,
    by status for orders. Any other pipeline returns a canned realistic shape."""
    if database == "acme_prod" and collection == "users":
        rows = _USERS
        # $match
        for stage in pipeline:
            if "$match" in stage:
                rows = _filter_users(stage["$match"])
                break
        groups: dict[str, int] = {}
        for r in rows:
            groups[r["plan"]] = groups.get(r["plan"], 0) + 1
        return {"results": [{"_id": k, "count": v} for k, v in groups.items()]}
    if database == "acme_prod" and collection == "orders":
        rows = _ORDERS
        groups: dict[str, dict[str, float]] = {}
        for r in rows:
            g = groups.setdefault(r["status"], {"count": 0, "total_usd": 0.0})
            g["count"] += 1
            g["total_usd"] += r["total_usd"]
        return {
            "results": [
                {"_id": k, "count": v["count"], "total_usd": round(v["total_usd"], 2)}
                for k, v in groups.items()
            ],
        }
    return {"results": []}


def _make_server() -> Server:
    server = Server("mongodb-stub")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="list_databases",
                 description="List databases on this MongoDB cluster.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="list_collections",
                 description="List collections in a database.",
                 inputSchema={"type": "object",
                              "properties": {"database": {"type": "string"}},
                              "required": ["database"]}),
            Tool(name="collection_schema",
                 description="Return inferred field types for a collection.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "database": {"type": "string"},
                                  "collection": {"type": "string"},
                              },
                              "required": ["database", "collection"]}),
            Tool(name="find",
                 description="Run a MongoDB find query. Returns up to `limit` matched documents.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "database": {"type": "string"},
                                  "collection": {"type": "string"},
                                  "filter": {"type": "object"},
                                  "limit": {"type": "integer", "default": 10},
                              },
                              "required": ["database", "collection"]}),
            Tool(name="count",
                 description="Count documents matching a filter.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "database": {"type": "string"},
                                  "collection": {"type": "string"},
                                  "filter": {"type": "object"},
                              },
                              "required": ["database", "collection"]}),
            Tool(name="aggregate",
                 description="Run a MongoDB aggregation pipeline. Supports $match and $group.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "database": {"type": "string"},
                                  "collection": {"type": "string"},
                                  "pipeline": {"type": "array",
                                               "items": {"type": "object"}},
                              },
                              "required": ["database", "collection", "pipeline"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        a = arguments
        if name == "list_databases":
            payload = list_databases_response()
        elif name == "list_collections":
            payload = list_collections_response(a.get("database", ""))
        elif name == "collection_schema":
            payload = collection_schema_response(a.get("database", ""), a.get("collection", ""))
        elif name == "find":
            payload = find_response(a.get("database", ""), a.get("collection", ""),
                                    a.get("filter") or {}, int(a.get("limit") or 10))
        elif name == "count":
            payload = count_response(a.get("database", ""), a.get("collection", ""),
                                     a.get("filter") or {})
        elif name == "aggregate":
            payload = aggregate_response(a.get("database", ""), a.get("collection", ""),
                                         a.get("pipeline") or [])
        else:
            payload = {"error": f"unknown tool {name!r}"}
        return [TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]

    return server


async def _main() -> None:
    server = _make_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
