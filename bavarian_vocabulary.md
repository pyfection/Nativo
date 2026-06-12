# Bavarian vocabulary — UI extraction

## Done (166 entries inserted, 8 PATCHed)

- batch 1: 5 · batch 2: 5 · bulk: 120 · batch 3: 27 · batch 4: 3 · sai/sei cleanup: 4 · sau split: 2
- `bedincbráh` notes corrected to reference *bedina* (verb stem)
- `sai`: verb → noun (PATCH), then singular → **plural "pigs"** (PATCH again)
- English `pig` entry renamed to `pigs` (plural) to match the now-corrected `sai`
- New `sau` (singular "pig") added with its own English `pig` (singular) link
- `bin`, `bist`, `is`, `san`, `han` notes updated from *form-of:sai* → *form-of:sei*
- New: **`sei`** (verb, "to be"), **`saids`** (2pl form of *sei*; dual/plural), **`se`** (formal-polite "you")

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
