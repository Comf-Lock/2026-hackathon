"""Contract tests for GET /api/events (and /{id})."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import Event

NOW = datetime.now(timezone.utc)

EVENT_OUT_FIELDS = {
    "id", "title", "description", "start", "end", "is_online", "venue_name",
    "address", "city", "postal_code", "lat", "lng", "organizer", "tags", "url",
    "image_url", "price", "language", "sources",
}


def _mk(session, **kw) -> Event:
    defaults = dict(
        title="Event",
        start=NOW + timedelta(days=1),
        is_online=False,
        tags=[],
    )
    defaults.update(kw)
    ev = Event(**defaults)
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


def test_empty_search_returns_contract_shape(client):
    r = client.get("/api/events")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"total", "items"}
    assert body == {"total": 0, "items": []}


def test_item_has_every_eventout_field(client, session):
    _mk(session, title="Python Meetup", organizer="WUE Data", city="Würzburg", tags=["python"])
    body = client.get("/api/events").json()
    assert body["total"] == 1
    (item,) = body["items"]
    assert set(item.keys()) == EVENT_OUT_FIELDS
    assert item["title"] == "Python Meetup"
    # start is a parseable ISO8601 string. (The +TZ offset is preserved on Postgres/timestamptz;
    # SQLite — the test backend — round-trips datetimes naive, so we don't assert the offset here.)
    assert datetime.fromisoformat(item["start"]).date().isoformat().startswith("2026-")


def test_q_matches_title_description_organizer(client, session):
    _mk(session, title="Python Night")
    _mk(session, title="Rust Talk", description="deep dive into python internals")
    _mk(session, title="Design Jam", organizer="JavaScript Würzburg")
    _mk(session, title="Cooking Class")

    assert client.get("/api/events", params={"q": "python"}).json()["total"] == 2
    assert client.get("/api/events", params={"q": "javascript"}).json()["total"] == 1
    assert client.get("/api/events", params={"q": "nothinghere"}).json()["total"] == 0


def test_city_and_is_online_filters(client, session):
    _mk(session, title="A", city="Würzburg", is_online=False)
    _mk(session, title="B", city="Schweinfurt", is_online=False)
    _mk(session, title="C", city=None, is_online=True)

    assert client.get("/api/events", params={"city": "Würzburg"}).json()["total"] == 1
    assert client.get("/api/events", params={"is_online": "true"}).json()["total"] == 1
    assert client.get("/api/events", params={"is_online": "false"}).json()["total"] == 2


def test_tag_filter_any_match(client, session):
    _mk(session, title="A", tags=["python", "data"])
    _mk(session, title="B", tags=["javascript"])
    _mk(session, title="C", tags=[])

    assert client.get("/api/events", params={"tag": "python"}).json()["total"] == 1
    # repeatable tag → keep if ANY matches
    r = client.get("/api/events", params=[("tag", "python"), ("tag", "javascript")])
    assert r.json()["total"] == 2


def test_upcoming_default_excludes_past_but_date_from_includes(client, session):
    _mk(session, title="Past", start=NOW - timedelta(days=10))
    _mk(session, title="Future", start=NOW + timedelta(days=10))

    # default: only upcoming
    body = client.get("/api/events").json()
    assert body["total"] == 1 and body["items"][0]["title"] == "Future"

    # explicit date_from in the past surfaces the old event too
    past_day = (NOW - timedelta(days=20)).date().isoformat()
    assert client.get("/api/events", params={"date_from": past_day}).json()["total"] == 2


def test_sort_ascending_and_pagination(client, session):
    for i in range(5):
        _mk(session, title=f"E{i}", start=NOW + timedelta(days=i + 1))

    body = client.get("/api/events", params={"limit": 2, "offset": 0}).json()
    assert body["total"] == 5  # total reflects all matches, not the page
    assert [it["title"] for it in body["items"]] == ["E0", "E1"]  # ascending by start

    page2 = client.get("/api/events", params={"limit": 2, "offset": 2}).json()
    assert [it["title"] for it in page2["items"]] == ["E2", "E3"]


def test_limit_capped_at_100(client):
    assert client.get("/api/events", params={"limit": 101}).status_code == 422


def test_get_event_by_id_and_404(client, session):
    ev = _mk(session, title="Detail Me")
    ok = client.get(f"/api/events/{ev.id}")
    assert ok.status_code == 200
    assert ok.json()["title"] == "Detail Me"
    assert set(ok.json().keys()) == EVENT_OUT_FIELDS

    assert client.get("/api/events/99999999").status_code == 404
