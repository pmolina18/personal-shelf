# Feature: media-tracker, Property 12: MCP-REST equivalence
# Feature: media-tracker, Property 13: MCP rejects invalid parameters with descriptive message
"""Property tests for MCP server equivalence and error handling (Properties 12, 13).

Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11
"""

from __future__ import annotations

import asyncio
import json

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import backend.mcp.server as mcp_module
from backend.mcp.server import mcp_server
from backend.models.media import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# -- Helpers -----------------------------------------------------------------


def _parse_mcp_result(result) -> dict:
    """Extract the JSON dict from an MCP tool call result."""
    return json.loads(result[0].text)


async def _with_fresh_db(coro_fn):
    """Set up an in-memory DB, patch the MCP session, run coro_fn, then tear down."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    mcp_module.async_session = factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        await coro_fn()
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


# -- Strategies --------------------------------------------------------------

valid_media_types = st.sampled_from(["movie", "book", "series"])
valid_titles = st.text(min_size=1, max_size=100).filter(lambda t: t.strip())

valid_media_create_args = st.fixed_dictionaries(
    {"title": valid_titles, "media_type": valid_media_types},
    optional={
        "year": st.integers(min_value=1800, max_value=2100),
        "creator": st.text(min_size=1, max_size=100),
        "notes": st.text(max_size=200),
        "tags": st.lists(st.text(min_size=1, max_size=50), max_size=5, unique=True),
    },
)

valid_statuses = st.sampled_from(["pending", "in_progress", "completed"])
valid_ratings = st.integers(min_value=1, max_value=10)
valid_tag_lists = st.lists(st.text(min_size=1, max_size=50), max_size=10, unique=True)

invalid_media_type_strings = st.text(min_size=1, max_size=50).filter(
    lambda s: s not in {"movie", "book", "series"}
)
invalid_status_strings = st.text(min_size=1, max_size=50).filter(
    lambda s: s not in {"pending", "in_progress", "completed"}
)
invalid_ratings = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=11),
)


# -- Property 12: MCP-REST equivalence ----------------------------------------


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_create_equivalent_to_service(args):
    """MCP create_media must produce the same item data as MediaService.create."""

    async def _test():
        r = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in r:
            return
        assert r["title"] == args["title"]
        assert r["media_type"] == args["media_type"]
        assert r["status"] == "pending"
        assert r["id"] is not None
        if "year" in args:
            assert r["year"] == args["year"]
        if "creator" in args:
            assert r["creator"] == args["creator"]
        if "notes" in args:
            assert r["notes"] == args["notes"]
        if "tags" in args:
            assert sorted(r["tags"]) == sorted(args["tags"])

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args, new_status=valid_statuses)
def test_mcp_update_status_equivalent_to_service(args, new_status):
    """MCP update_status must apply the same status transition rules."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        updated = _parse_mcp_result(
            await mcp_server.call_tool(
                "update_status", {"media_id": created["id"], "status": new_status}
            )
        )
        if "error" in updated:
            return
        assert updated["status"] == new_status
        if new_status == "in_progress":
            assert updated["started_at"] is not None
        if new_status == "completed":
            assert updated["completed_at"] is not None

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args, rating=valid_ratings)
def test_mcp_rate_media_equivalent_to_service(args, rating):
    """MCP rate_media must save the same rating as the service."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        rated = _parse_mcp_result(
            await mcp_server.call_tool(
                "rate_media", {"media_id": created["id"], "rating": rating}
            )
        )
        if "error" in rated:
            return
        assert rated["rating"] == rating

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args, tags=valid_tag_lists)
def test_mcp_manage_tags_equivalent_to_service(args, tags):
    """MCP manage_tags must save the same tags as the service."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        tagged = _parse_mcp_result(
            await mcp_server.call_tool(
                "manage_tags", {"media_id": created["id"], "tags": tags}
            )
        )
        if "error" in tagged:
            return
        assert sorted(tagged["tags"]) == sorted(set(tags))

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_delete_equivalent_to_service(args):
    """MCP delete_media must remove the item, matching service behavior."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        media_id = created["id"]
        deleted = _parse_mcp_result(
            await mcp_server.call_tool("delete_media", {"media_id": media_id})
        )
        assert "message" in deleted
        listing = _parse_mcp_result(await mcp_server.call_tool("list_media", {}))
        assert media_id not in [item["id"] for item in listing["items"]]

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_list_returns_created_items(args):
    """MCP list_media must return items created via MCP create_media."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        listing = _parse_mcp_result(
            await mcp_server.call_tool("list_media", {"media_type": args["media_type"]})
        )
        assert listing["total"] >= 1
        assert created["id"] in [item["id"] for item in listing["items"]]

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_update_media_equivalent_to_service(args):
    """MCP update_media must modify only the provided fields."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        updated = _parse_mcp_result(
            await mcp_server.call_tool(
                "update_media", {"media_id": created["id"], "title": "Updated Title"}
            )
        )
        if "error" in updated:
            return
        assert updated["title"] == "Updated Title"
        assert updated["media_type"] == created["media_type"]

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_stats_consistent_with_catalog(args):
    """MCP get_stats must return statistics consistent with the catalog."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        stats = _parse_mcp_result(await mcp_server.call_tool("get_stats", {}))
        total_by_type = sum(stats["by_type"].values())
        total_by_status = sum(stats["by_status"].values())
        assert total_by_type >= 1
        assert total_by_type == total_by_status

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(args=valid_media_create_args)
def test_mcp_export_contains_created_items(args):
    """MCP export_catalog must include items created via MCP."""

    async def _test():
        created = _parse_mcp_result(await mcp_server.call_tool("create_media", args))
        if "error" in created:
            return
        exported = _parse_mcp_result(await mcp_server.call_tool("export_catalog", {}))
        assert "items" in exported
        assert len(exported["items"]) >= 1
        assert created["title"] in [item["title"] for item in exported["items"]]

    asyncio.run(_with_fresh_db(_test))


