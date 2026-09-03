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

## Nothing is asserted that a native speaker has not confirmed

Content carries review flags rather than confident guesses. A learner who is
taught a wrong alternation has to unlearn it later, which is more expensive than
the delay of asking.
