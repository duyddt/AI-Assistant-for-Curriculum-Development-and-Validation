"""
tests/test_sv5.py — Bo test cho SV5 (Convention 9: >= 3 case bat buoc).

Chay: pytest tests/test_sv5.py -v
(Can dat SV5_LLM_API_KEY / OPENAI_API_KEY that de test happy-path goi CrewAI
that; cac test khac (validation, runtime, unit function) KHONG can API key
vi chung fail truoc khi cham toi buoc goi LLM.)
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.sv5_scheduler import (  # noqa: E402
    SV5SchedulerAgent, SV5Input,
    CLOItem, TopicItem, CurriculumStructure,
    topological_order_topics, distribute_topics_to_weeks,
    build_plo_clo_matrix, match_clo_by_progression,
    assign_clos_to_weeks, build_clo_time_allocation,
    validate_consistency, WeeklyScheduleItem, RubricCriterion,
    _parse_agent_json,
)

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"
HAS_LLM_KEY = bool(os.environ.get("SV5_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestAgentJsonParsing:
    def test_accepts_plain_json(self):
        result = _parse_agent_json(
            '[{"week": 1, "teaching_methods": "Thảo luận"}]',
            agent_name="Active Learning Agent",
            expected_type=list,
        )
        assert result[0]["week"] == 1

    def test_accepts_markdown_json_fence(self):
        result = _parse_agent_json(
            '```json\n{"attendance": {"criteria": []}}\n```',
            agent_name="Rubric Agent",
            expected_type=dict,
        )
        assert "attendance" in result

    def test_accepts_json_after_short_explanation(self):
        result = _parse_agent_json(
            'Kết quả đề xuất:\n[{"week": 1, "homework": "Đọc tài liệu"}]',
            agent_name="Active Learning Agent",
            expected_type=list,
        )
        assert result[0]["homework"] == "Đọc tài liệu"

    @pytest.mark.parametrize("raw", ["", "không có dữ liệu JSON"])
    def test_rejects_empty_or_non_json_output(self, raw):
        with pytest.raises(ValueError, match="phản hồi rỗng|JSON không hợp lệ"):
            _parse_agent_json(
                raw,
                agent_name="Active Learning Agent",
                expected_type=list,
            )

    def test_rejects_wrong_json_shape(self):
        with pytest.raises(ValueError, match="phải trả về list"):
            _parse_agent_json(
                '{"week": 1}',
                agent_name="Active Learning Agent",
                expected_type=list,
            )


class TestRubricScoreNormalization:
    @pytest.mark.parametrize(
        ("raw_score", "expected"),
        [
            (9, 9.0),
            ("7", 7.0),
            (">= 9", 9.0),
            ("8–10", 8.0),
            ("Dưới 6", 0.0),
        ],
    )
    def test_normalizes_common_llm_score_formats(self, raw_score, expected):
        criterion = RubricCriterion(
            level="Đạt",
            description="Mô tả",
            score=raw_score,
        )
        assert criterion.score == expected

    @pytest.mark.parametrize("raw_score", ["không xác định", -1, 11, True])
    def test_rejects_unusable_or_out_of_range_scores(self, raw_score):
        with pytest.raises(ValueError):
            RubricCriterion(
                level="Đạt",
                description="Mô tả",
                score=raw_score,
            )

# =====================================================================
# CASE 1 — HAPPY PATH (goi that qua BaseAgent.run, can LLM key)
# =====================================================================

@pytest.mark.asyncio
@pytest.mark.skipif(
    not HAS_LLM_KEY,
    reason="Bo qua test goi LLM that; can set SV5_LLM_API_KEY hoac OPENAI_API_KEY",
)
async def test_happy_path_full_pipeline():
    agent = SV5SchedulerAgent()
    request_data = load_fixture("sv5_rag_agentic_ai_happy_path.json")
    request_data["context"]["document_paths"] = [
        str(FIXTURES_DIR / "rag_agentic_ai_source.md")
    ]

    response = await agent.run(request_data)

    assert response["status"] == "success"
    assert response["errors"] == []
    data = response["data"]
    assert len(data["weekly_schedule"]) == 15
    assert data["plo_clo_matrix"]  # khong rong
    assert "attendance" in data["rubrics"]
    assert "assignment" in data["rubrics"]
    assert "final_exam" in data["rubrics"]
    assert data["validation_report"]["status"] == "PASS"
    assert data["document_ingestion"]["chunk_count"] > 0
    assert data["source_evidence"]
    assert "agentic" in data["course_summary"].lower()
    assert {"course_summary", "weekly_schedule", "rubrics"}.issubset(
        {
            purpose
            for citation in data["source_evidence"]
            for purpose in citation["used_for"]
        }
    )


# =====================================================================
# CASE 2 — VALIDATION ERROR (khong can LLM, fail ngay o BaseAgent.run)
# =====================================================================

@pytest.mark.asyncio
async def test_validation_error_missing_course_info():
    agent = SV5SchedulerAgent()
    request_data = load_fixture("sv5_invalid_missing_course_info.json")

    response = await agent.run(request_data)

    assert response["status"] == "failed"
    assert len(response["errors"]) > 0
    assert "course_info" in response["errors"][0] or "Payload" in response["errors"][0]


@pytest.mark.asyncio
async def test_validation_error_empty_clos():
    agent = SV5SchedulerAgent()
    request_data = load_fixture("sv5_invalid_empty_clos.json")

    response = await agent.run(request_data)

    assert response["status"] == "failed"
    assert len(response["errors"]) > 0


@pytest.mark.asyncio
async def test_validation_error_out_of_range_values():
    agent = SV5SchedulerAgent()
    request_data = load_fixture("sv5_invalid_out_of_range.json")

    response = await agent.run(request_data)

    assert response["status"] == "failed"
    assert len(response["errors"]) > 0


# =====================================================================
# CASE 3 — RUNTIME ERROR (schema hop le, nhung logic xu ly gap loi)
# =====================================================================

def test_runtime_error_cyclic_topics_raises():
    """Goi truc tiep ham xu ly (khong qua BaseAgent) de kiem chung
    exception dung loai va dung noi dung."""
    fixture = load_fixture("sv5_runtime_error_cyclic_topics.json")
    payload = SV5Input(**fixture["payload"])

    with pytest.raises(ValueError, match="chu trình|cyclic"):
        topological_order_topics(payload.curriculum_structure.topics)


@pytest.mark.asyncio
async def test_runtime_error_via_base_agent_returns_failed_envelope():
    """BaseAgent.run() PHAI bat exception va tra ve envelope status=failed,
    KHONG duoc de exception bay thang ra ngoai (Convention 6)."""
    agent = SV5SchedulerAgent()
    request_data = load_fixture("sv5_runtime_error_cyclic_topics.json")

    response = await agent.run(request_data)

    assert response["status"] == "failed"
    assert any("chu trình" in e or "cyclic" in e.lower() for e in response["errors"])


def test_document_rag_context_is_connected_to_sv5_agent():
    """Proves the agent consumes context.document_paths before the LLM step."""
    request_data = load_fixture("sv5_rag_agentic_ai_happy_path.json")
    payload = SV5Input(**request_data["payload"])
    source = FIXTURES_DIR / "rag_agentic_ai_source.md"

    summary, citations = SV5SchedulerAgent._retrieve_document_evidence(
        payload, {"document_paths": [str(source)]}
    )

    assert summary is not None
    assert summary.chunk_count > 0
    assert citations
    assert all(citation.source_file == source.name for citation in citations)


# =====================================================================
# UNIT TESTS cho cac ham thuan Python (khong can LLM, khong can mock)
# =====================================================================

class TestTopologicalOrdering:
    def test_orders_prerequisites_first(self):
        topics = [
            TopicItem(name="Nhập môn", prerequisites=[]),
            TopicItem(name="Cấu trúc dữ liệu", prerequisites=["Nhập môn"]),
            TopicItem(name="Giải thuật", prerequisites=["Cấu trúc dữ liệu"]),
        ]
        ordered = topological_order_topics(topics)
        assert [t.name for t in ordered] == ["Nhập môn", "Cấu trúc dữ liệu", "Giải thuật"]

    def test_raises_on_cycle(self):
        topics = [
            TopicItem(name="A", prerequisites=["B"]),
            TopicItem(name="B", prerequisites=["A"]),
        ]
        with pytest.raises(ValueError):
            topological_order_topics(topics)

    def test_independent_topics_any_order_but_all_present(self):
        topics = [
            TopicItem(name="X", prerequisites=[]),
            TopicItem(name="Y", prerequisites=[]),
        ]
        ordered = topological_order_topics(topics)
        assert {t.name for t in ordered} == {"X", "Y"}


class TestDistributeTopicsToWeeks:
    def test_more_weeks_than_topics_fills_remainder(self):
        topics = [TopicItem(name="A"), TopicItem(name="B")]
        weeks = distribute_topics_to_weeks(topics, 5)
        assert len(weeks) == 5
        assert weeks[0] == "A"
        assert weeks[1] == "B"
        assert weeks[2] == "Ôn tập / Thực hành"

    def test_more_topics_than_weeks_groups_them(self):
        topics = [TopicItem(name=f"T{i}") for i in range(6)]
        weeks = distribute_topics_to_weeks(topics, 3)
        assert len(weeks) == 3
        # 6 topics / 3 weeks -> 2 topics moi tuan
        assert "&" in weeks[0]

    def test_grouping_keeps_prerequisite_order(self):
        topics = [TopicItem(name=name) for name in ("A", "B", "C", "D")]
        weeks = distribute_topics_to_weeks(topics, 2)
        assert weeks == ["A & B", "C & D"]

    def test_raises_on_empty_topics(self):
        with pytest.raises(ValueError):
            distribute_topics_to_weeks([], 15)


class TestCloPloMatrix:
    def test_builds_matrix_from_mapped_plos(self):
        clos = [
            CLOItem(code="CLO1", description="x", bloom_level=1,
                     bloom_label="remember", mapped_plos=["PLO1"]),
            CLOItem(code="CLO2", description="y", bloom_level=3,
                     bloom_label="apply", mapped_plos=["PLO1", "PLO2"]),
        ]
        matrix = build_plo_clo_matrix(clos)
        assert matrix["PLO1"] == ["CLO1", "CLO2"]
        assert matrix["PLO2"] == ["CLO2"]

    def test_clo_without_mapped_plo_not_in_matrix(self):
        clos = [CLOItem(code="CLO1", description="x", bloom_level=1,
                         bloom_label="remember", mapped_plos=[])]
        matrix = build_plo_clo_matrix(clos)
        assert matrix == {}


class TestCloProgression:
    def test_early_week_picks_low_bloom(self):
        clos = [
            CLOItem(code="LOW", description="x", bloom_level=1, bloom_label="remember"),
            CLOItem(code="HIGH", description="y", bloom_level=6, bloom_label="create"),
        ]
        result = match_clo_by_progression(clos, week_index=1, total_weeks=15)
        assert result == ["LOW"]

    def test_late_week_picks_high_bloom(self):
        clos = [
            CLOItem(code="LOW", description="x", bloom_level=1, bloom_label="remember"),
            CLOItem(code="HIGH", description="y", bloom_level=6, bloom_label="create"),
        ]
        result = match_clo_by_progression(clos, week_index=15, total_weeks=15)
        assert result == ["HIGH"]

    def test_empty_clos_returns_empty(self):
        assert match_clo_by_progression([], 1, 15) == []

    def test_same_bloom_clos_are_balanced(self):
        clos = [
            CLOItem(code="CLO1", description="x", bloom_level=4, bloom_label="analyze"),
            CLOItem(code="CLO2", description="y", bloom_level=4, bloom_label="analyze"),
        ]
        assignments = assign_clos_to_weeks(clos, total_weeks=6)
        counts = {code: sum(code in week for week in assignments) for code in ("CLO1", "CLO2")}
        assert counts == {"CLO1": 3, "CLO2": 3}


class TestCloTimeAllocation:
    def test_total_hours_and_percent_are_preserved(self):
        clos = [
            CLOItem(code="CLO1", description="x", bloom_level=2, bloom_label="understand"),
            CLOItem(code="CLO2", description="y", bloom_level=4, bloom_label="analyze"),
        ]
        schedule = [
            WeeklyScheduleItem(
                week=1, topics="A", clos_covered=["CLO1"], hours=3,
                teaching_methods="Thảo luận", homework="",
            ),
            WeeklyScheduleItem(
                week=2, topics="B", clos_covered=["CLO1", "CLO2"], hours=3,
                teaching_methods="Case study", homework="",
            ),
        ]

        allocation = build_clo_time_allocation(schedule, clos)

        assert sum(item.total_hours for item in allocation) == 6
        assert sum(item.percentage for item in allocation) == 100
        assert allocation[0].weeks == [1, 2]
        assert allocation[1].weeks == [2]


class TestValidateConsistency:
    def test_detects_missing_week_count(self):
        schedule = [WeeklyScheduleItem(
            week=1, topics="A", clos_covered=["CLO1"],
            hours=3, teaching_methods="Thảo luận", homework="Đọc tài liệu",
        )]
        report = validate_consistency(
            schedule, [CLOItem(code="CLO1", description="x", bloom_level=1,
                                bloom_label="remember")],
            rubrics={"attendance": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]},
                     "assignment": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]},
                     "final_exam": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]}},
            total_weeks=15,
        )
        assert report.status == "FAIL"
        assert any("Số tuần" in e for e in report.errors)

    def test_detects_uncovered_clo(self):
        schedule = [WeeklyScheduleItem(
            week=i, topics="A", clos_covered=[], hours=3,
            teaching_methods="Thảo luận", homework="",
        ) for i in range(1, 16)]
        report = validate_consistency(
            schedule, [CLOItem(code="CLO1", description="x", bloom_level=1,
                                bloom_label="remember")],
            rubrics={"attendance": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]},
                     "assignment": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]},
                     "final_exam": {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]}},
            total_weeks=15,
        )
        assert report.status == "FAIL"
        assert any("CLO1" in e for e in report.errors)

    def test_passes_when_all_conditions_met(self):
        schedule = [WeeklyScheduleItem(
            week=i, topics="A", clos_covered=["CLO1"], hours=3,
            teaching_methods="Thảo luận", homework="",
        ) for i in range(1, 16)]
        rubrics = {c: {"criteria": [{"level": "Đạt", "description": "x", "score": 5}]}
                   for c in ("attendance", "assignment", "final_exam")}
        report = validate_consistency(
            schedule, [CLOItem(code="CLO1", description="x", bloom_level=1,
                                bloom_label="remember")],
            rubrics=rubrics, total_weeks=15,
        )
        assert report.status == "PASS"
        assert report.errors == []
