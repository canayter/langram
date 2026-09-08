# Langram: Research Specification

**Evidence base for a Turkish-for-English-speakers learning app**
Peer-reviewed SLA and instructed-SLA findings, 2019-2025 emphasis, translated into build constraints.

Provided by the project owner, 2026-09-07, as a planning reference. Not yet
scoped into implementation work -- see `docs/pedagogy-rationale.md` for what
is actually built and cited today, and `content/bibliography.yaml` for the
subset of sources this repo's validator currently allows a unit to cite.
Where this document's citations overlap with an existing `needs_citation`
entry there, the entry has been filled in with the fuller reference; nothing
here has been marked `verified` on the strength of this document alone --
that status is reserved for someone actually checking a claim against the
source page by page, per the working agreement in `CLAUDE.md`.

---

## 0. How to use this document

Every section is structured the same way:

- **Finding**: what the research shows, with effect sizes where available
- **Source**: peer-reviewed citation
- **Build implication**: the concrete parameter, schema field, or UI behavior it constrains

When a finding and a design intuition conflict, the finding wins. When the evidence is genuinely mixed, this document says so rather than picking a side, and you should make the behavior configurable so it can be A/B tested later.

Effect sizes are reported as Hedges' g or Cohen's d. Use Plonsky and Oswald's (2014) L2-field-specific benchmarks, not Cohen's generic ones: **0.40 = small, 0.70 = medium, 1.00 = large**. This matters because a g of 0.60 is unimpressive by SLA standards even though Cohen would call it medium-to-large.

---

## 1. Cross-cutting learning principles

These apply across grammar, vocabulary, and pronunciation. They should be implemented once, in a shared scheduling and practice engine, not duplicated per skill.

### 1.1 Spacing

**Finding.** Spaced practice reliably beats massed practice for L2 learning. Kim and Webb's meta-analysis of 48 experiments (98 effect sizes, N = 3,411) confirmed the advantage for both vocabulary and grammar. Latimier, Peyre, and Ramus found spaced retrieval practice outperformed massed retrieval practice at g = 0.74 across 29 studies.

**Critical nuance.** Expanding schedules (1d, 3d, 7d, 21d) and uniform schedules (7d, 7d, 7d) are **statistically equivalent** in both Kim and Webb (2022) and Latimier et al. (2021). Nakata (2015) found a small expanding advantage but concluded the presence of spacing matters far more than its shape.

- Kim, S. K., & Webb, S. (2022). The effects of spaced practice on second language learning: A meta-analysis. *Language Learning*, 72(1), 269-319.
- Latimier, A., Peyre, H., & Ramus, F. (2021). A meta-analytic review of the benefit of spacing out retrieval practice episodes on retention. *Educational Psychology Review*, 33, 959-987.
- Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008). Spacing effects in learning: A temporal ridgeline of optimal retention. *Psychological Science*, 19(11), 1095-1102.

**Build implication.**
- Do not over-engineer the interval algorithm. A simple expanding schedule is fine; the returns to tuning it are small compared to the returns to making sure users actually get spaced exposure at all.
- Cepeda et al.'s ridgeline result gives the one parameter worth tuning: **optimal gap is roughly 10-20% of the target retention interval**. If you want a learner to hold an item for 6 months, review gaps should stretch toward 3-5 weeks. If the goal is a 1-week quiz, gaps of 1 day are right. Expose "retention goal" as a user-level setting and derive intervals from it.
- Store `target_retention_days` per user or per deck, and compute intervals as a function of it rather than hardcoding SM-2 constants.

### 1.2 Retrieval practice (the testing effect)

**Finding.** Retrieving from memory beats re-studying. Rowland's meta-analysis of 159 effect sizes found g = 0.50 for retrieval versus restudy. The benefit compounds with spacing: spaced retrieval is the strongest single combination in the literature.

- Rowland, C. A. (2014). The effect of testing versus restudy on retention: A meta-analytic review of the testing effect. *Psychological Bulletin*, 140(6), 1432-1463.
- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science*, 17(3), 249-255.

**Build implication.**
- Every review encounter must require production or selection **before** the answer is shown. Never show a form and its meaning together and call it a review.
- Recall beats recognition. Multiple choice is a fallback for very weak items, not the default. Implement a per-item "retrieval strength ladder": recognition -> cued recall with first letter -> free recall -> productive use in a sentence. Promote items up the ladder as strength grows.
- Log the *retrieval format* on every review, not just correct/incorrect. Format is a moderator you will want in your own analytics.

### 1.3 Feedback timing

**Finding.** Kim and Webb found large effects for both immediate feedback (g = 1.04) and delayed feedback (g = 0.64-2.34) in L2 spaced practice. Neither is clearly superior across contexts. In computer-mediated settings specifically, immediate trial-by-trial feedback is the standard and is well supported.

Notably, the HVPT literature found feedback **type** (showing only the correct target, showing target plus the wrong option, or just signaling "wrong") did not significantly moderate outcomes (Q = 0.12, p = .941).

**Build implication.**
- Default to immediate feedback after each item. It is at least as good, and it is far better for engagement.
- Do not spend engineering effort on elaborate feedback presentation. The evidence says the presence of feedback matters, its cosmetic form does not. Spend that effort on error *diagnosis* instead (see 3.4).

### 1.4 Transfer-appropriate processing

**Finding.** Learning transfers best when the practice format matches the target-use format. The HVPT meta-analysis is the cleanest demonstration: identification training tested with identification yielded g = 1.11, but discrimination training tested with identification dropped to g = 0.67. Same underlying skill, mismatched format, roughly 40% of the effect lost.

