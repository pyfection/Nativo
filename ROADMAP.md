# Roadmap

## Prioritized — next up (agreed 2026-07-11)

Ranked by value after the open-platform + learning-path work landed.

1. **Suggester tier — fix the contribution dead-end.** `done`
   Shipped in two phases. Phase A (words): authenticated users submit new
   words as `LexemeStatus.PENDING_REVIEW` instead of 403; `can_verify`
   holders get a review queue at /review (approve → published+verified,
   reject → archived with note); auto-grant `can_edit` after 5 approved
   suggestions; permission notices became "suggest it". Phase B (texts):
   `Text.status` column (pending_review/published/archived), non-editors'
   documents/translations land pending, published-only filtering on all
   document reads (list/detail/links, activity feed, statistics, learning
   path) with author + reviewer visibility, text queue/approve/reject
   endpoints, texts section on /review, suggest mode on the add-document
   form. Still deferred: edits to existing records (ChangeProposal queue,
   per CLAUDE.md) and counting approved *texts* toward auto-promotion
   (currently words only).
2. **Durable audio, then narrated texts.** `done`
   Durable half: `file_storage` gained an S3-compatible backend — set
   `BUCKET_NAME` (on Fly: `fly storage create` for Tigris) and uploads go
   to the bucket, served via presigned redirects at `/uploads/*`; local
   disk stays the dev default; `backend/scripts/migrate_uploads_to_s3.py`
   copies existing blobs across; deleting audio now removes the blob too.
   *Ops step still required in prod: run `fly storage create` (or attach
   the volume from fly.toml) — without either, uploads remain ephemeral.*
   Value half: `Audio.text_id` narration — editors record/upload per text
   on the document page, learners get a play bar in the guided reader.
3. **Cheaper word-linking.** `done`
   The linker now auto-confirms tokens matching exactly ONE published word
   form (nothing for a human to decide); homographs get a distinct 0.8
   confidence and stay suggestions, spelling-variant matches stay 0.5. A
   "Confirm N exact matches" bulk button on the linking page clears
   pre-existing 1.0 suggestions in one click, the linking header shows live
   coverage ("X% of words linked · N left · ✓ ready for the learning
   path"), and the documents list shows a color-coded coverage badge per
   document (editors only). The linker also matches published lexemes only
   now — pending/draft/archived words can't link themselves into texts.
   Accepted risk (revisit if it bites): if a later dictionary addition
   turns a spelling into a homograph, earlier auto-confirmed links for that
   spelling are not demoted automatically (they carry an
   "Auto-confirmed: unique exact match" note, so they're findable).
4. **Learning retention: review mode + placement.** `done`
   Review mode: /learn shows a practice card whenever the user has shaky
   words (score < 3, published, weakest-first) — a flashcard round with
   show-answer (translations, IPA, pronunciation audio), "I knew it" (+1)
   / "I didn't know" (−1), and an end-of-round summary. Placement: fresh
   accounts get an "Already speak some X?" card; "I understand some"
   seeds the top 30% most corpus-frequent lexemes as known (score 3),
   "I speak it fairly well" the top 70% — gap-filling only, existing
   scores are never lowered, so re-running is safe. Frequency comes from
   confirmed-link counts, published lexemes only.
5. **Account survival basics.** Password reset (today a forgotten password
   permanently loses a contributor) and email verification (unblocks
   suggestion-approved notifications — the reward loop for item 1).

Honorable mentions, unscheduled: mobile/PWA audit for the reader;
author-facing "this draft introduces N new words" difficulty report; error
monitoring before real users; Bavarian for the deep editor tools (en/es
done, bar falls back to English by design).

---

Things we've intentionally deferred. Add new items at the bottom with a short note on *why later*.

## Deferred — design / content (Tier C from the UX rework)

- **Photography + illustration system per language.** Bavarian → alpine motif + heraldic blue/white. Lenape → eastern woodlands. Etc. Needs sourcing or commissioning; do this when there's content/contributor density to justify it.
- **Map of speakers and contributors.** Leaflet/Mapbox. Powerful for endangered-language UX but only meaningful once contributor count > 50ish.
- **Founder note / `/about` page.** A signed paragraph from the maintainer explaining the *why*. Punt until the project has a stable identity.
- **"Why this matters" mini-essay.** 200-word emotional anchor linked from the hero.
- **Newsletter / activity digest.** Weekly summary email.

## Deferred — features

- **Audio upload.** ~~Backend currently has a read-only `/api/v1/audio/` listing.~~ *Done for words: multipart upload endpoint + per-WordForm recorder UI exist. Remaining: durable storage and per-text narration — now prioritized item 2 above.*
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
