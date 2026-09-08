# Pedagogy rationale

Every pedagogical choice in the UI must be traceable to this file. Phase 1 has
no UI, so this file records only the decisions the engine itself embodies.

## The derivation trace is shown to the learner

The engine returns a step by step derivation alongside every surface form, and
the CLI prints it. This is deliberate. Teaching the rule and letting the learner
apply it is the difference between this project and a flashcard app; showing the
rule fire is the cheapest way to do that.

Grounding: rule application is the thing being learned, per the project brief's
framing of Turkish morphophonology as the load-bearing feature. Fuller grounding
in the SLA literature belongs here once docs/bibliography.md is real.

## Suffixes are stored as archiphonemes, never as allomorphs

A learner who is taught that the accusative is "-(y)I" and that harmony resolves
it has learned one thing. A learner taught -i, -ı, -u and -ü has learned four
things and no rule. The content format enforces the first.

## The start screen explains the method before the first exercise

A learner's first exercise was, until now, also their first contact with the
app: no screen ever said that recognition comes before production, that
exercises interleave topics on purpose, or that spaced review is why a
mastered item resurfaces later instead of disappearing. Without that, a
learner has no way to tell "this feels harder than it should" from "the app
is working as designed," and the first concept's intro text ("the rule you
just saw") presupposes a first exercise the learner has, in fact, just had:
the method needs to be named before the content demonstrates it, not left for
the learner to infer.

Grounding: input before output (vanpatten-input-processing), interleaving over
blocking (interleaving-over-blocking), and spaced retrieval over massed review
(cepeda-distributed-practice, roediger-karpicke-retrieval) are exactly the
mechanics the tutor already implements. This entry states them in the UI
copy; it introduces no new pedagogy.

## Vocabulary recognition is a narrow, deliberate exception, not a reversal

The derivation-trace entry above says teaching the rule and letting the
learner apply it is "the difference between this project and a flashcard
app." vocab_recognition looks like the thing that line is contrasting
against: a word, a set of possible meanings, pick one. It earns an exception
rather than breaking that claim for three reasons. First, scope: it is one
concept in one unit, not the shape of the whole curriculum, and every other
concept still teaches a rule via generated forms. Second, mechanism: this is
retrieval (choosing the right meaning yourself, from
roediger-karpicke-retrieval, already cited for spaced review) rather than
restudy, so it is not a static list to memorise, it is a question. Third,
and the actual reason it exists at all: coverage. Vocabulary only otherwise
enters a learner's path as a side effect of whichever suffix is current, so
a word never carrying a suffix that unit is currently drilling has no
dedicated path to being learned at all, however common it is. That gap, not
a desire for flashcards, is what this concept closes.

What keeps it from sliding into "a screen that is only a table" (the
long-focus-on-form citation's actual target, which is grammar taught apart
from meaning): the lexicon it draws from is the same reviewed lexicon every
other exercise already trusts, not a separate word list, and the task is
meaning-primary by construction, connecting a form to its meaning is the
whole content, not incidental to a grammar point. This unit has no
prerequisites and is open from the start, which is why it is unit 4 in file
order but not gated behind units 1 through 3. The intent is for it to recur
alongside whichever grammar unit is current, the same way vowel harmony
error rate ought to be tracked as a standing metric rather than a
unit-1-only concern, not to be finished once and left behind. tutor.py does
not fully deliver that yet: today it opens immediately but competes for a
turn by unit order, so in practice it surfaces once whichever earlier
concepts are current have hit their per-session block cap, not interleaved
turn by turn from the first exercise. Making a lexical_set concept genuinely
concept-agnostic to unit order is the scheduler change the project's roadmap
notes already call for; this entry should be revisited once that lands.

## The first verbal unit is scoped to what needs no new judgement call

