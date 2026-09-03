"""Tests for document ingestion and grounded retrieval used by SV5.

These tests do not call an LLM.  They prove that the system can read source
documents, retrieve evidence deterministically, and refuse to generate a
grounded result when evidence is absent.
"""

from pathlib import Path

import pytest

from agents.document_rag import (
    DocumentIngestionError,
    DocumentRetriever,
    extract_document_chunks,
    render_evidence_context,
    retrieve_sv5_evidence,
)


FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


def test_ingests_markdown_and_retrieves_agentic_ai_evidence():
    source = FIXTURES_DIR / "rag_agentic_ai_source.md"
    summary, citations = retrieve_sv5_evidence(
        [source],
        course_name="Agentic AI",
        clo_descriptions=["Phân tích planning action memory", "Thiết kế mini agent"],
        topics=["Khái niệm Agentic AI", "Kiến trúc multi-agent", "Mini agent"],
    )

    assert summary.source_files == [source.name]
    assert summary.chunk_count > 0
    assert summary.chunks_by_source[source.name] == summary.chunk_count
    assert summary.retrieval_strategy == "lexical_tfidf"
    assert citations
    assert any("Agentic AI" in citation.excerpt for citation in citations)
    assert {"course_summary", "weekly_schedule", "rubrics"}.issubset(
        {purpose for citation in citations for purpose in citation.used_for}
    )


def test_retriever_returns_traceable_chunk_location():
    source = FIXTURES_DIR / "rag_agentic_ai_source.md"
    retriever = DocumentRetriever.from_paths([source])

    hits = retriever.search("planning action memory feedback loop", limit=2)

    assert hits
    assert hits[0].chunk.source_file == source.name
    assert hits[0].chunk.location == "text"
    assert hits[0].chunk.chunk_id


def test_refuses_irrelevant_source_instead_of_returning_unsupported_result():
    source = FIXTURES_DIR / "rag_irrelevant_source.md"

    with pytest.raises(DocumentIngestionError, match="Không tìm thấy đoạn tài liệu liên quan"):
        retrieve_sv5_evidence(
            [source],
            course_name="Agentic AI",
            clo_descriptions=["Thiết kế mini agent", "planning action memory"],
            topics=["Agentic AI", "multi-agent"],
        )


def test_rejects_missing_and_unsupported_files(tmp_path):
    with pytest.raises(DocumentIngestionError, match="Không tìm thấy tài liệu"):
        extract_document_chunks([tmp_path / "khong_ton_tai.pdf"])

    unsupported = tmp_path / "source.csv"
    unsupported.write_text("a,b", encoding="utf-8")
    with pytest.raises(DocumentIngestionError, match="chưa được hỗ trợ"):
        extract_document_chunks([unsupported])


def test_ingests_docx_and_keeps_paragraph_location(tmp_path):
    docx = pytest.importorskip("docx")
    source = tmp_path / "agentic.docx"
    document = docx.Document()
    document.add_paragraph("Agentic AI uses planning, action and memory to reach a goal.")
    document.save(source)

    chunks = extract_document_chunks([source])

    assert chunks[0].source_file == "agentic.docx"
    assert chunks[0].location == "paragraph 1"
    assert chunks[0].page is None


def test_rendered_evidence_context_contains_source_locator():
    source = FIXTURES_DIR / "rag_agentic_ai_source.md"
    _, citations = retrieve_sv5_evidence(
        [source],
        course_name="Agentic AI",
        clo_descriptions=["Agentic AI"],
        topics=["Agentic AI"],
    )

    context = render_evidence_context(citations)

    assert source.name in context
    assert "[Nguồn:" in context
