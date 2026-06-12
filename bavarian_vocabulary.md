# Bavarian vocabulary — UI extraction

Every distinct lexical item from `frontend/src/locales/bar/common.json` that should be added as a `Word` entry in the database, grouped by part of speech. One section per **lemma** (sg form for nouns, infinitive for verbs, base form for adjectives). Inflected forms attested in the UI are noted under each entry.

Each entry follows the `Word` model fields. Leave `⚠️ ?` markers for anything that needs review. All entries default to `language_id = Bavarian` and `created_by_id = admin`. Once approved we'll bulk-insert with `status = published`.

**Attribute legend:**
- `pos` — part_of_speech enum
- `gender` / `plurality` — only relevant for nouns
- `register` — defaults to *neutral*
- `usage` — the actual sentence from the UI where the word appears (shows context)
- `forms` — other attested inflections in the UI
- `notes` — anything that needs clarification

---

## 1. Nouns

### voat
- **definition:** word
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular
- **forms:** plural *veata*
- **register:** neutral
- **usage:** *A {{source}} voat ocaugn*
- **notes:**

### veata
- **definition:** words
- **pos:** noun
- **plurality:** plural of *voat*
- **register:** neutral
- **usage:** *Suah in de {{source}} veata*
- **notes:** include as separate entry if plurals are first-class in the DB; otherwise fold into *voat*.

### veatabuah
- **definition:** dictionary
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *De midheifa baun no an dem veatabuah*
- **notes:** compound — *veata* + *buah*.

### veataguad
- **definition:** vocabulary
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Veataguad afbaun*
- **notes:** compound — *veata* + *guad*.

### voatsámlung
- **definition:** word collection / vocabulary set
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **forms:** plural *voatsámlunga*
- **register:** neutral
- **usage:** *…vortsámlunga und tonafnáma…* (plural)
- **notes:** compound — *voat* + *sámlung*.

### dokument
- **definition:** document
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular (also used as plural in UI)
- **register:** neutral
- **usage:** *Gcrimne dokument in bedrotn cbráha festhóitn und eahóitn*
- **notes:** loanword.

### afnáma
- **definition:** recording
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular (and same form for plural)
- **register:** neutral
- **usage:** *Ehde afnáma fo muadacbráhla cbaihan*
- **notes:** also forms compound *tonafnáma*.

### tonafnáma
- **definition:** audio recording
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular (same form for plural)
- **register:** neutral
- **usage:** *Tonafnáma houhlón kumt bóid*
- **notes:** compound — *ton* + *afnáma*.

### ton
- **definition:** sound / audio
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Ton afnema*
- **notes:**

### ivasetsung
- **definition:** translation
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **forms:** plural *ivasetsunga*
- **register:** neutral
- **usage:** *Sig d'ivasetsung af {{target}}*
- **notes:**

### ascbráh
- **definition:** pronunciation
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **forms:** plural *ascbráha*
- **register:** neutral
- **usage:** *…mid ivasetsunga und ascbráha…*
- **notes:**

### cbráh
- **definition:** language
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **forms:** plural *cbráha*
- **register:** neutral
- **usage:** *De dsuicbráh endad ma om réhds*
- **notes:** canonical core noun; the platform is built around it.

### dsuicbráh
- **definition:** target language
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *De dsuicbráh endad ma om réhds*
- **notes:** compound — *dsui* + *cbráh*.

### bedincbráh
- **definition:** interface language
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Bedincbráh*
- **notes:** compound — *bedin* + *cbráh*.

### veit
- **definition:** world
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *…af da veit…*
- **notes:**

### eab
- **definition:** heritage
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Cbráhlihs eab dahóitn*
- **notes:**

### afdróg
- **definition:** task / mission
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Unsa afdróg*
- **notes:**