Unit 5 teaches exactly two suffixes, -(y)Iyor and -mA, and only in the
unmarked third person. That is a deliberately narrow slice of "verbal
morphology" for a unit whose rationale claims to start it, and the narrowness
is the point: both facts are uncontested in every reference description of
Turkish (present tense, and how to negate it), neither needs a native
speaker's judgement call the way the disharmonic-loan and syncope questions
elsewhere in this content did, and third person needs no suffix at all,
mirroring PRED3SG's existing precedent instead of inventing a new one.

Grounding: input before output (vanpatten-input-processing, already cited
for the same reason in unit 1) and Pienemann's processability theory
(pienemann-processability), which is the actual reason this comes after the
nominal units rather than before them: a learner has to be able to process
harmony automatically before adding a second word class competing for the
same rule is worth anything.

What this unit deliberately does not attempt yet, and why: person marking on
verbs (öğreniyorum needs suffixes that do not exist in this content yet),
the aorist (its high/low vowel choice is lexically listed per verb in every
source I have seen quoted for it, which means a real per-verb list, not a
rule, and I do not have one I trust), the evidential -mIş (a real,
well-attested distinction, but teaching it well is a bigger unit than
"started"), and stress (this engine does not model it at all, so the
negative-imperative/verbal-noun minimal pair some sources raise for -mA is
mentioned in this unit's intro as a fact worth knowing, not tested, because
testing it would require an ability the app does not have).

## Verb person marking reuses the predicative suffixes rather than inventing new ones

Unit 5's own rationale entry above named this as deliberately unbuilt:
"person marking on verbs (öğreniyorum needs suffixes that do not exist in
this content yet)". They already existed. -(y)Im, -sIn, -(y)Iz and -sInIz
are the same pronominal-type person markers unit 2 teaches for nominal
predication (öğrenciyim), and Turkish reuses exactly these morphemes for
non-past verb agreement, not a separate paradigm. The new
verb-person-marking concept teaches no new suffix ids; it teaches the same
four suffixes attaching after a new fixed prefix (-(y)Iyor) instead of
directly to a noun, which is a new context for an already-taught rule, the
same shape as fourfold-harmony recurring through possessive-suffixes and
stem-alternation. Third singular stays bare, matching PRED3SG's existing
precedent (bare-third-person), and third plural is deliberately left out of
this concept: -lAr is the right morpheme, but its stored gloss is "plural"
(a nominal-count meaning), which would show a misleading option in a
"who is this about" exercise built from suffix glosses. Giving -lAr a
verb-agreement sense needs its own content decision, not a silent gloss
override, so it is left for a later pass rather than guessed at here.

Grounding: the same reuse-over-duplication reasoning already applied when
PL and the PRED suffixes were first identified as the correct morphemes to
reuse rather than re-teach.

## Chaining exposed a real, pre-existing bug in the shipped negation

Building the two-suffix chain generation the concept above needed
(-(y)Iyor then a person suffix) required generators to attach a suffix
after a fixed prefix for the first time. Actually generating a batch with
it, rather than trusting the single-suffix tests already in place, is what
caught this: -mA + -(y)Iyor was already wrong for any verb whose own vowel
is rounded, and had been since negation shipped, because none of the three
verbs test_known_forms.py checked it against (gel, git, yap) happen to
have a rounded stem vowel. The engine gave "okumıyor"; the correct,
well-attested form is "okumuyor".

The cause: -(Ø)Iyor's own vowel resolves its rounding from whatever vowel
precedes it, which is the ordinary and correct rule everywhere else (a low
vowel trigger defaults a following high-vowel suffix to unrounded, e.g.
PL + PRED3SG gives evlerdir, never evlerdür). -mA is always low (a/e) and
so has no rounding of its own to give. But the negative progressive is the
one combination where Turkish reference grammars note the suffix vowel
reaches past -mA to the verb root's own rounding instead of defaulting to
unrounded, which is why gitmiyor is regular only by coincidence (git's own
vowel is already unrounded) while okumuyor is not derivable from the
general rule at all. This is now a targeted exception in engine.py, keyed
specifically to NEG immediately preceding PROG, rather than a change to how
rounding harmony works generally, since the general rule is independently
confirmed correct by the evlerdir-style cases it already handles.