- Morris, C. D., Bransford, J. D., & Franks, J. J. (1977). Levels of processing versus transfer appropriate processing. *Journal of Verbal Learning and Verbal Behavior*, 16(5), 519-533.
- Uchihara, T., Karas, M., & Thomson, R. I. (2025). High variability phonetic training (HVPT): A meta-analysis of L2 perceptual training studies. *Studies in Second Language Acquisition*, 47(3), 794-827.

**Build implication.**
- Decide what each skill is *for* and train in that modality. If the goal is understanding spoken Turkish, train with audio input, not written. If the goal is speaking, require spoken or typed production, not tapping word tiles.
- Word-tile exercises (the Duolingo default) train recognition and syntax assembly, not recall. They are legitimate but should be tagged as a distinct exercise type with its own mastery track, not conflated with production mastery.

### 1.5 Desirable difficulties, and their limit

**Finding.** Conditions that slow acquisition often improve retention: spacing, interleaving, retrieval effort, variability of input. But the effect is not monotonic. Fuhrmeister and Myers (2020) showed variability can be an *undesirable* difficulty for low-aptitude learners, and the HVPT data show learners with higher pretest accuracy gain less from training (r = -.52 between pretest score and gain).

- Bjork, R. A., & Bjork, E. L. (2011). Making things hard on yourself, but in a good way.
- Fuhrmeister, P., & Myers, E. B. (2020). Desirable and undesirable difficulties. *Attention, Perception, & Psychophysics*, 82, 2049-2065.

**Build implication.**
- Ramp difficulty by measured performance, not by lesson number. Store a per-user, per-contrast difficulty level and adjust it from rolling accuracy.
- Target roughly 80-85% accuracy in review sessions. Below that, learners disengage; above 90%, you are wasting their time on over-learned items.

### 1.6 Learner-controlled scheduling underperforms

**Finding.** Learners' judgments of learning are poorly calibrated. They drop items too early, believing fluent recognition means durable knowledge.

- Karpicke, J. D. (2009). Metacognitive control and strategy selection. *Journal of Experimental Psychology: General*, 138(4), 469-486.

**Build implication.** Do not let users mark items "known" and remove them from scheduling. Offer a "bury for now" that suppresses an item for a bounded window and returns it, rather than a permanent dismissal.

---

## 2. Vocabulary

### 2.1 Coverage targets set your word list size

**Finding.** Comprehension requires knowing a high proportion of the running words in a text. 95% coverage supports adequate comprehension with some guessing; 98% supports unassisted comprehension.

- Hu, M., & Nation, P. (2000). Unknown vocabulary density and reading comprehension. *Reading in a Foreign Language*, 13(1), 403-430.
- Laufer, B., & Ravenhorst-Kalovski, G. C. (2010). Lexical threshold revisited. *Reading in a Foreign Language*, 22(1), 15-30.
- Nation, I. S. P. (2006). How large a vocabulary is needed for reading and listening? *Canadian Modern Language Review*, 63(1), 59-82.

**Build implication for Turkish specifically.**
- These thresholds are stated in word families, which is a problem for an agglutinative language. Turkish surface-form frequency lists are near-useless because a single lemma spawns hundreds of inflected forms. You **must** lemmatize before counting.
- Use a morphological analyzer: Zemberek-NLP (Java, mature), TRmorph, or Stanza's Turkish pipeline. Build your frequency list over lemmas plus a separate productivity ranking over derivational suffixes.
- Corpus sources: Turkish National Corpus (TNC, Aksan et al. 2012, ~50M words, balanced), TS Corpus, METU-Sabancı Treebank for syntactic patterns, OpenSubtitles for spoken register.
- Plan a core list of roughly 2,000-3,000 lemmas for A1-B1, sequenced by frequency band, with each band tagged for coverage contribution so you can show users "you now understand ~X% of running text."

### 2.2 Incidental learning from input is real but slow

**Finding.** Webb, Uchihara, and Yanagisawa's meta-analysis (24 studies, N = 2,771) found learners pick up **9-18% of target words** on immediate posttests and 6-17% on delayed posttests from meaning-focused input alone. Gains were similar for reading (17%/15%), listening (15%/13%), and reading-while-listening (13%/17%), but notably lower for viewing with subtitles (7%/5%).

- Webb, S., Uchihara, T., & Yanagisawa, A. (2023). How effective is second language incidental vocabulary learning? A meta-analysis. *Language Teaching*, 56(2), 161-180.

**Build implication.** Input is a supplement, not the engine. Deliberate study is far more efficient per minute. Budget roughly: deliberate retrieval as the spine, extensive input as reinforcement and for the knowledge dimensions deliberate study does not deliver (collocation, register, contextual nuance).

### 2.3 Repetition matters less than commonly assumed

**Finding.** Uchihara, Webb, and Yanagisawa's meta-analysis of correlational studies found the relationship between number of encounters and incidental vocabulary learning was **medium at best** (average r around .34), and moderated heavily by spacing, learner proficiency, and context informativeness. Teng found that 10 encounters in an informative context triggered reliable gains, but 10 encounters in an uninformative context did not.

- Uchihara, T., Webb, S., & Yanagisawa, A. (2019). The effects of repetition on incidental vocabulary learning: A meta-analysis of correlational studies. *Language Learning*, 69(3), 559-599.
- Teng, F. (2019). The effects of context and word exposure frequency on incidental vocabulary acquisition and retention through reading. *Language Learning Journal*, 47(2), 145-158.

**Build implication.** Do not optimize for raw encounter counts. Optimize for **informative contexts**: sentences where the surrounding material genuinely constrains the meaning. Add a `context_informativeness` field to your example sentences and prefer high-informativeness contexts for first encounters.

### 2.4 Task depth: the Involvement Load Hypothesis and its correction