### midheifa
- **definition:** contributor / helper
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely; can refer to any gender by convention)
- **plurality:** singular (same form for plural)
- **register:** neutral
- **usage:** *De midheifa baun no an dem veatabuah*
- **notes:** also functions as the page name (Contributors).

### muadacbráhla
- **definition:** native speaker
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular (also used as plural)
- **register:** neutral
- **usage:** *Ehde afnáma fo muadacbráhla cbaihan*
- **notes:** compound — *muada* + *cbráhla*.

### ascdeam
- **definition:** extinction
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Cbráha foa'm ascdeam rétn*
- **notes:**

### visn
- **definition:** knowledge
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Visn tailn*
- **notes:**

### minutn
- **definition:** minute
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** plural (also used as singular)
- **register:** neutral
- **usage:** *…in oana minutn numoi*
- **notes:**

### iór
- **definition:** year(s)
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** plural (same form for singular)
- **register:** neutral
- **usage:** *…is fia iva dausnd iór gret voan*
- **notes:**

### foatcrit
- **definition:** progress
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *{{language}} foatcrit*
- **notes:**

### ivasiht
- **definition:** overview
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Blátfoam ivasiht*
- **notes:**

### blátfoam
- **definition:** platform
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *A digitale blátfoam fia's festhóitn und eahóitn…*
- **notes:** technical loan.

### meni
- **definition:** menu
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Profil meni fia {{username}}*
- **notes:** technical loan.

### profil
- **definition:** profile
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Profil meni fia {{username}}*
- **notes:** technical loan.

### nutsa
- **definition:** user
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular (same form for plural)
- **register:** neutral
- **usage:** *Nutsa*
- **notes:**

### kentnis
- **definition:** proficiency / knowledge
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *Kentnis*
- **notes:**

### tréfa
- **definition:** hit / match
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular (same form for plural)
- **register:** neutral
- **usage:** *Koa tréfa fia "{{query}}"*
- **notes:**

### duan
- **definition:** activity / doing
- **pos:** noun
- **gender:** ⚠️ ? (neuter likely)
- **plurality:** singular (used collectively)
- **register:** neutral
- **usage:** *Letsde duan in {{language}}*
- **notes:** also serves as the verb stem "to do".

### bitn
- **definition:** request
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** plural (singular *bit* ⚠️ unverified)
- **register:** neutral
- **usage:** *Ds'fui bitn*
- **notes:**

### adminblóds
- **definition:** admin panel
- **pos:** noun
- **gender:** ⚠️ ? (masculine likely)
- **plurality:** singular
- **register:** technical
- **usage:** *Adminblóds*
- **notes:** compound — *admin* + *blóds*.

### keanveata
- **definition:** core word(s)
- **pos:** noun
- **plurality:** plural (singular *keanvoat* ⚠️ unverified)
- **register:** neutral
- **usage:** *{{count}} fo gcétsd {{target}} keanveata co dokumentiad*
- **notes:** compound — *kean* + *veata*.

### generaradsiona
- **definition:** generation
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** plural
- **register:** neutral
- **usage:** *…fia kemade generaradsiona…*
- **notes:** technical loan.

### suah
- **definition:** search
- **pos:** noun
- **gender:** ⚠️ ? (feminine likely)
- **plurality:** singular
- **register:** neutral
- **usage:** *D'suah is feigclógn*
- **notes:** identical form as imperative of *suaha*.

---

## 2. Verbs (infinitives)

### festhóitn
- **definition:** to hold fast, to record, to preserve
- **pos:** verb
- **register:** neutral
- **usage:** *Veataguad, tekst und tonafnáma fia {{language}} festhóitn*
- **forms:** noun-style use *Festhóitn* (mission card heading)
- **notes:**

### eahóitn
- **definition:** to maintain, to preserve
- **pos:** verb
- **register:** neutral
- **usage:** *…festhóitn und eahóitn…*
- **notes:** synonym of *dahóitn* but with a different prefix.

