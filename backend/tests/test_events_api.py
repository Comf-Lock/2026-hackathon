"""Contract tests for GET /api/events (and /{id})."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import Event

NOW = datetime.now(timezone.utc)

EVENT_OUT_FIELDS = {
    "id", "title", "description", "start", "end", "is_online", "venue_name",
    "address", "city", "postal_code", "lat", "lng", "organizer", "tags", "url",
    "image_url", "price", "language",
    "topic_weights", "intent_weights", "score_confidence",
    "attendee_count", "attendance_source", "sources",
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


def test_tag_is_free_text_not_strict_membership(client, session):
    # Events rarely carry clean tags → tag is matched as free text over title/description/organizer
    # /tags (substring, case-insensitive), so the pitch demo finds something.
    _mk(session, title="Kubernetes Hands-on", tags=[])  # term only in the title
    _mk(session, title="Talk", description="A deep dive into Kubernetes operators", tags=[])
    _mk(session, title="Workshop", organizer="Kubernetes Würzburg", tags=[])
    _mk(session, title="Vue Night", tags=["frontend"])  # unrelated

    body = client.get("/api/events", params={"tag": "kubernetes"}).json()
    assert body["total"] == 3
    assert {it["title"] for it in body["items"]} == {"Kubernetes Hands-on", "Talk", "Workshop"}

    # Multiple terms are OR-ed (generous): kubernetes OR frontend → 3 + 1.
    multi = client.get("/api/events", params=[("tag", "kubernetes"), ("tag", "frontend")]).json()
    assert multi["total"] == 4


def test_default_includes_past_and_future(client, session):
    _mk(session, title="Past", start=NOW - timedelta(days=10))
    _mk(session, title="Future", start=NOW + timedelta(days=10))

    # default now returns past events too (still listed on their source); ongoing/upcoming first.
    body = client.get("/api/events").json()
    assert body["total"] == 2
    assert [it["title"] for it in body["items"]] == ["Future", "Past"]


def test_upcoming_true_excludes_past(client, session):
    _mk(session, title="Past", start=NOW - timedelta(days=10))
    _mk(session, title="Future", start=NOW + timedelta(days=10))

    body = client.get("/api/events", params={"upcoming": "true"}).json()
    assert body["total"] == 1 and body["items"][0]["title"] == "Future"


def test_ongoing_multiday_event_counts_as_upcoming(client, session):
    # AI-Week scenario: started days ago but runs into the future → ongoing, NOT past.
    _mk(session, title="AI Week", start=NOW - timedelta(days=3), end=NOW + timedelta(days=2))
    _mk(session, title="Done", start=NOW - timedelta(days=3), end=NOW - timedelta(days=1))

    body = client.get("/api/events", params={"upcoming": "true"}).json()
    assert body["total"] == 1 and body["items"][0]["title"] == "AI Week"


def test_default_ordering_upcoming_asc_then_past_desc(client, session):
    _mk(session, title="U-near", start=NOW + timedelta(days=1))
    _mk(session, title="U-far", start=NOW + timedelta(days=5))
    _mk(session, title="P-recent", start=NOW - timedelta(days=1))
    _mk(session, title="P-old", start=NOW - timedelta(days=5))

    titles = [it["title"] for it in client.get("/api/events").json()["items"]]
    assert titles == ["U-near", "U-far", "P-recent", "P-old"]


def test_date_from_overrides_default(client, session):
    _mk(session, title="Past", start=NOW - timedelta(days=10))
    _mk(session, title="Future", start=NOW + timedelta(days=10))

    # explicit date_from in the future restricts to events at/after it (overrides the include-past default)
    future_day = (NOW + timedelta(days=5)).date().isoformat()
    body = client.get("/api/events", params={"date_from": future_day}).json()
    assert body["total"] == 1 and body["items"][0]["title"] == "Future"


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


# --- Radius (Haversine air-line) search -----------------------------------------------------
# Würzburg centre; Schweinfurt ~37 km NE, Frankfurt ~95 km W, Nürnberg ~90 km SE.
WUE = (49.7913, 9.9534)
SCHWEINFURT = (50.0494, 10.2336)
FRANKFURT = (50.1109, 8.6821)


def test_radius_keeps_inside_excludes_outside(client, session):
    _mk(session, title="In-Wue", lat=WUE[0], lng=WUE[1])
    _mk(session, title="Near-SW", lat=SCHWEINFURT[0], lng=SCHWEINFURT[1])  # ~37 km → inside 40
    _mk(session, title="Far-FFM", lat=FRANKFURT[0], lng=FRANKFURT[1])  # ~95 km → outside 40

    params = {"lat": WUE[0], "lng": WUE[1], "radius_km": 40}
    body = client.get("/api/events", params=params).json()
    assert body["total"] == 2
    assert {it["title"] for it in body["items"]} == {"In-Wue", "Near-SW"}

    # A wide radius pulls the far one back in.
    wide = client.get("/api/events", params={**params, "radius_km": 120}).json()
    assert wide["total"] == 3


def test_radius_excludes_events_without_coordinates(client, session):
    _mk(session, title="Located", lat=WUE[0], lng=WUE[1])
    _mk(session, title="NoCoords", lat=None, lng=None)
    _mk(session, title="OnlineNoCoords", is_online=True, lat=None, lng=None)

    body = client.get("/api/events", params={"lat": WUE[0], "lng": WUE[1], "radius_km": 50}).json()
    assert body["total"] == 1 and body["items"][0]["title"] == "Located"


def test_radius_inactive_when_params_incomplete(client, session):
    _mk(session, title="A", lat=FRANKFURT[0], lng=FRANKFURT[1])
    _mk(session, title="B", lat=None, lng=None)

    # No radius params at all → unchanged (both returned, no geo exclusion).
    assert client.get("/api/events").json()["total"] == 2
    # lat/lng without radius_km → ignored, behaviour unchanged.
    assert client.get("/api/events", params={"lat": WUE[0], "lng": WUE[1]}).json()["total"] == 2


def test_radius_paginates_filtered_set(client, session):
    # Five located events all within range → radius + pagination compose.
    for i in range(5):
        _mk(session, title=f"R{i}", start=NOW + timedelta(days=i + 1), lat=WUE[0], lng=WUE[1])
    params = {"lat": WUE[0], "lng": WUE[1], "radius_km": 10, "limit": 2, "offset": 0}
    body = client.get("/api/events", params=params).json()
    assert body["total"] == 5  # total reflects the full in-radius set, not the page
    assert [it["title"] for it in body["items"]] == ["R0", "R1"]


def test_get_event_by_id_and_404(client, session):
    ev = _mk(session, title="Detail Me")
    ok = client.get(f"/api/events/{ev.id}")
    assert ok.status_code == 200
    assert ok.json()["title"] == "Detail Me"
    assert set(ok.json().keys()) == EVENT_OUT_FIELDS

    assert client.get("/api/events/99999999").status_code == 404