**Finding.** Laufer and Hulstijn's Involvement Load Hypothesis predicts that gains increase with the task's combined *need*, *search*, and *evaluation* load. Yanagisawa and Webb's meta-analysis of 42 studies largely supported the ordinal prediction but found ILH explains **limited variance**, and the three components contribute unequally. Their revised "ILH+" model adds encounter frequency and test format as predictors.

- Laufer, B., & Hulstijn, J. (2001). Incidental vocabulary acquisition in a second language. *Applied Linguistics*, 22(1), 1-26.
- Yanagisawa, A., & Webb, S. (2021). Involvement load hypothesis plus: Creating an improved predictive model of incidental vocabulary learning. *Studies in Second Language Acquisition*, 43(5), 1279-1308.

**Build implication.** Rank your exercise types by involvement load and use higher-load tasks for items that have failed twice or more. A rough ladder for Turkish:
1. Meaning recognition (multiple choice) - low load
2. Meaning recall (produce English gloss) - moderate
3. Form recall (produce Turkish from English) - moderate-high
4. Gap-fill in a sentence requiring correct suffixation - high (adds evaluation)
5. Sentence construction from a prompt - highest

### 2.5 Four dimensions of word knowledge, tested separately

**Finding.** Form recognition, form recall, meaning recognition, and meaning recall are dissociable. A learner can score 90% on meaning recognition and 20% on form recall for the same set. Recognition-only testing systematically inflates apparent learning.

- Webb, S. (2005). Receptive and productive vocabulary learning. *Studies in Second Language Acquisition*, 27(1), 33-52.
- Nation, I. S. P. (2013). *Learning Vocabulary in Another Language* (2nd ed.). Cambridge.

**Build implication.** Your schema should track mastery per dimension, not per word:

```
lexical_item
  id, lemma, pos, frequency_rank, coverage_contribution
  gloss_en, ipa, audio_variants[]
  morphological_class          -- for suffix behavior
  vowel_harmony_class          -- front/back, rounded/unrounded
  final_consonant_alternation  -- p/b, ç/c, t/d, k/ğ

user_lexical_state
  user_id, lexical_item_id
  strength_form_recognition
  strength_form_recall
  strength_meaning_recognition
  strength_meaning_recall
  strength_collocational
  next_due_per_dimension
```

Do not collapse these into a single scalar. A single "mastery %" is the single most common design error in vocabulary apps and it makes your own efficacy analytics uninterpretable.

### 2.6 Deliberate paired-associate learning produces implicit knowledge

**Finding.** A persistent myth is that flashcard learning produces only explicit, inert knowledge. Elgort showed that deliberately learned L2 words show masked repetition and semantic priming effects, meaning they are integrated into the mental lexicon and accessed automatically.

- Elgort, I. (2011). Deliberate learning and vocabulary acquisition in a second language. *Language Learning*, 61(2), 367-413.
- Elgort, I., & Warren, P. (2014). L2 vocabulary learning from reading. *Language Learning*, 64(2), 365-414.

**Build implication.** Do not apologize for flashcards or hide them behind gamified wrappers that dilute retrieval. They are the highest-efficiency component you have. Make them fast, spaced, and productive.

### 2.7 Multiword units

**Finding.** Formulaic sequences and collocations are processed faster than novel combinations and contribute disproportionately to perceived fluency. They are not learned reliably from word-level study.

- Boers, F., & Lindstromberg, S. (2012). Experimental and intervention studies on formulaic sequences. *Annual Review of Applied Linguistics*, 32, 83-110.
- Siyanova-Chanturia, A., & Pellicer-Sanchez, A. (Eds.) (2019). *Understanding Formulaic Language*. Routledge.

**Build implication for Turkish.** Turkish has a large inventory of light-verb constructions (`yardım etmek`, `merak etmek`, `karar vermek`) and postposition collocations that English speakers systematically get wrong by translating the verb literally. Build a separate `collocation` entity with its own scheduling track. Extract candidates from the TNC using pointwise mutual information over lemma bigrams.

---

## 3. Grammar

### 3.1 Explicit instruction works, but the picture has shifted

**Finding.** The classical result (Norris and Ortega 2000) was that explicit instruction substantially outperforms implicit, with explicit around d = 1.13 versus implicit d = 0.54. Spada and Tomita (2010) confirmed explicit advantages for both simple and complex forms, including on free-production measures.

**The correction.** Two things complicate this. First, Norris and Ortega's outcome measures were biased toward explicit knowledge (metalinguistic judgments), which favors explicit treatments by construction. Second, Kang, Sok, and Han's more recent meta-analysis covering 35 years of form-focused instruction research found explicit and implicit instruction produced **similar effects**, with implicit slightly higher in their sample, and found robust support for input enhancement and recasting.

- Norris, J. M., & Ortega, L. (2000). Effectiveness of L2 instruction. *Language Learning*, 50(3), 417-528.
- Spada, N., & Tomita, Y. (2010). Interactions between type of instruction and type of language feature. *Language Learning*, 60(2), 263-308.
- Goo, J., Granena, G., Yilmaz, Y., & Novella, M. (2015). Implicit and explicit instruction in L2 learning: Norris and Ortega (2000) revisited.
- Kang, E. Y., Sok, S., & Han, Z. (2019). Thirty-five years of ISLA on form-focused instruction: A meta-analysis. *Language Teaching Research*, 23(4), 428-453.

**Build implication.**
- Include explicit rule statements, but keep them **short and just-in-time**. The evidence supports brief metalinguistic explanation delivered at the point of need, not grammar lectures.
- Pair every rule with immediate practice. The explicit advantage in the literature comes from explicit-instruction-plus-practice conditions, essentially never from explanation alone.
- Design rule cards as a distinct content type: one sentence of the generalization, two contrasting examples, one counterexample or scope limit. Cap at roughly 60 words.