### dahóitn
- **definition:** to preserve, to keep
- **pos:** verb
- **register:** neutral
- **usage:** *Cbráhlihs eab dahóitn*
- **forms:** participle/adjective *dahóitne* (preserved)
- **notes:**

### rétn
- **definition:** to save, to rescue
- **pos:** verb
- **register:** neutral
- **usage:** *Cbráha foa'm ascdeam rétn*
- **notes:**

### ocaugn
- **definition:** to look up (in a reference)
- **pos:** verb
- **register:** neutral
- **usage:** *A {{source}} voat ocaugn*
- **notes:**

### ségn
- **definition:** to see, to view
- **pos:** verb
- **register:** neutral
- **usage:** *Veata ségn*
- **forms:** imperative *sig* (also forms phrase *sig om* = "see above")
- **notes:**

### sig
- **definition:** see (imperative)
- **pos:** verb (imperative form of *ségn*)
- **register:** neutral
- **usage:** *…sig d'ivasetsung af {{target}}…*
- **notes:** include as a separate entry if imperative forms are first-class; otherwise note under *ségn*.

### nema
- **definition:** to take
- **pos:** verb
- **register:** neutral
- **usage:** *Mia nemas af befoas' nima gibt* (with prefix)
- **notes:** base verb; combines with prefixes (*af-* → *afnema*).

### afnema
- **definition:** to record (audio); to take down
- **pos:** verb
- **register:** neutral
- **usage:** *Ton afnema*
- **notes:** compound — *af-* + *nema*.

### baidrógn
- **definition:** to contribute
- **pos:** verb
- **register:** neutral
- **usage:** *Baidrógn*
- **forms:** participle *baidrógt*
- **notes:** also realised as separable construction *Dróg ... bai* (e.g. *Dróg dsu {{language}} bai*).

### datsuafign
- **definition:** to add
- **pos:** verb
- **register:** neutral
- **usage:** *S'easte voat datsuafign*
- **notes:** more formal; alternates with *dadsuagém* and *dadsuaduan*.

### dadsuagém
- **definition:** to give, to add
- **pos:** verb
- **register:** neutral
- **usage:** *…ven's midheifa dadsuagém*
- **notes:**

### dadsuaduan
- **definition:** to add
- **pos:** verb
- **register:** neutral
- **usage:** *…vo oans dadsuaduad* (3rd sg form)
- **notes:** ⚠️ infinitive form inferred — please confirm.

### ivasetsn
- **definition:** to translate
- **pos:** verb
- **register:** neutral
- **usage:** *A voat ivasetsn*
- **notes:**

### houhlón
- **definition:** to upload
- **pos:** verb
- **register:** neutral
- **usage:** *Tonafnáma houhlón*
- **notes:**

### afbaun
- **definition:** to build up, to establish
- **pos:** verb
- **register:** neutral
- **usage:** *Veataguad afbaun*
- **notes:**

### cbaihan
- **definition:** to store, to save (data)
- **pos:** verb
- **register:** neutral
- **usage:** *Ehde afnáma fo muadacbráhla cbaihan*
- **notes:**

### tailn
- **definition:** to share
- **pos:** verb
- **register:** neutral
- **usage:** *Visn tailn*
- **notes:**

### omein
- **definition:** to sign in, to log in
- **pos:** verb
- **register:** neutral
- **usage:** *Omein*
- **notes:**

### óbmein
- **definition:** to sign out, to log out
- **pos:** verb
- **register:** neutral
- **usage:** *Óbmein*
- **notes:**

### registrian
- **definition:** to register, to sign up
- **pos:** verb
- **register:** neutral
- **usage:** *Registrian*
- **forms:** imperative *Registria* (in *Registria di um baidsumdrogn*)
- **notes:**

### klasifidsian
- **definition:** to classify
- **pos:** verb
- **register:** technical
- **usage:** *UNESCO klasifidsiad {{language}} óis {{level}}* (3rd sg form)
- **notes:** ⚠️ infinitive form inferred — please confirm.

