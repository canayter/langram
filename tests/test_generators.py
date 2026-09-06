"""Generator tests.

The recurring claim across all of them is that nothing here contains a Turkish
surface form: options, distractors and answers are all produced by running the
engine. So the tests check the generators against the engine rather than against
a list of expected strings, which would just be the same claim written twice.
"""
import random

import pytest
import yaml

from langram.diagnosis import classify, feedback_for_item, normalize
from langram.generators import GenerationError, assemble, generate
from langram.generators._common import allomorphs, broken_variants, rounding_error
from langram.loader import CONTENT_ROOT, load_language
from langram.tutor import ExerciseSpec


@pytest.fixture(scope="module")
def language():
    return load_language("tr")


@pytest.fixture(scope="module")
def exercises():
    """Every exercise in the curriculum, as the tutor would present it."""
    out = []
    for path in sorted((CONTENT_ROOT / "l2" / "tr" / "curriculum").glob("unit-*.yaml")):
        with path.open(encoding="utf-8") as fh:
            unit = yaml.safe_load(fh)
        for concept in unit["concepts"]:
            for exercise in concept["exercises"]:
                out.append(ExerciseSpec(
                    id=f"{concept['id']}:{exercise['id']}",
                    concept_id=concept["id"],
                    generator=exercise["generator"],
                    stage=exercise["stage"],
                    prompt=exercise.get("prompt", ""),
                    params=exercise.get("params", {}) or {},
                    teaches_suffixes=tuple(concept.get("teaches_suffixes", []) or []),
                ))
    return out


def _spec(generator, **params):
    return ExerciseSpec(id=f"test:{generator}", concept_id="test-concept", generator=generator,
                        stage="structured_input", prompt="", params=params,
                        teaches_suffixes=("PL",))


class TestEveryExerciseInTheCurriculum:
    def test_builds_or_says_why_not(self, exercises, language):
        """Nothing fails silently. An exercise either produces an item or
        explains what it is waiting for."""
        rng = random.Random(3)
        built = deferred = 0
        for exercise in exercises:
            try:
                generate(exercise, language, rng)
                built += 1
            except GenerationError as exc:
                assert str(exc), "a deferral has to say why"
                deferred += 1
        assert built >= 20
        # Two person contrasts need audio, one register claim needs review.
        assert deferred == 3

    def test_answers_are_accepted(self, exercises, language):
        rng = random.Random(4)
        for exercise in exercises:
            for _ in range(3):
                try:
                    item = generate(exercise, language, rng)
                except GenerationError:
                    break
                assert item.accepts(item.answer, normalize), exercise.id

    def test_assemble_reproduces_the_item(self, exercises, language):
        """A review has to bring back the same item, not a similar one."""
        rng = random.Random(5)
        for exercise in exercises:
            try:
                item = generate(exercise, language, rng)
            except GenerationError:
                continue
            again = assemble(exercise, language, item.spec)
            assert again.answer == item.answer, exercise.id
            assert again.accepted == item.accepted, exercise.id
            assert again.payload == item.payload, exercise.id

    def test_no_item_leaks_its_answer(self, exercises, language):
        rng = random.Random(6)
        for exercise in exercises:
            try:
                item = generate(exercise, language, rng)
            except GenerationError:
                continue
            keys = set(item.payload)
            assert not keys & {"answer", "correct", "correct_index", "is_correct"}, exercise.id

    def test_no_item_uses_an_unreviewed_lexeme(self, exercises, language):
        """A word a native speaker has not confirmed never reaches a learner."""
        rng = random.Random(7)
        for exercise in exercises:
            for _ in range(5):
                try:
                    item = generate(exercise, language, rng)
                except GenerationError:
                    break
                if item.lemma:
                    assert not language.lexeme(item.lemma).review, item.lemma

    def test_a_predicative_exercise_never_predicates_an_unnatural_noun(self, exercises, language):
        """"biz fikriz" (we are an idea) is grammatical and nobody would say
        it; "biz doktoruz" (we are doctors) is what predicative_only exists
        to keep the pool to. Adjectives are exempt -- almost any adjective is
        a natural personal predicate -- so this only checks nouns."""
        rng = random.Random(8)
        checked = 0
        for exercise in exercises:
            if not (exercise.params.get("lexeme_filter") or {}).get("predicative_only"):
                continue
            for _ in range(8):
                try:
                    item = generate(exercise, language, rng)
                except GenerationError:
                    break
                if not item.lemma:
                    continue
                lexeme = language.lexeme(item.lemma)
                if lexeme.pos == "noun":
                    assert lexeme.predicate_natural, item.lemma
                checked += 1
        assert checked > 0, "no predicative exercise actually generated an item to check"


