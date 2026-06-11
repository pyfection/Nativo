# Roadmap

Things we've intentionally deferred. Add new items at the bottom with a short note on *why later*.

## Deferred — design / content (Tier C from the UX rework)

- **Photography + illustration system per language.** Bavarian → alpine motif + heraldic blue/white. Lenape → eastern woodlands. Etc. Needs sourcing or commissioning; do this when there's content/contributor density to justify it.
- **Map of speakers and contributors.** Leaflet/Mapbox. Powerful for endangered-language UX but only meaningful once contributor count > 50ish.
- **Founder note / `/about` page.** A signed paragraph from the maintainer explaining the *why*. Punt until the project has a stable identity.
- **"Why this matters" mini-essay.** 200-word emotional anchor linked from the hero.
- **Newsletter / activity digest.** Weekly summary email.

## Deferred — features

- **Audio upload.** Backend currently has a read-only `/api/v1/audio/` listing. Real upload needs: multipart endpoint, Fly volume or R2 storage, association to a word, frontend upload UI. Whole-feature work; do it once there's demand from a real speaker.
- **Contributor avatar strip on the home page.** Low payoff while contributor count = 1. Revisit when there are ≥ 5 active contributors.
- **Contributor quote panel on home page.** Maintainer has a real Bavarian sample line ready:
  *"Mei oma hód oivai Boaric gret. I hób's nia gfrágt vós fia veata si kent hód."*
  Pending a real name (and/or permission) to attribute it. When a real contributor quote with attribution is available, replace the 4-icon mission grid with a single quote+portrait component.
- **Audio sample on the hero.** A 5-second Bavarian clip + play button hooked into the hero. Pending a real recording from the maintainer.
- **Bavarian translations for new keys** added during the home-page redesign (`spotlight.*`, `endangerment.*`, the per-language `endangerment.body` strings). Currently English fallback in Bavarian UI mode.
- **Bidirectional contributor stats.** The `/contributors` page sums per-language; a profile page per contributor with all their languages would be nice once contributors join multiple.
- **Better empty audio CTA.** Once audio upload exists, the "Coming soon" notes need replacing.

## Deferred — code quality

- **`datetime.utcnow()` sweep** across `backend/app/models/*` and a few endpoints. Deprecated in 3.12; functional today but spamming warnings. Documented in CLAUDE.md.
- **Per-hook fix for the 5 frontend lint warnings** (4× `react-hooks/exhaustive-deps`, 1× `react-refresh/only-export-components`). Needs reasoning about each hook; not mechanical.
- **Audio + Documents listings: same backend filter pattern.** Documents page doesn't currently filter by language at the endpoint level; counts come from `/statistics` but the listing is unfiltered.

## Deferred — Bavarian standard

- Sections 2–10 of `bavarian_standard.md` are still stubs (phonology, morphology, syntax, lexicon, numerals, names, typography). The user is drafting these; don't generate Bavarian text the doc doesn't support yet.