### suaha
- **definition:** to search
- **pos:** verb
- **register:** neutral
- **usage:** *Suaha*
- **forms:** imperative *suah*; present *suaht*
- **notes:** also realised as the noun *suah*.

### dsoagn
- **definition:** to show
- **pos:** verb
- **register:** neutral
- **usage:** *Afnáma dsoagn si dó…*
- **notes:** in the UI used reflexively as *dsoagn si* = "show themselves / appear".

### eigém
- **definition:** to enter, to input
- **pos:** verb
- **register:** neutral
- **usage:** *A {{source}} voat eigém…*
- **notes:**

### dróg
- **definition:** to carry, to bring
- **pos:** verb
- **register:** neutral
- **usage:** *Dróg dsu {{language}} bai*
- **notes:** combines with *bai* as separable particle to form *baidrógn* ("contribute").

### gibt
- **definition:** there is, exists (3rd sg present of *gem* "to give")
- **pos:** verb
- **register:** neutral
- **usage:** *Mia nemas af befoas' nima gibt*
- **notes:** ⚠️ infinitive likely *gem* / *geben* — confirm. May want to add the lemma instead.

### hóm
- **definition:** to have (1st/3rd pl present)
- **pos:** verb
- **register:** neutral
- **usage:** *Ole, de midgmáhd oda baidrógn hóm tsua dera cbráh*
- **notes:** ⚠️ infinitive likely *hóm* same form or *hobm* — confirm.

### midmáhn
- **definition:** to join in, to participate
- **pos:** verb
- **register:** neutral
- **usage:** *…de midgmáhd…* (past participle)
- **notes:** ⚠️ infinitive inferred from past participle *midgmáhd* — confirm.

### fasuaha
- **definition:** to try
- **pos:** verb
- **register:** neutral
- **usage:** *Bice numoi fasuaha*
- **forms:** imperative *fasuah's* ("try it")
- **notes:**

### baun
- **definition:** to build (1st/3rd pl present)
- **pos:** verb
- **register:** neutral
- **usage:** *De midheifa baun no an dem veatabuah*
- **notes:** ⚠️ infinitive *baun* same form likely; confirm.

### lón
- **definition:** to load
- **pos:** verb
- **register:** neutral
- **usage:** *Midheifa lón…*
- **forms:** present *lót*
- **notes:**

### umcaugn
- **definition:** to browse, to look around
- **pos:** verb
- **register:** neutral
- **usage:** *Dsruk dsum umcaugn*
- **notes:**

---

## 3. Adjectives & participles

### digitale
- **definition:** digital
- **pos:** adjective
- **register:** neutral
- **usage:** *A digitale blátfoam…*
- **notes:** technical loan.

### bedrotn
- **definition:** endangered, threatened
- **pos:** adjective
- **register:** neutral
- **usage:** *…fo de bedrotn cbráha af da veit…*
- **notes:**

### gcrimne
- **definition:** written
- **pos:** adjective (past participle)
- **register:** neutral
- **usage:** *Gcrimne dokument in bedrotn cbráha…*
- **notes:**

### dahóitne
- **definition:** preserved
- **pos:** adjective (past participle of *dahóitn*)
- **register:** neutral
- **usage:** *Dahóitne cbráha*
- **notes:**

### dokumentiade
- **definition:** documented
- **pos:** adjective (past participle)
- **register:** neutral
- **usage:** *Dokumentiade veata*
- **notes:**

### umfángraihe
- **definition:** comprehensive, extensive
- **pos:** adjective
- **register:** neutral
- **usage:** *Umfángraihe voatsámlung…*
- **notes:**

### ehde
- **definition:** real, authentic
- **pos:** adjective
- **register:** neutral
- **usage:** *Ehde afnáma fo muadacbráhla cbaihan*
- **notes:**