class TestPosIsolation:
    """A verbal suffix attached to a noun is not a distractor, it is
    nonsense ("kucuguyor"). candidate_lexemes()'s default pool has to keep
    excluding verbs, the same as it always excluded them before verbs
    existed in the lexicon at all, and an exercise that actually wants verbs
    has to ask for them explicitly."""

    def test_the_default_pool_still_excludes_verbs(self, language):
        from langram.generators._common import candidate_lexemes
        pool = candidate_lexemes(language, {})
        assert all(lx.pos in ("noun", "adjective") for lx in pool)

    def test_pos_verb_filter_returns_only_verbs(self, language):
        from langram.generators._common import candidate_lexemes
        pool = candidate_lexemes(language, {"lexeme_filter": {"pos": "verb"}})
        assert pool
        assert all(lx.pos == "verb" for lx in pool)

    def test_a_nominal_suffix_never_draws_a_verb(self, language):
        rng = random.Random(5)
        for _ in range(20):
            item = generate(_spec("form_meaning_match", highlight="last_stem_vowel", suffix="PL"),
                            language, rng)
            assert language.lexeme(item.lemma).pos != "verb", item.lemma


class TestSuffixChaining:
    """base_suffixes lets an exercise fix a prefix (gel + PROG) and vary only
    the suffix after it (+ PRED1SG), which verb person marking needs and no
    exercise before it did. chain() is the one place that assembles the
    full list inflect() receives; everything else here checks that a
    generator built for a single suffix still displays the right thing once
    a second one is chained in front of it."""

    def test_chain_prepends_the_fixed_prefix(self):
        from langram.generators._common import chain
        assert chain({}, "PRED1SG") == ["PRED1SG"]
        assert chain({"base_suffixes": ["PROG"]}, "PRED1SG") == ["PROG", "PRED1SG"]

    def test_type_the_form_produces_the_full_chain(self, language):
        rng = random.Random(1)
        spec = _spec("type_the_form", persons=["PRED1SG"], base_suffixes=["PROG"],
                     lexeme_filter={"pos": "verb"})
        item = generate(spec, language, rng)
        assert item.suffixes == ("PROG", "PRED1SG")
        assert item.answer == language.inflect(item.lemma, ["PROG", "PRED1SG"]).surface

    def test_type_the_form_names_the_last_suffix_not_the_first(self, language):
        """bekle is front-vowel, but PROG's own o governs whatever follows
        it (engine.py's harmony_back), so the person suffix shown has to be
        PRED1SG's own notation, not PROG's."""
        rng = random.Random(1)
        spec = _spec("type_the_form", persons=["PRED1SG"], base_suffixes=["PROG"],
                     lexeme_filter={"pos": "verb"})
        item = generate(spec, language, rng)
        assert item.payload["suffix"]["id"] == "PRED1SG"

    def test_cloze_shows_the_chained_stem_not_the_bare_lemma(self, language):
        """gel + PROG + ___ has to read "geliyor___" to a learner, not
        "gel___": the person suffix attaches to the inflected verb, not the
        dictionary stem."""
        rng = random.Random(1)
        spec = _spec("cloze_suffix_choice", persons=["PRED1SG", "PRED2SG"],
                     base_suffixes=["PROG"], lexeme_filter={"pos": "verb"})
        item = generate(spec, language, rng)
        base = language.inflect(item.lemma, ["PROG"]).surface
        assert item.payload["stem"] == base
        assert item.payload["stem"] != item.lemma

    def test_form_meaning_match_gloss_answers_the_person_not_the_tense(self, language):
        rng = random.Random(1)
        spec = _spec("form_meaning_match", persons=["PRED1SG", "PRED2SG"],
                     base_suffixes=["PROG"], lexeme_filter={"pos": "verb"})
        item = generate(spec, language, rng)
        assert item.answer in ("I am", "you are (singular)", "you are")


