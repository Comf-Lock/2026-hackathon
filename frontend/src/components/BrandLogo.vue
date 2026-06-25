<script setup>
defineProps({ size: { type: Number, default: 34 } })
</script>

<template>
  <svg class="mark" :width="size" :height="size" viewBox="0 0 48 48" aria-label="Event Radar Logo">
    <rect width="48" height="48" rx="13" fill="#1d2530" />
    <g fill="none" stroke="#38414f" stroke-width="1.4">
      <circle cx="24" cy="24" r="16" />
      <circle cx="24" cy="24" r="10.5" />
      <circle cx="24" cy="24" r="5" />
    </g>
    <g stroke="#2c3543" stroke-width="1.2">
      <line x1="8" y1="24" x2="40" y2="24" />
      <line x1="24" y1="8" x2="24" y2="40" />
    </g>
    <defs>
      <linearGradient id="hsweep" x1="24" y1="8" x2="40" y2="40" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#b8324f" stop-opacity="0.95" />
        <stop offset="1" stop-color="#b8324f" stop-opacity="0" />
      </linearGradient>
      <radialGradient id="hblip" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0" stop-color="#36c5a0" />
        <stop offset="1" stop-color="#36c5a0" stop-opacity="0" />
      </radialGradient>
    </defs>
    <path d="M24 24 L24 8 A16 16 0 0 1 37.86 16 Z" fill="url(#hsweep)" />
    <circle cx="33" cy="14" r="6" fill="url(#hblip)" />
    <circle cx="33" cy="14" r="2.4" fill="#36c5a0" />
    <circle cx="15.5" cy="30" r="1.8" fill="#36c5a0" fill-opacity="0.55" />
    <circle cx="24" cy="24" r="2.3" fill="#b8324f" />
  </svg>
</template>

<style scoped>
.mark { flex: 0 0 auto; }
</style>