### letsde
- **definition:** latest, last
- **pos:** adjective
- **register:** neutral
- **usage:** *Letsde duan in {{language}}*
- **notes:**

### easte
- **definition:** first
- **pos:** adjective
- **register:** neutral
- **usage:** *S'easte voat datsuafign*
- **notes:**

### cbráhlihs
- **definition:** linguistic, relating to language
- **pos:** adjective
- **register:** neutral
- **usage:** *Cbráhlihs eab dahóitn*
- **notes:**

### kemade
- **definition:** coming, future
- **pos:** adjective (present participle)
- **register:** neutral
- **usage:** *…fia kemade generaradsiona…*
- **notes:**

### gcétsd
- **definition:** estimated
- **pos:** adjective (past participle)
- **register:** neutral
- **usage:** *{{count}} fo gcétsd {{target}} keanveata co dokumentiad*
- **notes:**

### fabundn
- **definition:** linked, connected
- **pos:** adjective (past participle)
- **register:** neutral
- **usage:** *Afnáma, de mid veata in dera cbráh fabundn san*
- **forms:** declined *fabundne* (e.g. *fabundne veata*)
- **notes:**

### feigclógn
- **definition:** failed
- **pos:** adjective (past participle)
- **register:** neutral
- **usage:** *D'suah is feigclógn*
- **notes:**

### midgmáhd
- **definition:** participated, joined in
- **pos:** adjective (past participle of *midmáhn*)
- **register:** neutral
- **usage:** *…de midgmáhd oda baidrógn hóm tsua dera cbráh*
- **notes:**

---

## 4. Adverbs

### bóid
- **definition:** soon
- **pos:** adverb
- **register:** neutral
- **usage:** *Tonafnáma houhlón kumt bóid*

### numoi
- **definition:** again
- **pos:** adverb
- **register:** neutral
- **usage:** *Ds'fui bitn - bitce ruiga, fasuah's in oana minutn numoi*

### nima
- **definition:** no longer, not anymore
- **pos:** adverb
- **register:** neutral
- **usage:** *Mia nemas af befoas' nima gibt*

### no
- **definition:** still, yet
- **pos:** adverb
- **register:** neutral
- **usage:** *De midheifa baun no an dem veatabuah*

### ruiga
- **definition:** more slowly, more calmly
- **pos:** adverb (comparative)
- **register:** neutral
- **usage:** *…bitce ruiga…*

### co
- **definition:** already
- **pos:** adverb
- **register:** neutral
- **usage:** *…keanveata co dokumentiad*

### dó
- **definition:** there, here
- **pos:** adverb
- **register:** neutral
- **usage:** *Koa ivasetsung dó*

### óis
- **definition:** as, in the role of
- **pos:** adverb / conjunction
- **register:** neutral
- **usage:** *UNESCO klasifidsiad {{language}} óis {{level}}*

### om
- **definition:** above, at the top
- **pos:** adverb
- **register:** neutral
- **usage:** *…endad ma om réhds* (and in the phrase *sig om* "see above")
- **notes:** also functions as preposition *on the / at the*.

### réhds
- **definition:** right (direction)
- **pos:** adverb
- **register:** neutral
- **usage:** *…om réhds*

---

## 5. Pronouns & determiners

### mia
- **definition:** we
- **pos:** pronoun
- **register:** neutral
- **usage:** *Mia nemas af…*

### ma
- **definition:** one (impersonal "you")
- **pos:** pronoun
- **register:** neutral
- **usage:** *…endad ma om réhds*

### di
- **definition:** you (accusative reflexive)
- **pos:** pronoun
- **register:** neutral
- **usage:** *Registria di um baidsumdrogn*

### si
- **definition:** themselves, oneself (reflexive)
- **pos:** pronoun
- **register:** neutral
- **usage:** *Afnáma dsoagn si dó*

