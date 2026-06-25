// Single swap point for the shared search kit.
//
// Agent-1 OWNS the real SearchMask.vue / EventList.vue / useEventSearch.js and builds them
// against the interface fixed in the Agent-2 brief. Until those are merged, this module
// re-exports Agent-2's local stubs (same interface). When Agent-1's components land, replace
// the three lines below with the real imports — DashboardView.vue needs NO changes:
//
//   export { default as SearchMask } from '../components/SearchMask.vue'
//   export { default as EventList } from '../components/EventList.vue'
//   export { useEventSearch } from '../composables/useEventSearch.js'
//
export { default as SearchMask } from './SearchMaskStub.vue'
export { default as EventList } from './EventListStub.vue'
export { useEventSearch } from './useEventSearchStub.js'
