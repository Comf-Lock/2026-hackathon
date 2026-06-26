// Presentation helpers for the event card: how raw Event/EventOut data becomes the
// Ground-News-style display (source-reconciliation chips, the tag-weighting spectrum bar).
// Pure functions, no Vue — easy to unit-test and reuse across LandingView + DashboardView.

// --- Description cleanup -------------------------------------------------------------------
// Scraped descriptions arrive dirty: literal "\n" escape sequences, HTML entities (&amp;,
// &#8211;, &nbsp;), leftover markup and runaway whitespace. We clean at the display layer (pure,
// string-only — no DOM) so the fix is frontend-contained and unit-testable; the rendered <p> uses
// `white-space: pre-line` so the real newlines this produces are honoured. If adapters are found to
// persist broken text at the source, that is a separate backend follow-up — see HANDOFF.

const NAMED_ENTITIES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
  ndash: '–', mdash: '—', hellip: '…', laquo: '«', raquo: '»', bull: '•', middot: '·',
  euro: '€', copy: '©', reg: '®', trade: '™', deg: '°',
  auml: 'ä', ouml: 'ö', uuml: 'ü', Auml: 'Ä', Ouml: 'Ö', Uuml: 'Ü', szlig: 'ß',
}

function fromCodePoint(cp) {
  try {
    return String.fromCodePoint(cp)
  } catch {
    return ''
  }
}

function decodeEntities(s) {
  return s
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => fromCodePoint(parseInt(d, 10)))
    .replace(/&([a-zA-Z][a-zA-Z0-9]*);/g, (m, name) =>
      Object.prototype.hasOwnProperty.call(NAMED_ENTITIES, name) ? NAMED_ENTITIES[name] : m,
    )
}

