# Bavarian vocabulary — UI extraction

## Status (post Lexeme/WordForm refactor — 2026-06-12)

The `Word` model was split into `Lexeme` + `WordForm` in commit `f0188f7`; the migration dropped all prior data. We re-inserted from scratch using the new shape via `scripts/reinsert_bavarian_vocab.py`.

**Current prod state:** **176 Bavarian lexemes** (198 WordForms total) + **158 English lexemes** + **176 translation links**.

The major regroupings vs. the old 197-row flat layout:

- **Paradigm lexemes** (one lexeme, many forms):
  - `sei` (to be): 7 forms — `sei` + `bin/bist/is/saids/san/han`
  - `hóm` (to have): 5 forms — `hóm` + `hób/hóst/hód/hóbds`
  - `máha` (to do): 5 forms — `máha` + `máh/máhsd/máhd/máhds`
  - `ségn` (to see): 2 forms — `ségn` + `sig` (imperative + 1sg)
  - `suaha` (to search): 3 forms — `suaha` + `suah/suaht`
  - `gém` (to give): 2 forms — `gém` + `gibd`
  - Noun pairs: `voat/veata`, `cbráh/cbráha`, `kind/kinda`, `sau/sai`
- **Homographs kept distinct** (same surface, different lexeme): `si`×2, `es`×2, `de`×2, `suah`×2.
- **Article paradigm** stays as separate lexemes (not forms of a master "the"): `da`, `de`, `dem`, `dera`, `'n`, `s'`, `d'`, `koa`, `koane`, `koam`, `koana`, `oa`, `oana`, `den`, `dene`, `an`, `a`, `des`.
- **Contractions** (`af'm`, `im`, `mid'm`, `fia'n`, `fom`, `dsum`, `aus'm`) stay as distinct preposition lexemes.
- **Past-participle adjectives** (`dahóitne`, `midgmáhd`, etc.) stay as distinct lexemes, not forms of the parent verb.
- **Dropped:** day-1 smoke entries (the orphan `is`-with-no-paradigm and the literal "test" row… wait, `test` was kept as a placeholder for the test page).

## Case examples — for your B. question

You aren't a linguist; the cases ARE confusing in textbook terms. Here they are in plain English first, then Bavarian.

### Nominative — the **doer** of the sentence

The thing doing the action.

| English | Bavarian |
| --- | --- |
| **The man** sleeps. | **Da mo** schlóft. |
| **The dog** runs. | **Da hund** laft. |
| **The mother** cooks. | **D' muada** koht. |
| **The book** is on the table. | **S' buah** is af'm tisch. |
| **The children** laugh. | **De kinda** lahn. |

This is the "default" form — what you'd say if you were just naming something.

### Accusative — the **target** of the action

What's being seen, eaten, read, held, etc.

| English | Bavarian |
| --- | --- |
| I see **the man**. | I siah **an mo**. |
| I read **the book**. | I lis **s' buah**. |
| She loves **the dog**. | Si magt **an hund**. |
| We greet **the children**. | Mia grießn **de kinda**. |

Key insight: only **masculine singular** changes form (`da` → `an` / `'n`). Feminine, neuter, plural stay the same as nominative.

### Dative — the **recipient**, or after certain prepositions

What you give *to*, talk *to*, or where you are.

| English | Bavarian |
| --- | --- |
| I give **the man** a book. | I gib **am mo** a buah. |
| I help **the woman**. | I hilf **da frau**. |
| I trust **the children**. | I trau **de kindan**. |
| The book lies on **the table**. | S' buah liagt af'm tisch. |
| I come from **the house**. | I kim aus'm haus. |

Dative is what `aus'm`, `foa'm`, `am`, `dsum` are — all preposition + dative-article contractions.

### Genitive — **of the X** / **X's**

Possession or relation.

| English | Bavarian (most common: `fo` + dat) |
| --- | --- |
| The book **of the man** / **the man's** book | S' buah **fom mo**. |
| The colour **of the wall** | D' farbe **fo da wand**. |
| The toys **of the children** | D' spuisachn **fo de kindan**. |

In speech Bavarian almost always uses *fo + dative* for "of-the". A pure genitive (like German *des Mannes*) exists in writing but is rare in speech.

---

## Still pending — please mark up

With those examples in mind, here's the article paradigm again. Fill in / correct the cells, and I'll insert the missing forms with `gender / case / plurality` set per cell.

### Definite article — *the*

| Case | Masc sg | Fem sg | Neut sg | Plural |
| --- | --- | --- | --- | --- |
| **Nominative** ("doer") | `da` ✓ | `d'` ✓ | `s'` ✓ | `de` ✓ |
| **Accusative** ("target") | ⚠️ `an` / `'n`? | ⚠️ `d'` (= nom)? | ⚠️ `s'` (= nom)? | ⚠️ `de` (= nom)? |
| **Dative** ("recipient / after preposition") | `am` / `'m` ✓ — bare `dem` ✓ | ⚠️ `da`? `dera`? | `dem` ✓ | ⚠️ `de`? `dene`? |
| **Genitive** ("of the") | ⚠️ replaced with *fo + dat*? | `dera` ✓ | ⚠️ replaced with *fo + dat*? | ⚠️ `dera`? |

### Indefinite article — *a / an*

| Case | Masc sg | Fem sg | Neut sg |
| --- | --- | --- | --- |
| **Nominative** | `a` ✓ | `a` ✓ / `oana` ✓ | `a` ✓ |
| **Accusative** | ⚠️ `an` / `'n`? | ⚠️ `a`? `oana`? | ⚠️ `a`? |
| **Dative** | ⚠️ `am` / `'m`? | ⚠️ `oana`? `ana`? | ⚠️ `am`? |
| **Genitive** | ⚠️ rephrased with *fo*? | ⚠️ same? | ⚠️ same? |

### Negation — *no / none*

| Case | Masc sg | Fem sg | Neut sg | Plural |
| --- | --- | --- | --- | --- |
| **Nominative** | `koa` ✓ | `koa` ✓ | `koa` ✓ | `koane` ✓ |
| **Accusative** | ⚠️ `koan`? | ⚠️ `koa`? | ⚠️ `koa`? | ⚠️ `koane`? |
| **Dative** | ⚠️ `koam`? | ⚠️ `koana`? | ⚠️ `koam`? | ⚠️ `koane`? |
| **Genitive** | ⚠️ ? | ⚠️ `koana`? | ⚠️ ? | ⚠️ ? |

### Numeral *"one"*

| Form | Use | English | In DB? |
| --- | --- | --- | --- |
| `oans` | cardinal (the number 1) | one | ✓ (as pronoun, sense "someone") |
| `oa` | masc/neut counting | one | ⚠️ — does this exist standalone? |
| `oana` | feminine counting | one | ✓ (as determiner, sense "a (f)") |

### Common preposition + article contractions

Already in DB: `aus'm`, `foa'm`, `dsum`.

Likely missing — please confirm:

| Contraction | = | English |
| --- | --- | --- |
| `af'm` | af + dem | on the (m/n dat) |
| `in'm` | in + dem | in the (m/n dat) |
| `fia'n` | fia + an | for the (m acc) |
| `mid'm` | mid + dem | with the (m/n dat) |
| `fom` | fo + dem | of / from the |
| `in'a` | in + a | in a |
| `af'a` | af + a | on a |