class TestSuffixBuilder:
    def test_options_are_the_real_allomorphs(self, language):
        rng = random.Random(1)
        item = generate(_spec("suffix_builder", suffix="PL"), language, rng)
        assert set(item.payload["options"]) <= set(allomorphs(language, "PL"))
        assert len(item.payload["options"]) >= 2

    def test_the_correct_option_finishes_the_word(self, language):
        rng = random.Random(2)
        item = generate(_spec("suffix_builder", suffix="POSS1SG"), language, rng)
        stem_form = language.inflect(item.lemma, list(item.suffixes)).stem_form
        correct = [o for o in item.payload["options"] if stem_form + o == item.answer]
        assert len(correct) == 1

    def test_a_bare_suffix_and_the_whole_word_both_count(self, language):
        item = generate(_spec("suffix_builder", suffix="PL"), language, random.Random(8))
        stem_form = language.inflect(item.lemma, list(item.suffixes)).stem_form
        assert item.accepts(item.answer, normalize)
        assert item.accepts(item.answer[len(stem_form):], normalize)

    def test_prog_stem_form_reflects_the_stem_vowel_deletion_not_the_bare_lemma(self, language):
        """Regression: _stem_after() did not recognise the new
        stem_vowel_deletion step, so stem_form silently froze at the bare
        lemma ("bekle") instead of the form after its own vowel was deleted
        and replaced ("bekli"). Both are the same LENGTH (one vowel swapped
        for another), so anything that only uses stem_form's length, like
        realisation() slicing a surface string, masked the bug completely.
        Anything that uses stem_form's actual characters does not: session.py
        reconstructs a bare-suffix answer as stem_form + given, and
        "bekle" + "yor" is not a Turkish word.
        """
        assert language.inflect("bekle", ["PROG"]).stem_form == "bekli"
        assert language.inflect("iste", ["PROG"]).stem_form == "isti"
        assert language.inflect("oku", ["PROG"]).stem_form == "oku"

    def test_prog_allomorphs_by_stem_shape(self, language):
        """A vowel-final verb's harmony vowel is analysed as part of the
        (alternated) stem, not the suffix -- the same treatment
        vowel_deletion nouns already get elsewhere in this engine -- so
        "yor" is the one, genuinely invariant realisation there. A
        consonant-final verb has nowhere for that vowel to go but the
        suffix, so all four harmony shapes show up as expected."""
        assert allomorphs(language, "PROG", consonant_final=False) == ["yor"]
        consonant_final = allomorphs(language, "PROG", consonant_final=True)
        assert {"iyor", "ıyor", "uyor", "üyor"} <= set(consonant_final)

    def test_prog_suffix_builder_on_a_consonant_final_verb(self, language):
        item = generate(_spec("suffix_builder", suffix="PROG",
                              lexeme_filter={"pos": "verb"}, stem_mix=["consonant_final"]),
                        language, random.Random(3))
        assert set(item.payload["options"]) == {"iyor", "ıyor", "uyor", "üyor"}
        stem_form = language.inflect(item.lemma, list(item.suffixes)).stem_form
        assert stem_form + item.answer[len(stem_form):] == item.answer


class TestMinimalPair:
    def test_one_option_is_possible_and_one_is_not(self, language):
        rng = random.Random(9)
        item = generate(_spec("minimal_pair_identification", suffix="PL",
                              distractor="wrong_harmony"), language, rng)
        options = item.payload["options"]
        assert len(options) == 2
        assert item.answer in options
        wrong = [o for o in options if o != item.answer][0]
        assert classify(language, language.lexeme(item.lemma), list(item.suffixes),
                        wrong, item.answer), "the distractor should be diagnosably wrong"

    def test_a_person_contrast_waits_for_audio(self, language):
        """Two well formed words differing only in person are readable on paper,
        so the item means nothing until there is a recording. It refuses rather
        than quietly becoming a reading task."""
        spec = _spec("minimal_pair_identification", contrast="person",
                     persons=["POSS1SG", "POSS2SG"])
        with pytest.raises(GenerationError, match="recorded talkers"):
            generate(spec, language, random.Random(10))


