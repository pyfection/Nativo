# Bavarian vocabulary — UI extraction

## Done (157 entries inserted)

- batch 1: 5
- batch 2: 5
- bulk pass: 120
- batch 3 (corrections + compound parts + conjugations + pronouns + new lemmas): 27

That covers everything from the UI plus all the compound parts and conjugations you've described so far.

## Still pending

### A. "You all" (2pl) — am I missing anything?

You asked. Yes — both paradigms are missing the 2pl ("you all"):

**to have** — what's *"you all have"*?

**to be** — what's *"you all are"*?

Bavarian sources I've seen use forms like *es habts* / *eß habts* / *ihr habts* depending on region. Once you give me the standard form, I'll insert as the 2pl form of *hóm* and *sai*.

(For the formal/polite *"you"* — capital *Sie* in German — let me know if Bavarian distinguishes that or just uses the 3pl forms.)

### B. Clarification you asked for

> 1. oans / oana — I don't understand the question.

Re-asked: *oans* is in the DB now as a **pronoun** (sense: "one, someone"). The same word also functions as the **numeral** "one" (the number 1). The DB has one `Word` row per lemma+POS, so right now only the pronoun sense is searchable.

**Question**: should we also create a second `Word` row for *oans* with `pos = numeral`, so that a future search for "the number one" finds it? Or skip — one row is enough for now and the numeral sense is implicit?

Same question for *oana* (currently a determiner; also "a (one) feminine").

## Side note — followup item

You corrected *bedin* → it's the stem of the verb *bedina* "to control", not a noun. I inserted *bedina* as a verb (done) but the **existing `bedincbráh` entry's notes** still say `"compound bedin+cbráh"`. I'd like to update them to say `"compound: verb stem of bedina + cbráh"`. Want me to PATCH that record? (Same kind of fix may be useful on a few other compounds as we learn more.)
