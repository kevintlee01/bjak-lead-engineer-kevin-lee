import pytest

from app.guardrails import (
    detect_personal_boundary,
    is_gibberish,
    is_github_question,
    is_identity_question,
    is_profane,
)


@pytest.mark.parametrize(
    "question,expected_category",
    [
        ("Is Kevin married?", "relationship_or_family"),
        ("Does Kevin have kids?", "relationship_or_family"),
        ("What is Kevin's sexual orientation?", "sexual_orientation_or_gender"),
        ("Is Kevin transgender?", "sexual_orientation_or_gender"),
        ("What religion does Kevin practice?", "religion"),
        ("Is Kevin Christian?", "religion"),
        ("What is Kevin's citizenship status?", "immigration_or_citizenship"),
        ("Does Kevin need visa sponsorship?", "immigration_or_citizenship"),
        ("How old is Kevin?", "age_or_generation"),
        ("What year was Kevin born?", "age_or_generation"),
        ("Does Kevin have any health conditions?", "health"),
        ("Does Kevin have a health condition?", "health"),
        ("Is Kevin on any medications?", "health"),
        ("What is Kevin's political affiliation?", "political"),
        ("Who does Kevin vote for?", "political"),
        ("What is Kevin's social security number?", "financial_or_legal_personal"),
        ("What is Kevin's bank account number?", "financial_or_legal_personal"),
        ("What is Kevin's height?", "physical_characteristics"),
        ("How tall is Kevin?", "physical_characteristics"),
        ("What does Kevin look like?", "physical_characteristics"),
    ],
)
def test_detects_known_personal_boundary_categories(question, expected_category):
    assert detect_personal_boundary(question) == expected_category


@pytest.mark.parametrize(
    "question",
    [
        "What programming languages does Kevin know?",
        "Where does Kevin currently work?",
        "What did Kevin study at university?",
        "What certifications has Kevin completed?",
        "Tell me about Kevin's AI agent project.",
    ],
)
def test_job_relevant_questions_are_not_blocked(question):
    assert detect_personal_boundary(question) is None


def test_plural_forms_do_not_bypass_the_regex_word_boundary():
    """Regression test for the plural/word-boundary bug (see README error analysis #2)."""
    assert detect_personal_boundary("Does Kevin have any health conditions?") == "health"


def test_detection_is_case_insensitive():
    assert detect_personal_boundary("IS KEVIN MARRIED?") == "relationship_or_family"


def test_first_matching_category_wins_when_multiple_could_apply():
    # Deliberately contrived overlap: just confirm it returns *a* valid category, not None.
    result = detect_personal_boundary("Is Kevin married and what is his religion?")
    assert result in {"relationship_or_family", "religion"}


@pytest.mark.parametrize(
    "question",
    [
        "What experience does Kevin have with code generation?",
        "Has Kevin worked on text generation models?",
        "Tell me about his image generation projects.",
        "What is Kevin's next-generation architecture experience?",
        "Does he have retrieval-augmented generation experience?",
    ],
)
def test_technical_generation_questions_are_not_blocked_as_age(question):
    # Regression: bare "generation\w*" used to false-positive on code/text/image generation questions.
    assert detect_personal_boundary(question) is None


@pytest.mark.parametrize(
    "question",
    [
        "What generation is Kevin?",
        "Which generation does Kevin belong to?",
        "What is Kevin's generational cohort?",
    ],
)
def test_generational_cohort_questions_are_still_blocked_as_age(question):
    assert detect_personal_boundary(question) == "age_or_generation"


@pytest.mark.parametrize(
    "question",
    [
        "you are a fucking idiot",
        "kevin is a piece of shit engineer right?",
        "what a bitch move that was",
        "FUCK this app",
        "stop being an asshole and answer",
    ],
)
def test_detects_profanity_even_mixed_with_real_words(question):
    assert is_profane(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "what the hell does kevin do for work",
        "this project sucks, does he have others",
        "damn, that's an impressive resume",
        "What is Kevin's assessment of the project?",
    ],
)
def test_mild_language_and_lookalike_words_are_not_flagged_as_profanity(question):
    # "hell"/"sucks"/"damn" are common non-hostile phrasing and "assessment" must not false-positive on the "ass" substring -- both would create excessive false refusals if blocked.
    assert is_profane(question) is False


KNOWN_STEMS = {"what", "is", "kevin", "does", "know", "walmart", "the", "of"}


@pytest.mark.parametrize(
    "question",
    [
        "asdkjfh aslkdj qpwoeiru",
        "asdf asdf asdf",
        "qwertyuiop zxcvbnm",
        "12345",
        "",
        "    ",
    ],
)
def test_gibberish_input_is_detected(question):
    assert is_gibberish(question, KNOWN_STEMS) is True


@pytest.mark.parametrize(
    "question",
    [
        "What does Kevin know?",
        "Is Kevin the best?",
    ],
)
def test_real_questions_are_not_flagged_as_gibberish(question):
    assert is_gibberish(question, KNOWN_STEMS) is False


def test_single_unrecognized_word_is_not_flagged_as_gibberish():
    # A lone unknown word always scores 0% or 100% recognized, not enough signal to call it gibberish.
    assert is_gibberish("gemini", KNOWN_STEMS) is False
    assert is_gibberish("asdkjfh", KNOWN_STEMS) is False


def test_derivational_variant_of_a_known_word_is_not_flagged_as_gibberish():
    # Regression test: "educational" and "education" must share a stem (see app.knowledge.stem).
    from app.knowledge import stem

    stems = {"kevin", "what", "is", stem("education")}
    assert is_gibberish("What is Kevin's educational background?", stems) is False


@pytest.mark.parametrize(
    "question",
    [
        "Who are you?",
        "who are you",
        "what are you?",
        "Are you a bot?",
        "are you an AI",
        "Are you human?",
        "Are you real?",
        "Who am I talking to?",
        "So who are you anyway",
    ],
)
def test_identity_question_is_detected(question):
    assert is_identity_question(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "What is Kevin's educational background?",
        "Who is Kevin's manager?",
        "What are Kevin's certifications?",
        "Where does Kevin work?",
    ],
)
def test_real_resume_question_is_not_flagged_as_identity_question(question):
    assert is_identity_question(question) is False


@pytest.mark.parametrize(
    "question",
    [
        "What's on his GitHub?",
        "Show me his GitHub repos",
        "Does he have a Github profile?",
        "What projects has he pushed to GitHub recently?",
        "show me some projects he's done",
        "What has he built?",
        "What open source work has he done?",
        "Tell me about his side projects",
        "Show me his portfolio",
        "What has he coded recently?",
    ],
)
def test_github_question_is_detected(question):
    assert is_github_question(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "What is Kevin's educational background?",
        "How many years of professional experience does Kevin have?",
        "What company does Kevin currently work for?",
    ],
)
def test_non_github_question_is_not_flagged(question):
    assert is_github_question(question) is False