Grounding: this is the third time this session that generating actual
output, rather than reasoning about the rule in isolation, is what surfaced
a bug a rule believed correct for the tested cases (see the recurring bug
shape below).

## Ability is built without touching the blocked aorist

Unit 5's own rationale entry names the aorist as deliberately unbuilt,
because its high/low vowel choice is lexically listed per verb and this
project does not have a wordlist it trusts for that. -(y)Abilir looks like
it needs exactly that: it ends in the aorist's own -Ir. It does not,
because -(y)Abilir's -Ir never attaches to the original verb at all; it
attaches to bil, the frozen root of bilmek that gives the whole
construction its name, and bil is the same fixed syllable regardless of
which verb preceded it. Whatever follows a fixed syllable resolves by
ordinary fourfold harmony against that syllable's own vowel, not by the
lexically listed rule that governs the aorist when it attaches directly to
a verb root, which is why yapabilir and gelebilir both end in -ir despite
yap and gel belonging to different harmony classes, and why this needed no
per-verb data to build correctly.

Modelled as two suffixes, ABIL then ABILTENSE, rather than one combined
"-(y)AbilIr", after generating actual output surfaced a real engine
limitation: harmony_back (the override engine.py already uses so a later
suffix reads harmony off the growing form rather than the original stem,
added for -(y)Iyor plus a person suffix) is fixed once per suffix
application, not per character within one suffix's own body, so a single
suffix spanning both the A before bil and the I after it would have forced
the I to inherit the A's override too, giving okuyabilır instead of
okuyabilir. Splitting into two suffixes means the second one starts with
stem_exposed already false, which is exactly the case that override was
built for.

Deliberately out of scope: saying you cannot do something. Turkish handles
inability with its own suffix, -(y)AmA, not -(y)Abilir with -mA attached
the way -(y)Iyor's negative composes -- a real irregularity (the auxiliary
bil disappears entirely: gelebilirim, gidemem, not gelebilmiyorum), not
this unit's negation, so it is left for a later unit rather than guessed at.

Grounding: input before output (vanpatten-input-processing) and Pienemann's
processability theory (pienemann-processability), the same reasons already
cited for unit 5, for the same reason: person marking is reused rather than
re-taught, so nothing here is acquired before a learner can process it.

## Existence is the first unit built on more than one word

Every generator before unit 7 assumes one lexeme, one inflect() call, one
surface form out. Var and yok cannot be taught that way: Turkish has no verb
"to have", so "I have a car" is literally "my car exists" (arabam var), two
words, only one of which inflects. Rather than bend inflect() itself to
produce more than one word, or fake a phrase by string-concatenating two
generators' outputs by hand in curriculum content, a new module (phrase.py)
composes a short, ordered sequence of parts -- inflected words and fixed
particles -- calling the exact same Language.inflect() every existing
generator already calls for each inflected part. Nothing about engine.py
changed; a phrase is several ordinary single-word results joined, not a new
kind of derivation.

Negation of existence gets its own exercise deliberately: yok is a
different word from var, not var plus a negative a learner already knows,
and değil (the negative copula from unit 2) is never used here either.
Both are real, specific facts worth testing directly, since a learner who
has just learned değil is the one most likely to overgeneralize it here.

## Possession needs its own naturalness curation, distinct from predication

