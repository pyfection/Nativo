# Bavarian vocabulary — UI extraction

## Done (160 entries inserted, 1 PATCHed)

- batch 1: 5 · batch 2: 5 · bulk: 120 · batch 3: 27 · batch 4: 3
- `bedincbráh` notes corrected to reference *bedina* (verb stem).

## Still pending

### A. *to-be* 2pl form — and formal "you"

`hóbds` (2pl of *hóm*, dual *es hóbds* / plural *ia hóbds*) is in.

Two follow-ups:
1. *to be* — what's *"you two are"* and *"you all are"*? My guess: *es seids* / *ia seids* (same root, *-s* ending pattern). Confirm.
2. Bavarian formal/polite *"you"* (German *Sie*) — does Bavarian distinguish, or just use 3pl forms?

### B. Article paradigm — please correct

You asked for the whole picture. Below is what I'd expect for Bavarian articles. Cells with ⚠️ are uncertain; cells already in the DB are marked ✓.

#### Definite article — *the*

| Case | Masc sg | Fem sg | Neut sg | Plural |
| --- | --- | --- | --- | --- |
| **Nominative** | `da` ✓ | `d'` ✓ | `s'` ✓ | `de` ✓ (or `d'` ✓ contracted) |
| **Accusative** | ⚠️ `an` / `'n`? | ⚠️ `d'` (same as nom)? | ⚠️ `s'` (same as nom)? | ⚠️ `de` (same as nom)? |
| **Dative** | `am` / `'m` ✓ (via *am, aus'm, foa'm*) — bare form `dem` ✓ | ⚠️ `da`? `dera`? | `dem` ✓ | ⚠️ `de`? `dene`? |
| **Genitive** | ⚠️ uses *fo* + dat? bare form? | `dera` ✓ | ⚠️ uses *fo* + dat? | ⚠️ `dera`? |

#### Indefinite article — *a / an*

| Case | Masc sg | Fem sg | Neut sg | (no pl) |
| --- | --- | --- | --- | --- |
| **Nominative** | `a` ✓ | `a` ✓ / `oana` ✓ | `a` ✓ | — |
| **Accusative** | ⚠️ `an` / `'n`? | ⚠️ `a`? `oana`? | ⚠️ `a`? | — |
| **Dative** | ⚠️ `am` / `'m`? | ⚠️ `oana`? `ana`? | ⚠️ `am`? | — |
| **Genitive** | ⚠️ usually rephrased with *fo*? | ⚠️ same? | ⚠️ same? | — |

#### Negation — *no / none* (kein paradigm)

| Case | Masc sg | Fem sg | Neut sg | Plural |
| --- | --- | --- | --- | --- |
| **Nominative** | `koa` ✓ | `koa` ✓ | `koa` ✓ | `koane` ✓ |
| **Accusative** | ⚠️ `koan`? | ⚠️ `koa`? | ⚠️ `koa`? | ⚠️ `koane`? |
| **Dative** | ⚠️ `koam`? | ⚠️ `koana`? | ⚠️ `koam`? | ⚠️ `koane`? `koanen`? |
| **Genitive** | ⚠️ ? | ⚠️ `koana`? | ⚠️ ? | ⚠️ ? |

#### Numeral *"one"*

| Form | Use | English | In DB? |
| --- | --- | --- | --- |
| `oans` | cardinal (the number 1) | one | ✓ (as pronoun, sense "someone") |
| `oa` | masc/neut counting | one | ⚠️ — does this form exist standalone? |
| `oana` | feminine counting | one | ✓ (as determiner, sense "a (f)") |

#### Common preposition + article contractions

Already in DB: `aus'm` (from the), `foa'm` (before the), `dsum` (to the).

Likely missing (please confirm I should add):

| Contraction | = preposition + article | English |
| --- | --- | --- |
| `af'm` | af + dem | on the (m/n dat) |
| `in'm` | in + dem | in the (m/n dat) |
| `fia'n` | fia + an | for the (m acc) |
| `mid'm` | mid + dem | with the (m/n dat) |
| `fom` | fo + dem | of the / from the |
| `in'a` | in + a | in a (indef m/n) |
| `af'a` | af + a | on a (indef m/n) |

---

When you mark up the table (fill the ⚠️ cells, fix anything wrong, strike rows that don't make sense in the standard), I'll insert the missing forms as `Word` rows with `pos = determiner`, gender/case/plurality set per the cell, and link each to the appropriate English equivalent.