### ole
- **definition:** all, everyone
- **pos:** pronoun / determiner
- **register:** neutral
- **usage:** *Ole, de midgmáhd…*

### oans
- **definition:** one (indefinite, "someone, something")
- **pos:** pronoun
- **register:** neutral
- **usage:** *…vo oans dadsuaduad*

### oana
- **definition:** a, one (feminine indefinite article)
- **pos:** determiner
- **register:** neutral
- **usage:** *…in oana minutn numoi*

### a
- **definition:** a, one (indefinite article)
- **pos:** determiner
- **register:** neutral
- **usage:** *A voat in {{source}} ocaugn*

### koa
- **definition:** none, no (singular)
- **pos:** determiner
- **register:** neutral
- **usage:** *Koa ivasetsung dó*

### koane
- **definition:** none, no (plural)
- **pos:** determiner
- **register:** neutral
- **usage:** *No koane veata dó*

### niks
- **definition:** nothing
- **pos:** pronoun
- **register:** neutral
- **usage:** *No niks dó*

### vo
- **definition:** who, that (relative pronoun)
- **pos:** pronoun
- **register:** neutral
- **usage:** *…sai da easte, vo oans dadsuaduad*
- **notes:** distinct in meaning from preposition *fo* despite similar spelling.

### dea
- **definition:** who, the one who
- **pos:** pronoun (relative / demonstrative)
- **register:** neutral
- **usage:** ⚠️ — not currently in `bar/common.json`; was in an earlier draft. Drop unless you want it added.

### da
- **definition:** the (masc sg)
- **pos:** determiner
- **register:** neutral
- **usage:** *Sai da easte*

### de
- **definition:** the (plural)
- **pos:** determiner
- **register:** neutral
- **usage:** *De midheifa baun…*

### dera
- **definition:** of the (gen sg fem)
- **pos:** determiner
- **register:** neutral
- **usage:** *…in dera cbráh fabundn san*
- **notes:** consider whether grammatical inflections should be stored as separate lexical entries.

### dem
- **definition:** the (dat sg masc/neut)
- **pos:** determiner
- **register:** neutral
- **usage:** *…an dem veatabuah*
- **notes:** same caveat as *dera*.

### s'
- **definition:** the (sg neuter, contracted before vowel)
- **pos:** determiner
- **register:** neutral
- **usage:** *S'easte voat datsuafign*

### d'
- **definition:** the (contracted before vowel)
- **pos:** determiner
- **register:** neutral
- **usage:** *D'suah is feigclógn*; *…sig d'ivasetsung…*

---

## 6. Prepositions

### foa
- **definition:** before
- **pos:** preposition
- **register:** neutral
- **usage:** *Cbráha foa'm ascdeam rétn*
- **forms:** contracted *foa'm* (= *foa* + *em*)

### af
- **definition:** on, at
- **pos:** preposition
- **register:** neutral
- **usage:** *…af da veit*

### in
- **definition:** in
- **pos:** preposition
- **register:** neutral
- **usage:** *In de Stadt* (UI: *in dera cbráh*)

### bai
- **definition:** at, with (separable verb particle when paired with *dróg* → *baidrógn*)
- **pos:** preposition / particle
- **register:** neutral
- **usage:** *Dróg dsu {{language}} bai*

### mid
- **definition:** with
- **pos:** preposition
- **register:** neutral
- **usage:** *…mid ivasetsunga und ascbráha…*

### fo
- **definition:** of, from
- **pos:** preposition
- **register:** neutral
- **usage:** *Midheifa fo {{language}}*

### fia
- **definition:** for
- **pos:** preposition
- **register:** neutral
- **usage:** *Koa tréfa fia "{{query}}"*

### duah
- **definition:** through, via
- **pos:** preposition
- **register:** neutral
- **usage:** *…duah grimne dokument…*

### iva
- **definition:** over, above, more than
- **pos:** preposition
- **register:** neutral
- **usage:** *…fia iva dausnd iór…*

