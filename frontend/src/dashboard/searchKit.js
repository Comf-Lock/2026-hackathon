// Single swap point for the shared search kit.
//
// Agent-1 owns the real SearchMask.vue / EventList.vue / useEventSearch.js (built against the
// interface fixed in the Agent-2 brief). The dashboard imports them through this module so the
// swap from the earlier local stubs was a one-place change — DashboardView.vue needs no edits.
export { default as SearchMask } from '../components/SearchMask.vue'
export { default as EventList } from '../components/EventList.vue'
export { useEventSearch } from '../composables/useEventSearch.js'
