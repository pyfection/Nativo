# Bavarian vocabulary — UI extraction

## Done (130 entries inserted)

5 from batch 1 + 5 from batch 2 + 120 in the bulk pass. All Bavarian words have a matching English Word entry and a translation link.

## Still pending — need your input

These items have something I couldn't decide alone. Once you confirm, I'll insert and remove from this doc. Same workflow as before.

### A. Infinitive uncertain

I'd inferred each Bavarian infinitive from an attested non-infinitive form. Need confirmation.

| Attested form | What I see it as | Inferred infinitive | Notes |
| --- | --- | --- | --- |
| *dadsuaduad* | 3rd sg present (UI: *vo oans dadsuaduad*) | **dadsuaduan**? | one of several "to add" verbs (alongside *datsuafign*, *dadsuagém* already inserted) |
| *klasifidsiad* | 3rd sg present (UI: *UNESCO klasifidsiad …*) | **klasifidsian**? | "to classify" |
| *midgmáhd* | past participle (UI: *de midgmáhd …*) | **midmáhn**? | "to participate / join in" |

### B. The verb "to be" + present forms

`sai` (imperative), `is` (3rd sg "is"), `san` (3rd pl "are") all appear in the UI as separate forms. Per your "separate rows for inflections" decision, I'd insert each as its own `Word`, but I need the **infinitive** to set as the canonical lemma:

- Bavarian "to be" infinitive — **sai**? **sain**? Something else? Please confirm and I'll create the lemma + the three inflected entries linked back to it.

### C. The verb "to have" / "to give" — infinitive uncertain

| Attested form | What I see it as | Inferred infinitive | Notes |
| --- | --- | --- | --- |
| *gibt* | 3rd sg (UI: *Mia nemas af befoas' nima gibt*) | **gem**? **gebm**? | "to give / there is" |
| *hóm* | 1st/3rd pl (UI: *…hóm tsua dera cbráh*) | **hóm**? **hobm**? | "to have" |

### D. Nouns with one form attested

| Attested | Need | Notes |
| --- | --- | --- |
| *bitn* | singular form | English "request"; UI: *Ds'fui bitn* uses plural |

### E. Compound parts to add (per your "also add compound parts" decision)

These are the second elements of compound nouns I've already inserted. Each needs a standalone entry — please confirm English gloss + gender:

| Bavarian | Comes from | Proposed English | Proposed gender | Confirm? |
| --- | --- | --- | --- | --- |
| **muada** | *muadacbráhla* (native speaker) | mother | feminine | |
| **cbráhla** | *muadacbráhla* (native speaker) | speaker | masculine | also: gender-neutral by convention? |
| **dsui** | *dsuicbráh* (target language) | target / goal | neuter | |
| **bedin** | *bedincbráh* (interface language) | use / operation / interface | feminine | |
| **blóds** | *adminblóds* (admin panel) | space / place / panel | masculine | |
| **kean** | *keanveata* (core words) | core | masculine | also adjective sense "core"? |

### F. Missed in the bulk pass — need to add

| Bavarian | English | Notes |
| --- | --- | --- |
| **muadacbráhla** | native speaker | compound *muada* + *cbráhla*. Was on my list but not inserted in the bulk pass — my error. Will go in once compound parts are confirmed. |

### G. Quick checks

1. **oans / oana** were inserted as a pronoun and a determiner respectively. They're also numerals ("one"). Skip the duplicate numeral entries, or insert *oans* / *oana* a second time with `pos = numeral`?
2. **dea** — relative pronoun "who/that" alternate to *vo*. Not in the current `bar/common.json`. **Drop** unless you want it.
