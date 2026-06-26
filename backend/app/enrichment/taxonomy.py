"""Fixed taxonomy for the LLM weighting step (slice 4).

Two orthogonal axes are estimated from an event's text:

1. **Topic mix** over a fixed set of ~12 canonical IT fields — the main weighting bar.
   A fixed taxonomy (not free tags) is what makes the bar comparable across events,
   stable in colour, filterable, and matchable against a user's profile interests.
2. **Intent mix** over 4 fixed character axes — the compact "what kind of event is this"
   readout (the original Ground-News-style angle: deep-tech vs recruiting vs sales vs networking).

These constants are the single source of truth: the LLM is constrained to these exact keys
(enum-validated structured output), the normaliser drops anything off-list, and the frontend
colour map keys off the same slugs.
"""
from __future__ import annotations

# Canonical IT topic fields. Slug -> human label. Order is the canonical display order.
TOPIC_FIELDS: dict[str, str] = {
    "web_frontend": "Web & Frontend",
    "backend_cloud": "Backend & Cloud",
    "data_ai": "Data & AI",
    "devops_platform": "DevOps & Platform",
    "security": "Security",
    "mobile": "Mobile",
    "embedded_iot": "Embedded & IoT",
    "product_ux": "Product & UX",
    "career_recruiting": "Career & Recruiting",
    "community_networking": "Community & Networking",
    "business_startup": "Business & Startup",
    "research_academia": "Research & Academia",
}

# Intent character axes. Slug -> human label.
INTENT_AXES: dict[str, str] = {
    "deep_tech": "Deep Tech",
    "recruiting": "Recruiting",
    "vendor_sales": "Vendor / Sales",
    "networking": "Networking",
}

TOPIC_SLUGS: tuple[str, ...] = tuple(TOPIC_FIELDS)
INTENT_SLUGS: tuple[str, ...] = tuple(INTENT_AXES)