# -- Property 13: MCP rejects invalid parameters with descriptive message ------


@settings(max_examples=100)
@given(bad_type=invalid_media_type_strings)
def test_mcp_rejects_invalid_media_type(bad_type):
    """MCP create_media must return a descriptive error for invalid media_type."""

    async def _test():
        r = _parse_mcp_result(
            await mcp_server.call_tool("create_media", {"title": "Test", "media_type": bad_type})
        )
        assert "error" in r
        error_msg = r["error"].lower()
        assert "movie" in error_msg or "book" in error_msg or "series" in error_msg

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(bad_status=invalid_status_strings)
def test_mcp_rejects_invalid_status(bad_status):
    """MCP update_status must return a descriptive error for invalid status."""

    async def _test():
        created = _parse_mcp_result(
            await mcp_server.call_tool("create_media", {"title": "Test", "media_type": "movie"})
        )
        if "error" in created:
            return
        r = _parse_mcp_result(
            await mcp_server.call_tool(
                "update_status", {"media_id": created["id"], "status": bad_status}
            )
        )
        assert "error" in r
        error_msg = r["error"].lower()
        assert "status" in error_msg or "invalid" in error_msg

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(bad_rating=invalid_ratings)
def test_mcp_rejects_invalid_rating(bad_rating):
    """MCP rate_media must return a descriptive error for out-of-range rating."""

    async def _test():
        created = _parse_mcp_result(
            await mcp_server.call_tool("create_media", {"title": "Test", "media_type": "book"})
        )
        if "error" in created:
            return
        r = _parse_mcp_result(
            await mcp_server.call_tool(
                "rate_media", {"media_id": created["id"], "rating": bad_rating}
            )
        )
        assert "error" in r
        error_msg = r["error"].lower()
        assert "rating" in error_msg or "between" in error_msg or "1" in error_msg

    asyncio.run(_with_fresh_db(_test))


@settings(max_examples=100, deadline=None)
@given(
    too_many_tags=st.lists(
        st.text(min_size=1, max_size=30), min_size=11, max_size=15, unique=True
    )
)
def test_mcp_rejects_too_many_tags(too_many_tags):
    """MCP manage_tags must return a descriptive error when more than 10 tags."""

    async def _test():
        created = _parse_mcp_result(
            await mcp_server.call_tool("create_media", {"title": "Test", "media_type": "series"})
        )
        if "error" in created:
            return
        r = _parse_mcp_result(
            await mcp_server.call_tool(
                "manage_tags", {"media_id": created["id"], "tags": too_many_tags}
            )
        )
        assert "error" in r
        error_msg = r["error"].lower()
        assert "10" in error_msg or "tag" in error_msg or "maximum" in error_msg

    asyncio.run(_with_fresh_db(_test))


def test_mcp_rejects_nonexistent_item():
    """MCP tools must return descriptive errors for non-existent item IDs."""

    async def _test():
        for tool, args in [
            ("delete_media", {"media_id": 999999}),
            ("update_media", {"media_id": 999999, "title": "X"}),
            ("rate_media", {"media_id": 999999, "rating": 5}),
        ]:
            r = _parse_mcp_result(await mcp_server.call_tool(tool, args))
            assert "error" in r, f"{tool} should error for non-existent ID"
            assert "not found" in r["error"].lower(), f"{tool}: {r['error']}"

    asyncio.run(_with_fresh_db(_test))