predicate_natural (unit 2's fix for "tabaksin", you are a plate) answers
"would a person be called this". Existence asks a different question, "would
a person be said to have this", and the two do not coincide: doktor is a
natural predicate (doktorum, I am a doctor) but an unnatural possession
(doktorum var reads as a doctor on staff, not a role held), while araba is
the reverse in spirit -- a natural possession nobody would use as a
predicate. Generating a batch before shipping (the same discipline that
caught three separate bugs earlier this session) surfaced this immediately:
the default noun pool produced "I have man" and "you do not have girl",
exactly the shape of the original tabaksin bug, from a different cause.
Fixed the same way: a new possession_natural flag, curated by hand (48
nouns: kinship terms a person would plausibly say they have -- kardeşim var,
not adamım var -- plus concrete objects, food and drink, and a handful of
natural abstracts like vaktim var and fikrim var), read via
lexeme_filter: {possession_only: true}.

## ile is taught as the suffix it already was

INS (-(y)lA) has existed in suffixes.yaml since early in this project,
fully correct, fully tested at the engine level, and never once exposed to
a learner: no unit referenced it. It needed no new engine work, because it
already is an ordinary case-category suffix -- twofold harmony, the same y
buffer any vowel-final stem takes elsewhere -- not a new mechanism the way
existence's var/yok was. The free-standing word ile is mentioned in the
intro for recognition, but the suffix is what gets exercises, since that is
what a learner will actually produce and hear far more often, and teaching
both forms with equal weight would be teaching the exception before the
rule.

için and gibi, by contrast, are genuinely two separate words attaching to a
bare noun, so they reuse the phrase.py primitive existence.py already
proved out, not INS's single-suffix machinery. Neither needed the
naturalness curation existence required: "for a car" and "like a car" are
natural for essentially any noun, unlike "I have a car" or "you are a car"
-- but generating a batch still caught a real, smaller version of the same
class of problem, an adjective (iyi, good) drawing into a pool meant for
nouns and producing "iyi için" (for good), which does not mean anything on
its own the way "for a car" does. Fixed by restricting both concepts'
lexeme_filter to pos: noun explicitly, the same fix applied to unit 5's
verbal suffixes for the identical reason (a suffix or postposition's
correct domain has to be declared, not assumed from whatever
candidate_lexemes()'s default pool happens to include).

Deliberately out of scope: the genitive for pronoun complements (benim
için, not ben için), since this lexicon has no pronouns yet to test it
against; and kadar entirely, since it governs a different case depending on
which of its two meanings (comparison vs "until") is intended, a genuine
complication worth its own unit rather than a guessed-at corner of this one.

## The question particle needed a third phrase.py part, not a bigger Literal

mI looks at first like existence's var/yok or postpositions' için/gibi: a
fixed word placed after a predicate. It is not fixed, and modelling it as a
Literal would have taught the wrong rule. Two things set it apart. First,
mI itself harmonizes fourfold against whatever precedes it (var mı,
öğrenci mi, geliyor mu), the same live computation Phonology.resolve()
already does for every suffix, not a string chosen ahead of time the way
Literal's var/yok/için/gibi are. Second, and the real complication: for
every predicate type except existence, the person ending moves off the
predicate entirely and attaches to mI instead -- geliyor musun, never
geliyorsun mu -- which means mI itself has to be able to take a further
suffix chain, the way an ordinary stem does, not just sit there inertly
the way a Literal always has.

Solved without adding a second inflection code path: once mI's own vowel
is resolved, a synthetic Lexeme is built on the fly with that resolved
form as its lemma and harmony_class left unset, and handed to the exact
same engine.inflect() every Word already goes through. harmony_class
unset is what makes this correct rather than coincidental -- it means
backness and rounding for whatever suffix follows are read off mI's own
resolved vowel, not the original predicate's class, which is precisely
the harmony_back reset already in engine.py for the identical reason
(-(y)Iyor's own o governing harmony for a person suffix chained after it).
The new phrase.py part, QuestionParticle, is this: an optional suffix
chain plus a resolve-then-inflect step, verified directly against the
engine for all four predicate types (nominal, present progressive,
ability, existence) before a single test was written, exactly the same
discipline as everything else in this file.

Scoped to affirmative yes/no questions on predicate types already taught.
Past tense mI (a real, different rule: the person ending stays put and mI
follows the verb bare, geldin mi rather than geldi misin) is out of scope
because the past tense itself is not built yet; negative questions
(gelmiyor musun, aren't you coming) are ordinary NEG-then-question and
should work already through the same mechanism, but were not separately
curated into this unit's content.

## The past tense needed no engine work, and a genuinely new person paradigm

-DI looked, before it was checked, like it might need something new: every
other tense suffix taught so far either inserts a buffer after a vowel-final
stem (-(y)Iyor's y, -(y)Abil's y) or deletes the stem's own final vowel
first (-(y)Iyor's Ø step). -DI does neither. It attaches directly to
whatever precedes it, vowel or consonant, with nothing inserted and nothing
dropped: oku plus this suffix gives okudu, not okuydu or okudu-with-a-buffer.
D and I are both archiphonemes engine.py already handles in full generality
(voicing assimilation, fourfold harmony), so nothing in the engine changed
for this unit -- confirmed directly against it, not assumed, before a
suffix entry or a test was written: gel -> geldi, git -> gitti (D reads
git's own final t as voiceless, giving gitti rather than gidti; the
independent final_voicing rule that would otherwise apply to a stem like
kitap never fires here at all, since it only triggers before a
vowel-initial suffix, and D is not one), yap -> yaptı, oku -> okudu.

The person endings after -DI are a different matter. Before writing
anything, the working assumption (carried over from a much earlier point in
this project, before it was checked) was that these might reuse either the
predicative endings (unit 2, already reused twice more in units 5 and 6) or
the possessive endings (unit 3). Neither is correct. Research confirmed a
third, distinct paradigm -- traditionally described as the short subject
markers used only after the definite past -DI and the conditional -sA (not
built) -- m/n/Ø/k/nIz/lAr, matching neither predicative -(y)Im/-sIn/-DIr/
-(y)Iz/-sInIz nor possessive -(I)m/-(I)n/-(s)I/-(I)mIz/-(I)nIz. The clearest
tell is "we": geldik uses -k, which resembles neither -(y)Iz nor -(I)mIz at
all, so it cannot be reasoned out from a pattern a learner already has and
has to be taught as its own small, closed set. Third singular stays bare,
matching every other tense's precedent; third plural reuses -lAr directly,
the same reuse-over-duplication choice already made for present-tense
person marking in unit 5.

Scoped to the definite, witnessed past only. The reported/evidential past
(-mIş) is a real, separate distinction, not a variant of this one, and is
left for its own unit rather than taught alongside this one as an
afterthought.

## Past-tense mI is the exception to the rule unit 9 just taught as universal

Unit 9 taught one behavior across three predicate types (nominal, present
progressive, ability) and reused it a fourth time for existence: mI
harmonizes fourfold against whatever precedes it, always. The one place it
does not generalize is the past tense. There, the person ending -- unit
10's own paradigm, not the predicative one every unit 9 exercise was built
on -- stays on the verb exactly where a statement puts it, and mI simply
follows, bare: geldin mi, never geldi misin. Göksel and Kerslake describe
the past and the conditional (not taught here) as the two tenses where the
personal ending is retained on the verb itself rather than moving onto mI,
which is the mechanism this unit's why_hard text points at directly rather
than letting a learner discover it by producing geldi misin and being told
it is wrong.

This did not need a new phrase.py part, or even new logic inside the
existing one: `QuestionParticle` already supported a bare, no-suffix-chain
mode, because unit 9's own var mı / yok mu needed exactly that (var and yok
never carry a person suffix to begin with, so mI never has anything to
take from them). Past-tense mI is architecturally identical to that case,
not to question.py's nominal/progressive/ability shape where the particle
takes a further suffix chain: the verb (stem + DI + person) is inflected
in full first, exactly like any other Word, and QuestionParticle() with no
suffixes follows it as a second, invariant word. The one meaningful
difference from existence's case is the first word's own shape (a fully
inflected verb rather than a Literal like var/yok), which needed no change
to phrase.py at all -- render() already treats every Word the same way
regardless of what suffixes it carries. Confirmed directly against the
engine across all four verb-final harmony classes before anything shipped:
geldin mi, okudum mu, çalıştık mı, içtim mi -- every rounding, backness and
devoicing combination correct on the first attempt, since nothing here
asked the engine to do anything it had not already done for unit 9 and
unit 10 separately.

New content only: `past_question.py` and `past_question_production.py`,
the same build/assemble-plus-thin-wrapper shape every prior phrase.py
generator uses, with no other file touched except the registry.

## The 2026-09 theme is held to the same standard as the curriculum, not exempt from it

The visual redesign replaced generic Tailwind slate/rose with Langram's own
tokens (`web/src/index.css`), and three of its choices are pedagogical
decisions, not aesthetic ones, so they get the same accountability as any
content change.

**The Turkish form gets its own typeface.** Every exercise's stem, answer
and derivation result now render in Newsreader (`font-turkish`) rather than
the interface's own Archivo/IBM Plex faces. This is Schmidt's noticing
hypothesis applied directly: a form has to be consciously noticed before it
can be acquired, and giving the target-language text a typographic voice
distinct from every button, label and English gloss around it is what makes
it the one thing on screen that reads as language rather than chrome.
Deliberately not applied to every option button (`choose_meaning`'s English
choices, `choose_suffix`'s bare notation) -- only where the text actually is
Turkish, since applying it uniformly would dilute the distinction rather
than sharpen it.

**Structured input and free/scheduled output are two different colors, not
just two different words.** VanPatten's input processing says comprehension
has to precede production and that blurring the two undermines the staging.
`SessionScreen`'s stage badge (Notice/Build vs. Produce/Review) now carries
that distinction visually (`stageBadgeClass`), so a learner knows which
cognitive task they are in before reading the label.

**The unit map is drawn as a route, not a list, so weak-domain resurfacing
has somewhere to go.** `lib/domains.ts` groups the eleven units into three
recurring grammatical domains (nominal, verbal/tense, particle/phrase) and
`UnitsScreen` colors them the way a transit map colors lines. This is
presentation only today -- it makes no scheduling decision -- but it is the
visual home the roadmap's still-unbuilt weak-concept resurfacing needs:
once a learner's accuracy by domain is tracked, this is where it would
surface, rather than inventing a new screen for it later.

None of this touches content or the engine. The domain grouping in
`domains.ts` is explicitly commented as presentational, not a linguistic
claim, so it carries no citation obligation the way a lexicon flag or a
suffix's `review` tag would.

## The case system was finished, not started, and finished around meaning

Unit 3 already taught the buffer-consonant and voicing mechanics every case
suffix shares, but only ever applied them to the possessive suffixes. Five
real case suffixes (`ACC`, `DAT`, `LOC`, `ABL`, `GEN`) already existed,
fully correct, in `suffixes.yaml` and were already exhaustively checked in
`test_known_forms.py`'s known-forms oracle, and had simply never been
surfaced to a learner -- the same shape unit 8's `ile` was in before it
shipped. This unit closes that gap in one pass rather than one suffix at a
time, prompted directly by `docs/research-spec.md` naming the accusative as
its own worked example (section 3.4) and Stage 3 of its proposed Turkish
acquisition sequence (section 5.3).

Three design decisions, each traceable to a real source:

**The accusative gets two concepts, not one, because its difficulty is not
its shape.** Every other case suffix shipped so far is difficult the way a
new allomorph is difficult: harmony, a buffer, an alternation. The
accusative's real difficulty is that it marks specificity, not objecthood --
kitap istiyorum (a book, any) versus kitabı istiyorum (the book, a specific
one) -- a distinction English marks with an article and Turkish does not
mark at all outside this suffix. Splitting "notice the shape" from "notice
what it means" mirrors VanPatten's own point (already cited for units 5 and
9): a learner who has only drilled the shape has not been given anything
that forces the meaning to matter, so a second concept exists specifically
to put the same suffix's two readings in direct contrast, one word's
absence or presence of `-(y)I` and nothing else deciding which sentence is
meant. `docs/research-spec.md` section 3.4 asks for exactly this shape of
exercise (its own worked example is Turkish accusative marking); its
"picture" detail was adapted away since this app has no image assets, using
a fixed, universally-compatible verb (istemek, want) instead of a
picture as the second half of the minimal pair.

**Dative, locative and ablative are one concept, not three.** Turkish
treats to/at/from as a single paradigm sharing one slot and one harmony
pattern, and teaching them as three unrelated vocabulary items would hide
that. The one genuine trap when they are taught together, and the reason
this concept's own explanatory text leans on it directly: dative is
vowel-initial and triggers a stem's own final-consonant devoicing
alternation (kitap -> kitaba), while locative and ablative both begin with
the D archiphoneme, a consonant, and never trigger it (kitap -> kitapta,
kitaptan, not kitapda/kitapdan) -- the identical distinction unit 10 already
taught for -DI, confirmed to recur here by checking the engine directly
rather than assumed to generalize.

**Genitive is taught only as izafet, because that is the only way it is
actually used.** Rather than a fourth bare-shape concept, genitive is
introduced already doing its real job: naming a possessor explicitly
(öğrencinin kitabı, the student's book), pairing the new suffix with
POSS3SG, which unit 3 already taught. This is the first generator
(`izafet.py`) with two independently-drawn lexemes in a single item, which
is exactly what surfaced this unit's one real bug: its spec dictionary used
`"possessor"`/`"possessed"` keys instead of the `"lemma"` key `tutor.py`'s
`card_ref()` depends on for every other generator's review-card identity,
caught by the full test suite, not by generating a batch (the batch itself
looked completely correct; the bug was in review scheduling plumbing, not
in any Turkish form). Fixed by renaming the key rather than special-casing
`card_ref()` -- every generator should look the same from tutor.py's side,
one lexeme irregularity is not worth a second code path.

Generating a batch caught a second, smaller issue the way it always does:
`ok` (arrow) plus the accusative gives `oku`, identical in spelling to the
unrelated reading verb `oku`, which read as confusing in "oku istiyorum"
even though the sentence is grammatically correct. Fixed by restricting the
accusative-specificity concept's noun pool to `possession_only`, which
excludes `ok` as a side effect of asking for nouns someone would plausibly
say "I want ___" about in the first place, not by hand-excluding one word.

## Scheduling exposes desired_retention; the acquisition/retention split it did not have was already free

`docs/research-spec.md` section 3.6 (Suzuki & DeKeyser 2017) names a real
tension: the spacing that best builds automatization is short and dense,
the spacing that best builds durable retention expands over time, and a
scheduler needs both. Checked against `scheduling.py` before building
anything: FSRS, already in use, already has this. A card starts in
`State.Learning` and moves through fixed, short `learning_steps` (the
acquisition phase) before FSRS ever hands it to the expanding-interval
algorithm that governs `State.Review` (the retention phase). Nothing needed
building here; `tests/test_scheduling.py` (a new file -- none existed
before) confirms the split directly, by showing a brand new card's first
review is unaffected by `desired_retention` at all.

What genuinely was missing, per section 1.1 (Cepeda et al. 2008): FSRS's
own `desired_retention` parameter, its native "how aggressively should
intervals expand" control, was hardcoded to the library default (0.9) with
no way to change it. Exposed as a real parameter on `review()`, defaulting
to the same 0.9 so no existing behavior changes, and proven to have a real
effect (a lower target genuinely produces a longer next-review gap, not
just an accepted-and-ignored argument) rather than trusted to work.
Deliberately not wired to a per-user `target_retention_days` setting yet:
no onboarding flow asks a learner what their retention goal is, and adding
an unused database column and API surface for a preference nothing can set
would be exactly the over-engineering the research spec itself warns
against in the same section. This is the hook that setting would plug into
once one exists, not the setting itself.

## Blocks were never actually happening, and the block counter said so honestly

Reported directly, a second time: "1 of 5, Notice stuck at 1." The first
report was fixed with `STAGE_PROMOTION_THRESHOLD` (see the entry above on
verb person marking), which addressed one real cause -- two concepts
sharing a tier alternating forever -- but not the deeper one. `next_item()`
takes an `avoid_concept` parameter, documented as "the concept just
answered, so it is not repeated," and it excluded that concept from
candidates on *every single call*, unconditionally. `BLOCK_SIZE` (5) and
`_current_streak()` existed and were correctly implemented, but nothing
ever gave a concept the chance to accumulate a streak past 1 in the first
place, since the very next turn always excluded it (short of it being the
only candidate left, an edge case, not the normal multi-concept case this
curriculum has had since unit 1). The UI's "N of 5" was not lying about a
broken counter; it was accurately reporting that no block was ever
happening: the exclusion this app calls interleaving was total, applied
before a block could exist to be interleaved between.

Fixed by making the exclusion conditional: `avoid_concept` is only excluded
once its own streak has actually reached `BLOCK_SIZE`. Before that, the
concept just answered is looked up and served again directly, using the
same `stage_rank()` (comprehension-first, promoted after
`STAGE_PROMOTION_THRESHOLD`) that already governed which of its exercises
to pick. This is a real behavior change, not a tuning tweak: sessions will
now visibly repeat a concept several times before moving on, which is
BLOCK_SIZE's documented intent and what "N of 5" was always supposed to
mean, both true only in name until this fix. No test file existed for
`tutor.next_item` before this. `tests/test_api.py`'s existing interleaving
test asserted the old (broken) behavior directly -- `after` always
produces a different concept -- and had to be corrected, not just left
passing, since it was itself proof the bug had been accepted as intended
behavior at some point.

## cloze_suffix_choice gave its own answer away, reported directly by a learner

The exact report: a "Complete the sentence" item cued "teacher, I am,"
offering four suffix options, one of them labelled "I am." `assemble()`
computed the cue's `meaning` field and each option's own `gloss` field from
the identical source -- `(suffix.glosses or (suffix.id,))[0]` -- so for the
correct option specifically, the two strings were always exactly equal.
Nothing about Turkish had to be known to solve it: find the option whose
label matches words already in the prompt. This was not narrow to one
concept; every unit built on `cloze_suffix_choice` (predication, present
tense, ability, past tense, and their production/review variants) shipped
the same leak, undetected because generating a batch and reading the
Turkish answer, this session's usual discipline, never surfaces it -- the
Turkish form was always correct. Only reading the English side, cue against
options together, the way a learner actually experiences the item, caught
it.

Fixed by dropping `gloss` from each option entirely: a `SuffixOption` is
now `{id, notation}` only, so choosing has to mean recognizing which
notation carries the meaning the cue already states, not matching a label
against the prompt's own words. This narrows what the exercise can test
(the archiphoneme notation `-(y)Im` no longer carries a redundant label
that happened to double as the answer key) without narrowing what it is
supposed to test in the first place -- the payload never needed the gloss
at all, since `cloze_suffix_choice.py`'s own docstring already says options
are "shown in archiphoneme notation, so choosing does not leak the shape,"
a stated design goal the gloss field was quietly working against the whole
time.

## Nothing is asserted that a native speaker has not confirmed

Content carries review flags rather than confident guesses. A learner who is
taught a wrong alternation has to unlearn it later, which is more expensive than
the delay of asking.