### dsu
- **definition:** to, toward
- **pos:** preposition
- **register:** neutral
- **usage:** *Dróg dsu {{language}} bai*

### tsua
- **definition:** to, toward (long form)
- **pos:** preposition
- **register:** neutral
- **usage:** *…hóm tsua dera cbráh*

### dsum
- **definition:** to the (contracted *dsu* + *m*)
- **pos:** preposition
- **register:** neutral
- **usage:** *Dsruk dsum umcaugn*

### um
- **definition:** around, in order to
- **pos:** preposition / conjunction
- **register:** neutral
- **usage:** *Registria di um baidsumdrogn*

### af'm / am
- **definition:** on the (contracted *af* + *em*)
- **pos:** preposition
- **register:** neutral
- **usage:** ⚠️ not currently in `bar/common.json`. Skip unless you want to add.

### aus'm
- **definition:** from the (contracted *aus* + *em*)
- **pos:** preposition
- **register:** neutral
- **usage:** *A voat aus'm {{language}}*

---

## 7. Conjunctions / particles / discourse

### und
- **definition:** and
- **pos:** conjunction
- **register:** neutral
- **usage:** *…festhóitn und eahóitn…*

### oda
- **definition:** or
- **pos:** conjunction
- **register:** neutral
- **usage:** *…oda baidrógn hóm…*

### ven
- **definition:** when, if
- **pos:** conjunction
- **register:** neutral
- **usage:** *…ven's midheifa dadsuagém*

### bitce
- **definition:** please
- **pos:** particle / interjection
- **register:** neutral
- **usage:** *…bitce ruiga…*
- **forms:** sentence-initial form *Bice* (drops the *t*)

### sai
- **definition:** be (imperative singular)
- **pos:** verb (imperative)
- **register:** neutral
- **usage:** *…sai da easte…*

### is
- **definition:** is (3rd sg present)
- **pos:** verb
- **register:** neutral
- **usage:** *D'suah is feigclógn*
- **notes:** ⚠️ store as inflection of *sai* or as standalone — your call.

### san
- **definition:** are (3rd pl present)
- **pos:** verb
- **register:** neutral
- **usage:** *…fabundn san*
- **notes:** same caveat as *is*.

---

## 8. Numerals

### oans
- **definition:** one
- **pos:** numeral
- **register:** neutral
- **usage:** *vo oans dadsuaduad*

### oana
- **definition:** a / one (feminine)
- **pos:** numeral / article
- **register:** neutral
- **usage:** *in oana minutn*

### dausnd
- **definition:** thousand
- **pos:** numeral
- **register:** neutral
- **usage:** *…fia iva dausnd iór…*

---

## Open questions

A few items I'd like your call on before inserting:

1. **Inflected forms as separate entries?** Past participles (*dahóitne*, *fabundn*, *midgmáhd*), imperative forms (*sig*, *Registria*), 3rd-person forms (*dadsuaduad*, *klasifidsiad*) — keep each as its own `Word` row, or only store lemmas and note the inflections in the lemma's `usage_examples` / `context_notes` field? The DB has fields for gender / plurality / case / verb_aspect but not a generic "inflectional form of X" linkage.
2. **Compound nouns as single entries?** *veatabuah*, *veataguad*, *muadacbráhla*, *dsuicbráh*, *bedincbráh*, *adminblóds*, *keanveata*, *voatsámlung* — keep as single entries, or also add their parts (*kean*, *muada*, *blóds*) where attested?
3. **Determiners as content words?** *dera*, *dem*, *s'*, *d'* — these are inflected articles. Worth their own rows, or fold into the *a/da/de* base entries?
4. **English translation linkage.** When inserting, should each Bavarian word also create / link an English `Word` entry (so the dictionary search works bidirectionally), or do you want me to skip linkage for now and you'll wire it later?

Once you've gone through the doc (mark up changes inline), I'll generate the insert script.