### 3.2 Corrective feedback is effective and durable

**Finding.** Li's meta-analysis found an overall effect of d = 0.61 for corrective feedback on L2 grammar, and, unusually, **effects were larger on delayed posttests than immediate ones**. Explicit feedback produced larger short-term gains; implicit feedback showed better durability. Lyster and Saito found prompts (which push the learner to self-correct) outperformed recasts in classroom settings.

- Li, S. (2010). The effectiveness of corrective feedback in SLA: A meta-analysis. *Language Learning*, 60(2), 309-365.
- Lyster, R., & Saito, K. (2010). Oral feedback in classroom SLA. *Studies in Second Language Acquisition*, 32(2), 265-302.
- Russell, J., & Spada, N. (2006). The effectiveness of corrective feedback for the acquisition of L2 grammar.

**Build implication.**
- When a learner produces an incorrect form, prefer a **prompt** over a correction on first error: highlight the erroneous morpheme and ask them to retry. Give the explicit correction on the second failure. This is directly implementable and is the single highest-value feedback design choice available to you.
- Measure your own efficacy on delayed posttests. Immediate-only measurement will understate corrective feedback effects.

### 3.3 Developmental readiness constrains sequencing

**Finding.** Processability Theory holds that learners acquire morphosyntactic structures in a fixed developmental order determined by processing constraints, and that instruction targeting a stage the learner is not ready for produces little durable gain.

- Pienemann, M. (1998). *Language Processing and Second Language Development*. Benjamins.
- Pienemann, M. (2005). *Cross-Linguistic Aspects of Processability Theory*. Benjamins.

**Build implication.** Do not sequence purely by frequency or by textbook convention. Gate advanced morphosyntax (relative clauses, complex embedding) behind demonstrated mastery of the prerequisite stage. Concretely for Turkish, see 5.3.

### 3.4 Input processing and structured input

**Finding.** VanPatten's model holds that learners default to processing lexical items for meaning and skip redundant grammatical morphology. Structured input activities force attention to the morpheme by making it the only cue to meaning. Shintani, Li, and Ellis's meta-analysis found processing instruction effective for comprehension, but **output-based practice better for production**.

- VanPatten, B. (2004). *Processing Instruction: Theory, Research, and Commentary*. Erlbaum.
- Shintani, N., Li, S., & Ellis, R. (2013). Comprehension-based versus production-based grammar instruction: A meta-analysis. *Language Learning*, 63(2), 296-329.

**Build implication.** This is a concrete exercise-design pattern. For Turkish accusative marking, do not present `Kitabı okudum` alongside a picture. Present two sentences differing only in the accusative suffix and require the learner to pick the matching picture. The morpheme must carry the semantic load or it will be ignored.

Include both comprehension-based and production-based exercises for every target structure, and tag them so you can compare.

### 3.5 Input enhancement alone is weak

**Finding.** Textual enhancement (bolding, coloring the target form) has a small effect on its own: Lee and Huang found d = 0.22 for form learning.

- Lee, S. K., & Huang, H. T. (2008). Visual input enhancement and grammar learning. *Studies in Second Language Acquisition*, 30(3), 307-331.

**Build implication.** Highlight morphemes, but do not expect it to teach anything by itself. It is a cheap attention cue that supports other instruction, not a technique.

### 3.6 Practice and proceduralization

**Finding.** Skill Acquisition Theory holds that L2 knowledge moves from declarative to procedural to automatized through practice, following a power law. Suzuki and DeKeyser showed that the spacing that best supports proceduralization differs from the spacing that best supports declarative retention: **shorter gaps aid automatization; longer gaps aid retention**.

- DeKeyser, R. (2007). *Practice in a Second Language*. Cambridge.
- Suzuki, Y., & DeKeyser, R. (2017). Effects of distributed practice on the proceduralization of morphology. *Language Teaching Research*, 21(2), 166-188.

**Build implication.** This is a genuine tension in your scheduler. Resolve it by phase:
- **Acquisition phase** (first ~5 encounters with a structure): short gaps, high density, same session or same day. Goal is proceduralization.
- **Retention phase** (thereafter): expanding gaps per 1.1. Goal is durable memory.

Store a `phase` field on the user-structure state and switch scheduling policy on it.

---

## 4. Pronunciation

This is the section where the evidence is most precise and most under-implemented in commercial apps. It is also where an acoustic phonetics background gives Langram a real differentiator.

### 4.1 High Variability Phonetic Training is the best-supported paradigm

**Finding.** Uchihara, Karas, and Thomson's meta-analysis of **79 studies** is the definitive current synthesis. Headline results:

| Outcome | Effect |
|---|---|
| Pretest-posttest perception gain | g = 0.92 (g = 0.71 after publication-bias correction) |
| Treatment vs control | g = 0.67 |
| Typical accuracy gain | 12-14 percentage points |
| Retention at 0.5 to 6 months | maintained, posttest-to-delayed g = -0.08 (negligible decay) |
| Generalization to novel talker + novel item | small decrement, g = -0.25 |
| Untrained control group drift | 2.7 percentage points, g = 0.19 |

Canonical HVPT requires exactly three features: **talker variability, phonetic context variability, and trial-by-trial corrective feedback**. Remove any one and it is not HVPT and the effects do not hold.

- Uchihara, T., Karas, M., & Thomson, R. I. (2025). High variability phonetic training (HVPT): A meta-analysis of L2 perceptual training studies. *Studies in Second Language Acquisition*, 47(3), 794-827. (Open access, CC-BY)
- Thomson, R. I. (2018). High Variability [Pronunciation] Training. *Journal of Second Language Pronunciation*, 4(2), 208-231.
- Zhang, X., Cheng, B., & Zhang, Y. (2021). The role of talker variability in nonnative phonetic learning. *Journal of Speech, Language, and Hearing Research*, 64(12), 4802-4825.