// Turn a raw scraped description into clean, readable plain text with real line breaks.
export function cleanDescription(text) {
  if (!text) return ''
  let s = String(text)
  // 1. Literal escape sequences (backslash-n etc.) that survived a JSON-ish scrape → real breaks.
  s = s.replace(/\\r\\n|\\n|\\r/g, '\n').replace(/\\t/g, ' ')
  // 2. Block-level markup → newline, then strip any remaining tags.
  s = s
    .replace(/<\s*br\s*\/?\s*>/gi, '\n')
    .replace(/<\/\s*(p|div|li|h[1-6])\s*>/gi, '\n')
    .replace(/<[^>]+>/g, '')
  // 3. Decode HTML entities (numeric + common named).
  s = decodeEntities(s)
  // 4. Normalise whitespace: collapse spaces/tabs/nbsp, trim each line, cap blank-line runs.
  s = s
    .replace(/[ \t ]+/g, ' ')
    .split('\n')
    .map((line) => line.trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  return s
}

// adapter (EventSource.source_adapter) -> platform label / icon letter / accent colour.
// Several meetup_* ICS adapters collapse to one "Meetup" platform in the UI.
const SOURCE_META = {
  meetup: { label: 'Meetup', letter: 'M', color: '#e5575f' },
  meetup_wue_data: { label: 'Meetup', letter: 'M', color: '#e5575f' },
  meetup_wue_deeplearning: { label: 'Meetup', letter: 'M', color: '#e5575f' },
  meetup_wue_frontend: { label: 'Meetup', letter: 'M', color: '#e5575f' },
  meetup_wue_softwaredev: { label: 'Meetup', letter: 'M', color: '#e5575f' },
  eventbrite_wue: { label: 'Eventbrite', letter: 'E', color: '#f0762b' },
  thws_fiw: { label: 'THWS-FIW', letter: 'T', color: '#1f9d76' },
  frizz_wuerzburg: { label: 'FRIZZ', letter: 'F', color: '#9c5cab' },
  zdi_gruenderzentren: { label: 'ZDI', letter: 'Z', color: '#2f7bd6' },
}

export function sourceMeta(adapter) {
  return (
    SOURCE_META[adapter] || {
      label: adapter || 'Quelle',
      letter: (adapter || '?').charAt(0).toUpperCase(),
      color: '#6b7686',
    }
  )
}

// Distinct platforms an event was found on (dedupes the meetup_* adapters by label).
export function distinctSources(sources) {
  const byLabel = new Map()
  for (const s of sources || []) {
    const meta = sourceMeta(s.adapter)
    if (!byLabel.has(meta.label)) byLabel.set(meta.label, { ...meta, url: s.url })
  }
  return [...byLabel.values()]
}

// Visibility magnitude from the number of distinct sources an event was found on. This reframes
// the old "Blindspot" (a gap metric, negative) as a *positive* signal: more independent sources
// listing the same event → higher visibility/popularity. The badge grows more prominent with the
// tier, never less. `count` is distinctSources(...).length.
//   1     → exclusive find (a discovery, not a deficit)
//   2–3   → listed on several sources
//   4+    → high visibility across the region
export function visibilityTier(count) {
  const n = count || 0
  if (n >= 4) {
    return {
      key: 'high',
      badge: `Hohe Sichtbarkeit · ${n} Quellen`,
      tooltip: `Auf ${n} Quellen in der Region gelistet.`,
    }
  }
  if (n >= 2) {
    return {
      key: 'multi',
      badge: `Mehrfach gelistet · ${n} Quellen`,
      tooltip: `Auf ${n} unabhängigen Quellen gefunden.`,
    }
  }
  return {
    key: 'exclusive',
    badge: '★ Exklusiv gelistet',
    tooltip: 'Aktuell nur über eine Quelle gefunden.',
  }
}

// Canonical IT topic taxonomy — slug -> { label, color }. MUST mirror backend
// app/enrichment/taxonomy.py (TOPIC_FIELDS): the LLM emits these exact slugs and the bar keys off
// them, so a stable colour per field stays comparable across every card.
export const TOPIC_META = {
  web_frontend: { label: 'Web & Frontend', color: '#2f7bd6' },
  backend_cloud: { label: 'Backend & Cloud', color: '#1f9d76' },
  data_ai: { label: 'Data & AI', color: '#b8324f' },
  devops_platform: { label: 'DevOps & Platform', color: '#0e8a8a' },
  security: { label: 'Security', color: '#c2557a' },
  mobile: { label: 'Mobile', color: '#7a5cd0' },
  embedded_iot: { label: 'Embedded & IoT', color: '#6b8e23' },
  product_ux: { label: 'Product & UX', color: '#d98a2b' },
  career_recruiting: { label: 'Career & Recruiting', color: '#9c5cab' },
  community_networking: { label: 'Community & Networking', color: '#2f9bb3' },
  business_startup: { label: 'Business & Startup', color: '#cc7a14' },
  research_academia: { label: 'Research & Academia', color: '#5a6b8c' },
}

// Intent character axes — slug -> { label, color }. Mirrors backend INTENT_AXES.
export const INTENT_META = {
  deep_tech: { label: 'Deep Tech', color: '#b8324f' },
  recruiting: { label: 'Recruiting', color: '#9c5cab' },
  vendor_sales: { label: 'Vendor / Sales', color: '#d98a2b' },
  networking: { label: 'Networking', color: '#1f9d76' },
}

// Map a {slug: int} weight dict onto display segments, sorted by weight desc. Used for both the
// topic bar (TOPIC_META) and the intent mix (INTENT_META). Unknown slugs are skipped defensively.
function segmentsFrom(weights, meta) {
  if (!weights || typeof weights !== 'object') return []
  return Object.entries(weights)
    .filter(([slug, pct]) => meta[slug] && Number(pct) > 0)
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .map(([slug, pct]) => ({ tag: meta[slug].label, color: meta[slug].color, pct: Number(pct) }))
}

// Real LLM topic distribution for the bar (empty until the event is scored).
export function topicWeights(event) {
  return segmentsFrom(event && event.topic_weights, TOPIC_META)
}

// Real LLM intent distribution (deep-tech / recruiting / sales / networking).
export function intentMix(event) {
  return segmentsFrom(event && event.intent_weights, INTENT_META)
}

// Below this LLM confidence the bar is real data but flagged "geschätzt" — honest about a weak read.
const LOW_CONFIDENCE = 0.45

// The topic-weighting bar for a card — ONLY real LLM topic_weights. There is deliberately no
// placeholder and no tag-derived fallback: an event that has not been LLM-scored shows no bar at
// all ("either rated or not shown"). Returns null when there are no real weights, otherwise
// { segments, estimated } where `estimated` flags a low-confidence (but still real) read.
export function weightBar(event) {
  const ev = event || {}
  const topics = topicWeights(ev)
  if (!topics.length) return null
  const conf = ev.score_confidence
  const estimated = typeof conf === 'number' && conf < LOW_CONFIDENCE
  return { segments: topics, estimated }
}
