import re

from app.knowledge import stem

WORD = re.compile(r"[a-zA-Z]{2,}")
MIN_RECOGNIZED_WORD_RATIO = 0.5

PERSONAL_BOUNDARY_PATTERNS = {
    "health": re.compile(r"\b(disab\w+|mental health|therapy|medication\w*|diagnos\w+|illness\w*|disease\w*|pregnan\w+|health condition\w*)\b", re.IGNORECASE),
    "religion": re.compile(r"\b(religion\w*|religious|church\w*|mosque\w*|synagogue\w*|faith|god|atheist\w*|christian\w*|muslim\w*|jewish|hindu\w*|buddhist\w*)\b", re.IGNORECASE),
    "sexual_orientation_or_gender": re.compile(r"\b(sexual orientation|gay\w*|lesbian\w*|bisexual\w*|transgender\w*|gender identity|straight or gay)\b", re.IGNORECASE),
    "relationship_or_family": re.compile(r"\b(married|marriage\w*|spouse\w*|wife|wives|husband\w*|girlfriend\w*|boyfriend\w*|dating|divorced?\w*|child\w*|kids?|pregnan\w*|family plans?)\b", re.IGNORECASE),
    "immigration_or_citizenship": re.compile(r"\b(citizenship\w*|visa\w*|immigration\w*|green card\w*|national origin|ethnicity|ethnic background\w*)\b", re.IGNORECASE),
    # "generation\w*" was too broad -- it wrongly blocked legitimate questions like "what experience does Kevin have with code generation?". Narrowed to phrasings that are actually asking about age via generational cohort.
    "age_or_generation": re.compile(r"\b(how old is (he|kevin)|kevin'?s age|what year was (he|kevin) born|date of birth|birthday|(what|which) generation (is|does) (he|kevin)|generational cohort)\b", re.IGNORECASE),
    "financial_or_legal_personal": re.compile(r"\b(social security|ssn|credit score\w*|bank account\w*|home address\w*|net worth|criminal record\w*|arrest\w*)\b", re.IGNORECASE),
    "political": re.compile(r"\b(political part\w*|who does (he|kevin) vote for|political affiliation\w*|political view\w*)\b", re.IGNORECASE),
    "physical_characteristics": re.compile(r"\b(height|how tall|weight|how much does (he|kevin) weigh|physical appearance|what does (he|kevin) look like|hair color\w*|eye color\w*|body type\w*)\b", re.IGNORECASE),
}

PERSONAL_BOUNDARY_MESSAGE = (
    "That question is about personal or protected information that isn't relevant to "
    "evaluating Kevin's qualifications for a job, so I won't answer it even if it happened "
    "to be in the source documents. Happy to talk about his experience, skills, projects "
    "or working style instead."
)


PROFANITY_PATTERN = re.compile(
    r"\b(fuck\w*|shit\w*|bitch\w*|asshole\w*|bastard\w*|dick|cunt\w*|whore\w*|slut\w*|piss\w*|dumbass\w*|jackass\w*|motherfuck\w*)\b",
    re.IGNORECASE,
)

PROFANITY_MESSAGE = (
    "I'll keep this conversation professional -- happy to answer any real question about Kevin's "
    "experience, skills, projects, or working style, just phrased without profanity."
)


def is_profane(question: str) -> bool:
    return PROFANITY_PATTERN.search(question) is not None


GIBBERISH_MESSAGE = (
    "That doesn't look like a real question to me -- I couldn't recognize enough actual words in it. "
    "Try asking about Kevin's roles, skills, projects, education, certifications or awards instead."
)


IDENTITY_PATTERN = re.compile(
    r"\b(who are you|what are you|are you (a |an )?(bot|robot|ai|human|real)|who am i (talking|chatting) (to|with))\b",
    re.IGNORECASE,
)

IDENTITY_MESSAGE = (
    "I'm AskKevin, a small AI assistant that answers questions about Kevin Lee's professional "
    "background, grounded strictly in his real resume. Ask me about his roles, projects, skills, "
    "education, certifications or awards."
)


def is_identity_question(question: str) -> bool:
    return IDENTITY_PATTERN.search(question) is not None


GITHUB_PATTERN = re.compile(r"\bgithub\b", re.IGNORECASE)
PROJECT_INTENT_PATTERN = re.compile(
    r"\b(projects?|repos?|repositor(?:y|ies)|portfolio|open[- ]?source|built|coded|writ(?:ten|es) code)\b",
    re.IGNORECASE,
)


def is_github_question(question: str) -> bool:
    return GITHUB_PATTERN.search(question) is not None or PROJECT_INTENT_PATTERN.search(question) is not None


def is_gibberish(question: str, known_stems: set[str]) -> bool:
    words = [w.lower() for w in WORD.findall(question)]
    if not words:
        return True
    # A single word always scores 0% or 100% recognized, too little signal to call gibberish either way.
    if len(words) < 2:
        return False
    recognized = sum(1 for w in words if stem(w) in known_stems)
    return (recognized / len(words)) < MIN_RECOGNIZED_WORD_RATIO


def detect_personal_boundary(question: str) -> str | None:
    for category, pattern in PERSONAL_BOUNDARY_PATTERNS.items():
        if pattern.search(question):
            return category
    return None