### 4.2 HVPT moderators: the exact parameters to build to

This is the most directly actionable table in the whole document. All values from Uchihara et al. (2025) moderator analyses.

| Design choice | Finding | Build decision |
|---|---|---|
| **Training task** | Identification g = 0.95 vs discrimination g = 0.57 (Q = 15.54, p < .001) | Use **identification** (hear a token, pick which category it is). Do not use same/different discrimination. |
| **Response labels** | Keywords g = 1.03, phonetic symbols g = 1.01, orthography g = 0.90, **visual images g = 0.47** | Use written keywords or Turkish orthography as response buttons. **Do not use pictures.** Pictures split attention between form and meaning and roughly halve the training effect. |
| **Total training time** | Positive and significant up to ~400 minutes, then plateaus through 1,125 min | Budget roughly **400 minutes (6.7 hours) total per contrast set**. Past that, move the learner to a new contrast rather than continuing. |
| **Number of talkers** | No overall effect 2-30. For higher-proficiency learners, gains rose with talker count up to 6 (g = 0.66 at 3 talkers -> g = 1.44 at 6). Lower-proficiency learners showed no talker-count sensitivity. | Record **6 talkers minimum** per target sound. Serve fewer (2-4) to beginners, all 6 to intermediate and above. |
| **Talker presentation** | Blocked g = 0.99 vs intermixed g = 0.89, n.s. | Either works. Pick intermixed for simplicity. |
| **Feedback type** | Target-only, target-plus-distractor, and wrong-signal-only did not differ (p = .941) | Simplest implementation is fine. Just signal correctness and replay the correct token. |
| **Real words vs nonwords** | No difference (p = .809) | Use real Turkish words. Free vocabulary exposure at no cost to phonetic gains. |
| **Adaptive vs fixed difficulty** | g = 1.06 vs 0.91, n.s. | Adaptive is not proven better. Build fixed first; adaptivity is a nice-to-have. |
| **Audiovisual (talking heads)** | g = 0.82 vs audio-only 0.93, n.s. | Skip video. Not worth the production cost. |
| **Session length** | Not a significant predictor | Short sessions are fine. Optimize for adherence. |
| **Training environment** | Lab g = 0.95, participant-controlled g = 0.83, classroom g = 0.87, n.s. | **At-home self-paced training works.** This is the finding that licenses HVPT in a consumer app. |
| **Target sound type** | Syllable structure g = 1.41, sonorants g = 1.17, vowels g = 1.00, tone g = 1.00, obstruents g = 0.69 | Vowels train well, which is fortunate for Turkish. |

**Two learner-side findings that affect your targeting.**
- Pretest accuracy correlates **negatively** with gain (r = -.52). Learners who already perceive the contrast well have little to gain. Diagnose before training and skip contrasts a user already handles.
- Longer prior L2 experience predicted **smaller** gains (b = -.036, p = .029), likely because entrenched L1-based perceptual routines resist restructuring. Beginners are your best HVPT audience.

### 4.3 Perception training transfers to production, partially

**Finding.** Uchihara, Karas, and Thomson's earlier meta-analysis found perceptual HVPT improves production accuracy at g = 0.49 to 0.66, smaller than perception gains (10.6% on trained items, 4.5% on untrained). Support for long-term retention and generalization of production gains was weaker.

- Uchihara, T., Karas, M., & Thomson, R. I. (2024). Does perceptual high variability phonetic training improve L2 speech production? *Applied Psycholinguistics*, 45(4), 591-623.
- Sakai, M., & Moorman, C. (2018). Can perception training improve the production of second language phonemes? *Applied Psycholinguistics*, 39(1), 187-224.

**Build implication.** Perception training is necessary but not sufficient for production. Add explicit production practice (recording plus feedback) as a separate module. Do not claim perception training will fix a learner's accent.

### 4.4 Intelligibility, not accent

**Finding.** Levis's intelligibility principle: the goal of pronunciation instruction is being understood, not sounding native. Saito and Plonsky's framework separates accentedness, comprehensibility, and intelligibility as distinct constructs with different instructional sensitivities. Suzukida and Saito showed that **functional load** predicts which segmental errors actually damage comprehensibility.

- Levis, J. M. (2005). Changing contexts and shifting paradigms in pronunciation teaching. *TESOL Quarterly*, 39(3), 369-377.
- Saito, K., & Plonsky, L. (2019). Effects of second language pronunciation teaching revisited. *Language Learning*, 69(3), 652-708.
- Suzukida, Y., & Saito, K. (2021). Which segmental features matter for successful L2 comprehensibility? *Language Teaching Research*, 25(3), 431-450.

**Build implication.** Prioritize contrasts by functional load in Turkish, not by how "foreign" they sound. Compute functional load from your TNC lemma frequencies: for each phoneme pair, count minimal pairs weighted by frequency. Train the high-load contrasts first. See 5.1.

### 4.5 ASR-based pronunciation scoring: use with caution

**Finding.** Automatic pronunciation assessment correlates only moderately with human ratings, and correlations degrade for lower-proficiency speech, which is exactly your population. Reviews of computer-assisted pronunciation training report positive effects overall but flag scoring reliability as the weak point.

- Mahdi, H. S., & Al Khateeb, A. A. (2019). The effectiveness of computer-assisted pronunciation training. *Cogent Education*, 6(1).
- Neri, A., Cucchiarini, C., & Strik, H. (2008). The effectiveness of computer-based speech corrective feedback. *ReCALL*, 20(2), 225-243.

