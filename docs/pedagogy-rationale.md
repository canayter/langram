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

## Nothing is asserted that a native speaker has not confirmed

Content carries review flags rather than confident guesses. A learner who is
taught a wrong alternation has to unlearn it later, which is more expensive than
the delay of asking.