class TestGrammaticalityJudgement:
    def test_both_verdicts_occur(self, language):
        rng = random.Random(11)
        spec = _spec("grammaticality_judgement", suffix="PL")
        answers = {generate(spec, language, rng).answer for _ in range(20)}
        assert answers == {"yes", "no"}

    def test_a_no_item_shows_a_broken_form(self, language):
        rng = random.Random(12)
        spec = _spec("grammaticality_judgement", suffix="PL")
        for _ in range(30):
            item = generate(spec, language, rng)
            if item.answer == "no":
                shown = item.payload["form"]
                well_formed = language.inflect(item.lemma, list(item.suffixes)).surface
                assert shown != well_formed
                assert item.answer_form() == well_formed
                return
        pytest.fail("no ungrammatical item was generated")

    def _judgement(self, language, want: str):
        rng = random.Random(21)
        spec = _spec("grammaticality_judgement", suffix="PL")
        for _ in range(40):
            item = generate(spec, language, rng)
            if item.answer == want:
                return item
        pytest.fail(f"no item with answer {want} was generated")

    def test_rejecting_a_well_formed_word_is_named(self, language):
        """Two ways to be wrong, and they are different mistakes. Neither may
        come back with no tag, or the diagnostic report cannot count it."""
        item = self._judgement(language, "yes")
        result = feedback_for_item(language, item, "no", 1, correct=False)
        assert result["tags"] == ["rejected_a_good_form"]

    def test_accepting_a_broken_form_is_named(self, language):
        item = self._judgement(language, "no")
        result = feedback_for_item(language, item, "yes", 1, correct=False)
        assert "missed_the_error" in result["tags"]
        assert item.extra["broken_rule"] in result["tags"],             "the rule that was missed should be named too"

    def test_every_wrong_judgement_carries_a_tag(self, language):
        rng = random.Random(22)
        spec = _spec("grammaticality_judgement", suffix="POSS1SG")
        for _ in range(30):
            item = generate(spec, language, rng)
            wrong = "no" if item.answer == "yes" else "yes"
            for attempt in (1, 2, 3, 4):
                result = feedback_for_item(language, item, wrong, attempt, correct=False)
                assert result["tags"], f"{item.payload['form']} at attempt {attempt}"

    def test_a_register_comparison_is_not_served_yet(self, language):
        spec = _spec("grammaticality_judgement", compare=["bare_predication", "PRED3SG"])
        with pytest.raises(GenerationError, match="confirmed"):
            generate(spec, language, random.Random(13))