**Build implication.** Use ASR for coarse binary or three-level judgments ("clear / unclear / try again") on whole words. Do not give per-phoneme numeric scores. If you want finer feedback, a formant-based visualization of the learner's vowel against a native reference ellipse is more defensible than a black-box score, and it plays directly to a Praat and formant-modeling background.

### 4.6 Speech Learning Model and PAM-L2: why some sounds are hard

**Finding.** Flege's revised Speech Learning Model (SLM-r) predicts that L2 sounds perceived as similar to an L1 category are hardest, because equivalence classification blocks new category formation. Genuinely novel sounds with no L1 counterpart can be easier to establish. Best and Tyler's PAM-L2 makes related predictions based on how L2 sounds assimilate to L1 categories.

- Flege, J. E., & Bohn, O. S. (2021). The revised Speech Learning Model (SLM-r). In Wayland (Ed.), *Second Language Speech Learning*. Cambridge.
- Best, C. T., & Tyler, M. D. (2007). Nonnative and second-language speech perception.

**Build implication.** Sequence Turkish contrasts by predicted assimilation type, not by orthographic novelty. See 5.1 for the Turkish-specific mapping.

---

## 5. Turkish-specific research

This is where Langram can beat generic apps, because almost none of this is implemented anywhere.

### 5.1 The vowel system and English-speaker difficulty

Turkish has a symmetrical eight-vowel system defined by three binary features: **[±back], [±high], [±round]**.

| | Unrounded | Rounded |
|---|---|---|
| **Front high** | i | ü /y/ |
| **Front non-high** | e | ö /ø/ |
| **Back high** | ı /ɯ/ | u |
| **Back non-high** | a | o |

**Predicted difficulty for L1 English speakers, by SLM-r/PAM-L2:**

