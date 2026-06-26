// Presentation helpers for the event card: how raw Event/EventOut data becomes the
// Ground-News-style display (source-reconciliation chips, the tag-weighting spectrum bar).
// Pure functions, no Vue — easy to unit-test and reuse across LandingView + DashboardView.

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

// Palette tuned to the Mainfranken accent family — indexed (not hashed) so adjacent bar
// segments always differ in colour.
const TAG_PALETTE = ['#b8324f', '#d98a2b', '#9c5cab', '#1f9d76', '#2f7bd6', '#c2557a']

// Equal-weight split across an event's tags (3 tags -> thirds). This is the placeholder for the
// Ground-News-style "intent" bar; Slice 4's LLM intent-scoring later replaces the equal `pct`
// with real per-tag weights — the rendering stays the same.
export function tagWeights(tags) {
  const list = (tags || []).slice(0, 6)
  if (!list.length) return []
  const pct = 100 / list.length
  return list.map((tag, i) => ({ tag, color: TAG_PALETTE[i % TAG_PALETTE.length], pct }))
}