class TestFormMeaningMatch:
    def test_meaning_options_come_from_the_suffix_glosses(self, language):
        item = generate(_spec("form_meaning_match", cue="possessive_suffix_only"),
                        language, random.Random(14))
        assert item.payload["kind"] == "choose_meaning"
        assert item.answer in item.payload["options"]
        assert len(item.payload["options"]) >= 2

    def test_the_trigger_is_the_last_stem_vowel(self, language):
        item = generate(_spec("form_meaning_match", highlight="last_stem_vowel",
                              min_syllables=2, suffix="PL"), language, random.Random(15))
        assert item.payload["kind"] == "choose_letter"
        assert item.answer == language.phonology.last_vowel(item.payload["stem"])

    def test_a_word_whose_vowels_are_all_the_same_letter_is_never_the_trigger_choice(self, language):
        """anahtar (key) has three vowels, a, a and a: len(vowels) >= 2 passed
        the old check, but set(vowels) has one member, so the choice was
        between "a" and nothing. Every draw across many seeds must land on a
        word with at least two DIFFERENT vowels."""
        for seed in range(60):
            item = generate(_spec("form_meaning_match", highlight="last_stem_vowel",
                                  min_syllables=2, suffix="PL"), language, random.Random(seed))
            assert len(item.payload["options"]) >= 2, item.payload["stem"]

    def test_anahtar_itself_is_refused_by_assemble(self, language):
        """The fix belongs in the check itself, not only in build()'s retry:
        assemble() is reachable directly, for instance replaying a review
        card, and must refuse this word on its own."""
        from langram.generators.form_meaning_match import assemble as fmm_assemble
        with pytest.raises(GenerationError, match="no two different vowels"):
            fmm_assemble(_spec("form_meaning_match", highlight="last_stem_vowel"),
                         language, {"mode": "trigger", "lemma": "anahtar", "suffixes": ["PL"]})

    def test_the_buffer_item_marks_the_vowel_final_stem(self, language):
        item = generate(_spec("form_meaning_match", highlight="buffer_segment",
                              suffix="POSS3SG"), language, random.Random(16))
        assert item.answer in item.payload["options"]
        assert language.phonology.is_vowel(item.lemma[-1]), \
            "the stem that needed a buffer is the vowel final one"

    def test_the_buffer_item_glosses_every_option_not_just_one(self, language):
        """Three different words share this item, not three shapes of one
        word: a learner cannot judge which one needed a buffer without
        knowing what each option means, not just the one the item happens to
        track as `lemma`."""
        item = generate(_spec("form_meaning_match", highlight="buffer_segment",
                              suffix="POSS3SG"), language, random.Random(16))
        word_info = item.payload["word_info"]
        assert set(word_info) == set(item.payload["options"])
        for form, info in word_info.items():
            assert info["gloss"]
            assert info["ipa"]


class TestClozeAndProduction:
    def test_cloze_offers_suffixes_not_shapes(self, language):
        item = generate(_spec("cloze_suffix_choice", persons=["POSS1SG", "POSS2SG", "POSS3SG"]),
                        language, random.Random(17))
        assert item.payload["kind"] == "choose_suffix"
        notations = {o["notation"] for o in item.payload["options"]}
        # Archiphoneme notation, so choosing does not leak the shape.
        assert all(n.startswith("-") for n in notations)
        assert item.answer in {o["id"] for o in item.payload["options"]}

    def test_typing_is_checked_against_the_engine(self, language):
        item = generate(_spec("type_the_form", suffix="PL"), language, random.Random(18))
        assert item.payload["kind"] == "type"
        assert item.answer == language.inflect(item.lemma, list(item.suffixes)).surface
        assert item.payload["cue"], "a typing item needs an English cue"

    def test_turkish_capitals_are_forgiven(self, language):
        """Capitals should not count as a mistake, as long as they are Turkish
        capitals: the pair is i and İ, not i and I."""
        item = generate(_spec("type_the_form", suffix="PL"), language, random.Random(19))
        shouted = item.answer.replace("i", "İ").replace("ı", "I").upper()
        assert item.accepts(shouted, normalize)

    def test_dotted_and_dotless_i_stay_distinct(self, language):
        """Python uppercases i to I, which in Turkish reads as ı, a different
        phoneme. Forgiving that would undercut the distinction this app exists
        to teach, so it is not forgiven.

        Measured: about 1 in 7 draws contains i, so 20 unseeded attempts
        failed to find one about 4.5% of the time in 200 trials. 100 pushes
        that under one in a hundred thousand.
        """
        for _ in range(100):
            item = generate(_spec("type_the_form", suffix="PL"), language, random.Random())
            if "i" in item.answer:
                assert not item.accepts(item.answer.upper(), normalize)
                assert not item.accepts(item.answer.replace("i", "ı"), normalize)
                return
        pytest.fail("no answer containing i was generated")


class TestDistractors:
    def test_rounding_errors_are_real_rounding_errors(self, language):
        """Unit 2 is about rounding, so its distractors have to be rounding
        errors rather than backness errors wearing the same label."""
        lexeme = language.lexeme("doktor")
        correct = language.inflect(lexeme, ["PRED1SG"]).surface
        wrong = rounding_error(language, lexeme, ["PRED1SG"])
        assert wrong and wrong != correct
        assert classify(language, lexeme, ["PRED1SG"], wrong, correct) == ("harmony_rounding",)

    def test_every_distractor_is_diagnosable(self, language):
        for lemma in ("kitap", "araba", "doktor", "burun", "göz"):
            lexeme = language.lexeme(lemma)
            correct = language.inflect(lexeme, ["POSS1SG"]).surface
            for tag, form in broken_variants(language, lexeme, ["POSS1SG"]).items():
                assert tag in classify(language, lexeme, ["POSS1SG"], form, correct), \
                    f"{lemma}: {form} should be diagnosed as {tag}"