1. **/y/ (ü) and /ø/ (ö)** - no English counterparts. New categories, initially very hard perceptually but establishable. English speakers commonly substitute /u/ and /o/ or the /ju/ sequence.
2. **/ɯ/ (ı)** - the hardest case. It assimilates variably to English schwa, /ɪ/, or /u/, with no stable mapping. The /i/-/ɯ/ contrast has extremely high functional load in Turkish because it is carried by the vowel harmony system itself.
3. **/e/ vs /a/** - relatively easy, but English speakers over-diphthongize Turkish /e/ and /o/, which Turkish does not have.
4. **Vowel length** - Turkish is largely non-contrastive for length except in Arabic/Persian loans (`hâlâ` vs `hala`). Low priority.

**Build implication.** Priority HVPT contrast list, in order:

```
1. /i/ vs /ɯ/          (highest functional load; drives harmony)
2. /u/ vs /y/          (rounding + backness)
3. /o/ vs /ø/
4. /ɯ/ vs /u/
5. /e/ vs /a/          (low difficulty, high frequency, quick win)
6. monophthong /e/ /o/ vs English diphthongal realizations (production-focused)
```

Given an acoustic phonetics background specifically in Turkish vowel production by native and non-native speakers, this is the module where something genuinely novel is buildable: an F1/F2 vowel-space visualization that plots the learner's productions against a native reference distribution. Extract formants with Parselmouth (the Python interface to Praat) server-side, or with a WebAudio LPC implementation client-side if real-time matters.

### 5.2 Vowel harmony: what learners actually acquire

**Finding.** Özçelik and Sprouse's work is the key study here. English-speaking learners of Turkish acquire **canonical vowel harmony** from explicit instruction and abundant input, as expected. More interestingly, they also show knowledge of **non-canonical vowel harmony** (the patterns triggered by "light" versus "dark" laterals, as in `hal` -> `hali` versus `hal` -> `halı`), for which they receive no instruction and very little input. This is a poverty-of-the-stimulus argument: acquisition appears guided by a universal phonological principle (the No Crossing Constraint).

They also found that **orthography helps early and hinders later**. Turkish orthography transparently encodes most of the phonology, which facilitates early phonological development, but the non-transparent parts (where orthography obscures the lateral distinction) actively inhibit acquisition of non-canonical harmony in early learners. Advanced learners come to rely less on orthography.

- Özçelik, Ö., & Sprouse, R. A. (2017). Emergent knowledge of a universal phonological principle in the L2 acquisition of vowel harmony in Turkish. *Second Language Research*, 33(2), 179-206.
- Özçelik, Ö., & Sprouse, R. A. (2016). Decreasing dependence on orthography in phonological development. In Gürel (Ed.), *Second Language Acquisition of Turkish*. Benjamins.

**Build implication.**
- Teach canonical harmony explicitly and early. It is rule-governed, high-yield, and learners get it.
- **Provide audio alongside orthography for every vowel harmony exercise.** The Özçelik and Sprouse finding is that orthography-only presentation actively misleads for the non-canonical cases. Audio-plus-orthography beat audio-alone for canonical harmony accuracy but the reverse pattern showed up for non-canonical items.
- Do not teach non-canonical harmony as a rule. Provide the input (audio of `hali` vs `halı`, `usul` vs `usulü`) and let it develop.
- Encode `vowel_harmony_class` per lemma in your schema (last vowel's [back] and [round] values) so suffix selection can be generated and validated programmatically.

### 5.3 Morphology: acquisition order and known difficulty hierarchy

**Findings from the L2 Turkish literature.**

- **Case morphology is used variably** by learners, with the **accusative** the most error-prone. Learners struggle particularly with the interaction of case and non-canonical word order. Verbal inflection is acquired relatively well by comparison.
- Among TAM markers, **-mIş (evidential)** shows the most variability and emerges late. It requires conceptual learning (the reported/inferred distinction) beyond the morphology itself, which English does not grammaticalize.
- Errors are predominantly **omissions rather than substitutions**, which supports a Missing Surface Inflection account rather than a representational deficit.
- Nominal case morphology is used *less* variably than TAM markers, which runs against some theoretical predictions.

- Papadopoulou, D., Varlokosta, S., Spyropoulos, V., Kaili, H., Prokou, S., & Revithiadou, A. (2011). Case morphology and word order in second language Turkish. *Second Language Research*, 27(2), 173-204.
- Gürel, A. (Ed.) (2016). *Second Language Acquisition of Turkish*. Benjamins. (Especially Kaili et al. on TAM markers, Montrul on causative/inchoative, Uygun and Gürel on morphological processing.)
- Haznedar, B. (2006). Persistent problems with case morphology in L2 acquisition.

**Build implication: proposed structural sequence, gated by mastery.**

```
Stage 1  Copular sentences, plural -lAr, possessive suffixes
         Canonical vowel harmony, consonant assimilation (-DA/-TA)
Stage 2  Locative -DA, ablative -DAn, dative -(y)A
         Present continuous -(I)yor
Stage 3  Accusative -(y)I and DIFFERENTIAL OBJECT MARKING
         (specificity-conditioned; expect long plateau, high error rate)
Stage 4  Past -DI, future -(y)AcAK, aorist -(A/I)r
         Genitive-possessive agreement (izafet)
Stage 5  Evidential -mIş  (gate behind Stage 4 mastery; teach the
         epistemic contrast conceptually, not as "reported past")
Stage 6  Relative clauses -(y)An (subject) before -DIK (non-subject)
         Nominalizations -mA, -mAK, -DIK
Stage 7  Non-canonical word order and information structure
         (topic/focus/backgrounding; learners default to rigid SOV)
```

Two design notes:
- **Do not gate Stage 3 progression on accusative accuracy.** The research says variability here is normal and persistent even in learners with good overall proficiency. Gating on it will trap users. Track it, surface it, keep recycling it, but let them move on.
- **Suffix ordering is a system, not a list.** Turkish verbal suffix order is fixed: root - voice - negation - tense/aspect - person. Teach it as a slot template and build exercises that require assembling the template. Learners taught the ordering as a system produce more accurate complex forms than those who learn suffixes individually.

### 5.4 Other Turkish-specific items to encode

- **Final consonant devoicing and alternation**: `kitap` -> `kitabı`, `ağaç` -> `ağacı`, `renk` -> `rengi`. Encode `final_consonant_alternation` per lemma; do not let learners derive it.
- **Buffer consonants**: -y-, -n-, -s- insertion. Rule-governed and teachable explicitly.
- **Stress**: default word-final, with lexical exceptions (place names, many adverbs) and pre-stressing suffixes (-mA negation, -(I)yor, -ken, -CA). Özçelik's dissertation on Turkish stress is the reference. Pre-stressing suffixes are a discrete, learnable set and a high-value explicit rule.
- **The ğ (yumuşak g)**: not a consonant in modern standard Turkish but a lengthening/glide phenomenon. Teach through audio, not orthography.
- **Palatalized /c/, /ɟ/** before front vowels and in loanwords (`kâğıt`, `lâzım`). Low functional load, low priority.

### 5.5 Corpus and NLP tooling for Turkish

- **Morphological analysis**: Zemberek-NLP (Java, most mature), TRmorph (finite-state), Stanza and spaCy Turkish pipelines (neural, easier to integrate, less morphologically detailed)
- **Corpora**: Turkish National Corpus (Aksan et al. 2012), TS Corpus, METU-Sabancı Treebank, Universal Dependencies Turkish treebanks, OpenSubtitles for spoken register
- **Frequency reference**: Göz, İ. (2003). *Yazılı Türkçenin Kelime Sıklığı Sözlüğü*. TDK.
- **TTS/audio**: for 6-talker HVPT you need six distinct native voices. Commercial multi-speaker TTS for Turkish has improved but check whether the vowel space is naturalistic before relying on it. Recorded human tokens are safer for the perceptual training module specifically, since the whole paradigm depends on genuine talker variability.

---

## 6. Engagement, retention, and gamification

### 6.1 Gamification effects are real but modest

**Finding.** Sailer and Homner's meta-analysis found gamification effects of g = 0.49 (cognitive outcomes), g = 0.36 (motivational), and g = 0.25 (behavioral). These are small to medium. Points and badges alone perform worst; meaningful progress feedback and autonomy support perform better.

- Sailer, M., & Homner, L. (2020). The gamification of learning: A meta-analysis. *Educational Psychology Review*, 32, 77-112.
- Ryan, R. M., & Deci, E. L. (2000). Self-determination theory. *American Psychologist*, 55(1), 68-78.

**Build implication.** Streaks and XP are table stakes but they are not where the learning gains are. The evidence favors: visible competence progress tied to real capability ("you can now understand 40% of running Turkish text"), genuine choice over what to study, and difficulty calibrated to keep success rates near 80%.

### 6.2 App efficacy evidence is thin

**Finding.** Mihaylova et al.'s meta-analysis found mobile language learning app groups outperform traditional-method controls on L2 achievement, but the evidence base is heterogeneous and methodologically weak. Studies of Duolingo specifically (Jiang et al., Loewen et al.) show that learners who complete substantial coursework reach measurable proficiency, but attrition is severe and self-selection confounds the estimates. Comparative reviews rank Busuu ahead of Duolingo on study design quality, with Duolingo's higher receptive-skill numbers discounted for lack of control over study time and prior proficiency.

- Mihaylova, M., Gorin, S., Reber, T. P., & Rothen, N. (2022). A meta-analysis on mobile-assisted language learning applications: Benefits and risks. *Psychologica Belgica*, 62(1), 252-271.
- Jiang, X., Rollinson, J., Plonsky, L., Korinek, E., & Pajak, B. (2021). Evaluating the reading and listening outcomes of beginning-level Duolingo courses. *Foreign Language Annals*, 54(4), 974-1002.
- Loewen, S., et al. (2019). Mobile-assisted language learning: A Duolingo case study. *ReCALL*, 31(3), 293-311.

**Build implication.** Attrition, not instructional design, is the binding constraint on real-world app efficacy. Optimize session length for adherence. Short daily sessions with correct spacing beat long optimal sessions users skip.

### 6.3 Half-life regression as a scheduling baseline

**Finding.** Settles and Meeder's half-life regression model, developed on Duolingo data and published at ACL, models memory half-life as a log-linear function of item and learner features, and outperformed Leitner and Pimsleur baselines on recall prediction.

- Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. *ACL 2016*, 1848-1858.

**Build implication.** Start with a simple expanding-interval scheduler. Once you have review logs, HLR is a well-documented upgrade path with an open-source reference implementation. Log everything you would need: item id, user id, timestamp, lag since last review, prior correct/incorrect counts, exercise type, response latency.

---

## 7. Measurement: how to know whether Langram works

If you build only one differentiating thing, make it this. Almost no consumer app measures itself honestly.

1. **Use delayed posttests.** Li (2010) found corrective feedback effects were *larger* at delay. Immediate-only measurement will systematically misrank your features. Measure at 1 week and 1 month minimum.

2. **Subtract baseline drift.** Untrained control groups in HVPT studies gained 2.7 percentage points from testing effects and incidental exposure alone (g = 0.19), and roughly twice that in immersion contexts. If you observe a 15% gain, the true training effect may be closer to 12%.

3. **Test the dimension you claim.** Recognition tests inflate apparent vocabulary knowledge. If you claim productive knowledge, test productive recall.

4. **Match test format to training format, and be aware this inflates your numbers.** ID-training tested with ID gave g = 1.11; the same training tested with discrimination gave g = 0.80. Report both if you want an honest estimate of transfer.

5. **Use validated instruments for benchmarking.** For grammar, Ellis's (2005) battery separates implicit from explicit knowledge: timed grammaticality judgment and elicited imitation for implicit, untimed GJT and metalinguistic knowledge test for explicit. For vocabulary, adapt the Vocabulary Size Test format to your Turkish lemma frequency bands.

- Ellis, R. (2005). Measuring implicit and explicit knowledge of a second language. *Studies in Second Language Acquisition*, 27(2), 141-172.
- Plonsky, L., & Oswald, F. L. (2014). How big is "big"? Interpreting effect sizes in L2 research. *Language Learning*, 64(4), 878-912.

6. **Report effect sizes against L2 benchmarks**, not Cohen's. 0.40 small, 0.70 medium, 1.00 large.

---

## 8. Anti-patterns: what the research says not to do

| Anti-pattern | Why it fails | Source |
|---|---|---|
| Picture-based response labels in phonetic training | Splits attention between form and form-meaning mapping; halves the effect (g = 0.47 vs 1.03) | Uchihara et al. 2025 |
| Single-talker audio | Removes one of the three defining features of HVPT; harms generalization to novel talkers | Zhang et al. 2021; Uchihara et al. 2025 |
| Surface-form frequency lists for Turkish | Agglutination makes surface-form counts meaningless | Nation 2006 + Turkish morphology |
| Collapsing word knowledge to one "mastery %" | Recognition and recall dissociate; the metric becomes uninterpretable | Webb 2005 |
| Letting users permanently dismiss "known" items | Judgments of learning are poorly calibrated; users drop items too early | Karpicke 2009 |
| Long grammar explanations before practice | Explicit advantage in the literature comes from explanation *plus* practice, not explanation | Norris & Ortega 2000; Kang et al. 2019 |
| Massed practice within a single lesson only | Spaced beats massed for both vocabulary and grammar | Kim & Webb 2022 |
| Training a contrast past ~400 minutes total | Gains plateau; learner fatigue and ceiling effects | Uchihara et al. 2025 |
| Per-phoneme numeric ASR scores | Scoring reliability degrades exactly at low proficiency | Neri et al. 2008 |
| Accent reduction as a stated goal | Intelligibility and comprehensibility are the constructs that matter and respond to instruction | Levis 2005; Saito & Plonsky 2019 |
| Gating progression on accusative accuracy | Variability in Turkish accusative is normal and persistent even at high proficiency | Papadopoulou et al. 2011 |
| Immediate-posttest-only efficacy claims | Systematically misranks features; CF effects grow at delay | Li 2010 |

---

## 9. Suggested build order

1. **Scheduling engine** with per-dimension state, phase-aware intervals (1.1, 1.6, 3.6), full review logging for later HLR (6.3)
2. **Turkish lexical database**: lemmatized frequency list from TNC via Zemberek, with harmony class, final-consonant alternation, coverage contribution (2.1, 5.4)
3. **Vocabulary module** with the four knowledge dimensions and an involvement-load exercise ladder (2.4, 2.5)
4. **Grammar module** with prompt-before-correction feedback, structured input exercises, and processability-gated sequencing (3.2, 3.4, 5.3)
5. **HVPT module** to the exact parameters in 4.2, starting with /i/ vs /ɯ/ (4.1, 4.2, 5.1)
6. **Vowel space visualization** using Parselmouth formant extraction (4.5, 5.1)
7. **Measurement harness**: delayed posttests, baseline controls, effect-size reporting (7)

---

## Note on completeness

This document was pasted into a session mid-conversation and was truncated by the input's own length limit partway through section 10 (the consolidated reference list, which otherwise duplicates citations already given inline in each section above). Sections 0-9 -- the entire findings/implications/anti-patterns/build-order content -- came through complete. If a fuller reference list is needed later, ask for section 10 again specifically.
