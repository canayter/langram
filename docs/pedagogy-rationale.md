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

## Nothing is asserted that a native speaker has not confirmed

Content carries review flags rather than confident guesses. A learner who is
taught a wrong alternation has to unlearn it later, which is more expensive than
the delay of asking.
