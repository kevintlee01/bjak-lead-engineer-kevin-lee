
from app.knowledge import KnowledgeIndex, load_chunks, rank_texts_by_query


def write_md(tmp_path, filename, content):
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_load_chunks_splits_on_h2_headers(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Title\n\n"
        "## Section One\n\nContent one.\n\n"
        "## Section Two\n\nContent two.\n",
    )
    chunks = load_chunks(str(tmp_path))
    sections = {c.section for c in chunks}
    assert sections == {"Section One", "Section Two"}
    assert len(chunks) == 2


def test_preamble_before_first_header_is_folded_into_first_chunk_only(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin Lee\n\nLocation: Somewhere\n\n"
        "## Skills\n\nPython, JavaScript.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    chunks = load_chunks(str(tmp_path))
    assert len(chunks) == 2
    assert "Location: Somewhere" in chunks[0].text
    assert "Python" in chunks[0].text
    assert "Location: Somewhere" not in chunks[1].text
    assert "Best coder" in chunks[1].text


def test_source_filename_is_recorded_on_each_chunk(tmp_path):
    write_md(tmp_path, "resume.md", "# H\n\n## Section\n\nBody.\n")
    chunks = load_chunks(str(tmp_path))
    assert chunks[0].source == "resume.md"


def test_non_markdown_files_are_ignored(tmp_path):
    write_md(tmp_path, "sample.md", "# H\n\n## Section\n\nBody.\n")
    (tmp_path / "notes.txt").write_text("## Fake Section\n\nShould be ignored.\n", encoding="utf-8")
    chunks = load_chunks(str(tmp_path))
    assert len(chunks) == 1


def test_has_dates_and_is_current_flags():
    from app.knowledge import DATES_LINE

    text_current = "## Job\n\nCompany: X\nDates: Jan 2020 - Present\n\nDid things."
    match = DATES_LINE.search(text_current)
    assert match is not None
    assert "present" in match.group(1).lower()


def test_empty_knowledge_dir_produces_no_chunks(tmp_path):
    chunks = load_chunks(str(tmp_path))
    assert chunks == []


def test_search_ranks_relevant_chunk_above_unrelated_chunk(tmp_path):
    # Terms chosen to overlap only one section, avoiding TF-IDF's short-document length bias in a tiny test corpus.
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin\n\n"
        "## Technical Skills\n\nPython, JavaScript, Java, Kubernetes.\n\n"
        "## Hobbies\n\nCooking pasta and hiking on weekends.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Does he know Python and Kubernetes?", top_k=2)
    top_chunk, top_score = ranked[0]
    assert top_chunk.section == "Technical Skills"
    assert top_score > 0


def test_temporal_boost_favors_current_role_for_current_queries(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin\n\n"
        "## Employment: Engineer\n\nCompany: OldCo\nDates: Jan 2018 - Dec 2019\n\nDid legacy platform work.\n\n"
        "## Employment: Senior Engineer\n\nCompany: NewCo\nDates: Jan 2020 - Present\n\nDid legacy platform work.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Where does Kevin currently work?", top_k=1)
    assert ranked[0][0].is_current is True