class TestVocabRecognition:
    def test_the_word_shown_is_the_bare_lemma_never_an_inflected_form(self, language):
        from langram.generators.vocab_recognition import OPTION_COUNT
        rng = random.Random(9)
        for _ in range(15):
            item = generate(_spec("vocab_recognition"), language, rng)
            assert item.payload["kind"] == "choose_meaning"
            assert item.payload["form"] == item.lemma
            assert len(item.payload["options"]) == OPTION_COUNT
            assert item.answer in item.payload["options"]

    def test_no_two_options_share_a_meaning(self, language):
        """A duplicate gloss among the options would make the question
        unanswerable even by someone who knows the word."""
        rng = random.Random(10)
        for _ in range(15):
            item = generate(_spec("vocab_recognition"), language, rng)
            assert len(set(item.payload["options"])) == len(item.payload["options"])

    def test_distractors_are_drawn_from_the_same_reviewed_pool_as_the_target(self, language):
        """Both the target and its distractors come from one
        candidate_lexemes() call in the generator, so this checks the
        generator draws distractors from that pool at all rather than the
        full unfiltered lexicon."""
        from langram.generators._common import candidate_lexemes
        reviewed_glosses = {lx.gloss for lx in candidate_lexemes(language, {})}
        rng = random.Random(11)
        for _ in range(15):
            item = generate(_spec("vocab_recognition"), language, rng)
            assert set(item.payload["options"]) <= reviewed_glosses


class TestExistence:
    """The first generator built on phrase.py rather than a single
    inflect() call: a possessed noun plus an invariant particle (var/yok),
    Turkish's stand-in for a verb "to have" that does not exist."""

    def _params(self):
        return {"lexeme_filter": {"pos": "noun", "possession_only": True}}

    def test_recognition_shows_the_two_word_phrase(self, language):
        rng = random.Random(1)
        for _ in range(15):
            item = generate(_spec("existence", **self._params()), language, rng)
            assert item.payload["kind"] == "choose_meaning"
            assert " " in item.payload["form"]
            assert item.payload["form"].split()[-1] in ("var", "yok")
            assert item.answer in item.payload["options"]

    def test_production_answer_is_the_turkish_phrase(self, language):
        rng = random.Random(2)
        for _ in range(15):
            item = generate(_spec("existence_production", **self._params()), language, rng)
            assert item.payload["kind"] == "type"
            assert item.answer.split()[-1] in ("var", "yok")
            assert item.accepts(item.answer, normalize)

    def test_only_possession_natural_nouns_are_drawn(self, language):
        from langram.generators._common import candidate_lexemes
        pool_lemmas = {lx.lemma for lx in candidate_lexemes(language, self._params())}
        assert pool_lemmas, "the filter should not empty the pool entirely"
        rng = random.Random(3)
        for _ in range(20):
            item = generate(_spec("existence", **self._params()), language, rng)
            assert item.lemma in pool_lemmas

    def test_negation_is_yok_never_a_suffix_on_the_noun(self, language):
        rng = random.Random(4)
        saw_yok = False
        for _ in range(20):
            item = generate(_spec("existence", **self._params()), language, rng)
            if item.extra["particle"] == "yok":
                saw_yok = True
                assert item.payload["form"].endswith(" yok")
                assert "değil" not in item.payload["form"]
        assert saw_yok, "20 draws with no yok at all is suspicious, not just unlucky"

    def test_assemble_reproduces_the_item(self, language):
        rng = random.Random(5)
        for generator in ("existence", "existence_production"):
            item = generate(_spec(generator, **self._params()), language, rng)
            again = assemble(_spec(generator, **self._params()), language, item.spec)
            assert again.answer == item.answer
            assert again.payload == item.payload