def test_subjects_own_name_is_derived_as_a_stopword_across_multiple_sources(tmp_path):
    from app.knowledge import NO_SIGNAL_FLOOR_BOOST

    write_md(
        tmp_path,
        "resume.md",
        "# Zork\n\nLinkedIn: zork.example\n\n"
        "## Skills\n\nPython, JavaScript.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    write_md(tmp_path, "projects.md", "# Zork Projects\n\n## Side Project\n\nA small tool.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("What is Zork's favorite pizza topping?", top_k=1)
    # Zero lexical overlap either way; the LLM's own honesty layer declines this, not a TF-IDF hard-refuse.
    assert ranked[0][1] == NO_SIGNAL_FLOOR_BOOST


def test_who_is_subject_query_gets_a_no_signal_floor_instead_of_a_false_zero_score(tmp_path):
    # Regression test: "who is X" strips to zero tokens once stopwords and the subject's own name are removed, which used to score 0.0 everywhere and falsely refuse the most obvious question anyone could ask.
    from app.knowledge import NO_SIGNAL_FLOOR_BOOST

    write_md(
        tmp_path,
        "resume.md",
        "# Zork\n\nLinkedIn: zork.example\n\n"
        "## Skills\n\nPython, JavaScript.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    for question in ["Who is Zork?", "who is zork"]:
        ranked = index.search(question, top_k=1)
        assert ranked[0][1] == NO_SIGNAL_FLOOR_BOOST


def test_no_signal_floor_also_covers_a_real_word_that_the_corpus_never_uses(tmp_path):
    # "tell" isn't a stopword but never appears in the corpus, so it scores zero and gets the same floor as "who is X".
    write_md(
        tmp_path,
        "resume.md",
        "# Zork\n\nLinkedIn: zork.example\n\n"
        "## Skills\n\nPython, JavaScript.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    from app.knowledge import NO_SIGNAL_FLOOR_BOOST

    ranked = index.search("Tell me about Zork", top_k=1)
    assert ranked[0][1] == NO_SIGNAL_FLOOR_BOOST


def test_no_signal_floor_does_not_stack_on_top_of_a_real_match(tmp_path):
    write_md(
        tmp_path,
        "resume.md",
        "# Zork\n\n"
        "## Skills\n\nPython, JavaScript, Kubernetes.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Does Zork know Python and Kubernetes?", top_k=1)
    top_chunk, top_score = ranked[0]
    assert top_chunk.section == "Skills"
    assert 0.0 < top_score < 1.0


def test_location_boost_does_not_leak_from_folded_history_into_an_unrelated_new_topic(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Zork\n\nLocation: Metropolis\n\n"
        "## Certifications\n\nCertified widget maker, 2020.\n",
    )
    write_md(tmp_path, "other.md", "# Zork Projects\n\n## Side Project\n\nA small tool.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    folded_query = "Where is Zork? Zork is located in Metropolis. What certifications has Zork completed?"
    ranked = index.search(folded_query, top_k=1, intent_query="What certifications has Zork completed?")
    assert ranked[0][0].section == "Certifications"


def test_location_boost_surfaces_the_contact_chunk_for_where_questions(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Zork\n\nLocation: Metropolis\n\n"
        "## Skills\n\nPython, JavaScript.\n\n"
        "## Awards\n\nBest coder 2020.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Where is Zork?", top_k=1)
    assert ranked[0][0].section == "Skills"
    assert ranked[0][1] > 0.0


def test_location_boost_defers_to_temporal_cue_for_where_does_he_currently_work(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Zork\n\nLocation: Metropolis\n\n"
        "## Employment: Old Job\n\nCompany: OldCo\nDates: Jan 2018 - Dec 2019\n\nDid work.\n\n"
        "## Employment: New Job\n\nCompany: NewCo\nDates: Jan 2020 - Present\n\nDid work.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Where does Zork currently work?", top_k=1)
    assert ranked[0][0].is_current is True


def test_title_match_boost_prefers_section_whose_title_matches_query_word(tmp_path):
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin\n\n"
        "## Certifications\n\nIBM AI Certificate, Google Data Certificate.\n\n"
        "## Awards\n\nHackathon finalist, IBM AI mention in passing.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("What certifications has Kevin completed?", top_k=1)
    assert ranked[0][0].section == "Certifications"


def test_title_match_boost_recognizes_a_derivational_variant_of_the_title_word(tmp_path):
    # Regression test: "educational" and "Education" must match via stemming, not literal tokens.
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin\n\n"
        "## Education\n\nMaster of Engineering, University of Toronto.\n\n"
        "## Awards\n\nHackathon finalist.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("What is Kevin's educational background?", top_k=1)
    assert ranked[0][0].section == "Education"
    assert ranked[0][1] > 0.0


def test_real_knowledge_dir_loads_without_errors():
    """Integration-style smoke check against the actual committed knowledge/ dir."""
    chunks = load_chunks("knowledge")
    assert len(chunks) > 0
    assert any(c.source == "resume.md" for c in chunks)


def test_known_words_includes_subject_name_even_though_its_excluded_from_tfidf_vocabulary(tmp_path):
    write_md(tmp_path, "resume.md", "# Zork\n\n## Skills\n\nPython, JavaScript.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    assert "zork" in index.known_words
    assert "python" in index.known_words


def test_known_words_includes_common_english_stopwords(tmp_path):
    write_md(tmp_path, "resume.md", "# Zork\n\n## Skills\n\nPython, JavaScript.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    assert "what" in index.known_words
    assert "is" in index.known_words


def test_known_stems_recognizes_a_derivational_variant(tmp_path):
    from app.knowledge import stem

    write_md(tmp_path, "resume.md", "# Zork\n\n## Education\n\nBachelor of Science.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    assert stem("educational") in index.known_stems


def test_vectorizer_stems_so_different_word_forms_still_match(tmp_path):
    # Regression test: the vectorizer itself must stem, not just the title-boost layer.
    write_md(
        tmp_path,
        "sample.md",
        "# Kevin\n\n"
        "## Employment: Engineer\n\nManaged a team while employed at BigCo.\n\n"
        "## Awards\n\nHackathon finalist.\n",
    )
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("Did Kevin manage anyone?", top_k=1)
    assert ranked[0][0].section == "Employment: Engineer"
    assert ranked[0][1] > 0.0


def test_apostrophe_s_does_not_leave_a_stray_single_letter_token(tmp_path):
    # Regression test: "Kevin's" must not tokenize into a bare "s" that can dominate the query vector.
    from app.knowledge import NO_SIGNAL_FLOOR_BOOST

    write_md(
        tmp_path,
        "resume.md",
        "# Zork\n\nLinkedIn: zork.example\n\n"
        "## Employment: Engineer\n\nBuilt Walmart's billing system.\n\n"
        "## Awards\n\nHackathon finalist.\n",
    )
    write_md(tmp_path, "projects.md", "# Zork Projects\n\n## Side Project\n\nA small tool.\n")
    chunks = load_chunks(str(tmp_path))
    index = KnowledgeIndex(chunks)
    ranked = index.search("What is Zork's favorite pizza topping ever?", top_k=1)
    # A leaked stray "s" token would coincidentally match "Walmart's" and score nonzero; the flat floor confirms it's gone.
    assert ranked[0][1] == NO_SIGNAL_FLOOR_BOOST


def test_rank_texts_by_query_filters_below_threshold_and_orders_by_score():
    # Regression: live GitHub excerpts used to be dumped as sources with a hardcoded 1.0 score; ranking against the question keeps the "Sources" panel honest.
    texts = [
        "An autonomous AI agent framework built on LangGraph for orchestrating multi-step tasks.",
        "A two-player chess game written in Python.",
        "A CLI currency converter using a public exchange-rate API.",
        "Agentic workflow tooling that plans and executes safely.",
    ]
    ranked = rank_texts_by_query("What has Kevin built with AI agents?", texts, threshold=0.05, top_k=4)
    kept_indices = {i for i, _ in ranked}
    assert 0 in kept_indices
    assert 3 in kept_indices
    assert 1 not in kept_indices
    assert 2 not in kept_indices
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_texts_by_query_returns_empty_on_empty_input():
    assert rank_texts_by_query("anything", [], threshold=0.0) == []
