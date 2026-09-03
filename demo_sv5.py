"""Demo offline cho SV5 - không cần API key.

Mục tiêu của demo là cho thấy đúng pipeline của SV5:
Envelope chuẩn -> kiểm tra input -> topological sort -> 15 tuần
-> Active Learning/Rubric mẫu -> ma trận PLO-CLO -> kết quả hoặc lỗi.

Chạy:
    python demo_sv5.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from agents.sv5_scheduler import (
    SV5Input,
    WeeklyScheduleItem,
    build_clo_time_allocation,
    build_plo_clo_matrix,
    distribute_topics_to_weeks,
    merge_weeks,
    topological_order_topics,
    validate_consistency,
)


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests" / "fixtures" / "sv5_valid_happy_path.json"
CYCLIC_FIXTURE = ROOT / "tests" / "fixtures" / "sv5_runtime_error_cyclic_topics.json"


def envelope(request: dict[str, Any], status: str, data: Any = None, errors=None) -> dict[str, Any]:
    return {
        "run_id": request.get("run_id", "demo-run"),
        "agent_id": request.get("agent_id", "sv-5"),
        "status": status,
        "data": data,
        "metadata": {"model": "offline-demo", "cached": False},
        "errors": errors or [],
    }


def choose_method(max_bloom: int) -> str:
    if max_bloom <= 2:
        return "Think-Pair-Share / thảo luận nhóm"
    if max_bloom <= 4:
        return "Case study / bài tập tình huống"
    return "Project-based learning / mini project"


def build_offline_success(request: dict[str, Any]) -> dict[str, Any]:
    payload = SV5Input(**request["payload"])
    ordered = topological_order_topics(payload.curriculum_structure.topics)
    topic_slots = distribute_topics_to_weeks(ordered, payload.total_weeks)

    weeks_skeleton = []
    for week, topics in enumerate(topic_slots, start=1):
        clos = payload.clos[:]
        target = min(6, max(1, round(week / payload.total_weeks * 6)))
        selected = min(clos, key=lambda item: abs(item.bloom_level - target))
        weeks_skeleton.append({
            "week": week,
            "topics": topics,
            "clos_covered": [selected.code],
            "hours": payload.course_info.credits,
        })

    covered = {code for week in weeks_skeleton for code in week["clos_covered"]}
    for index, clo in enumerate(payload.clos):
        if clo.code not in covered:
            weeks_skeleton[index % len(weeks_skeleton)]["clos_covered"].append(clo.code)

    activities = []
    for week in weeks_skeleton:
        related = [c for c in payload.clos if c.code in week["clos_covered"]]
        max_bloom = max((c.bloom_level for c in related), default=1)
        method = choose_method(max_bloom)
        activities.append({
            "week": week["week"],
            "teaching_methods": method,
            "class_activities": f"{method}; phân tích chủ đề: {week['topics']}",
            "homework": f"Bài tập ngắn gắn với {', '.join(week['clos_covered'])}.",
        })

    rubrics = {
        "attendance": {"criteria": [
            {"level": "Xuất sắc", "description": "Tham gia đầy đủ, đóng góp chủ động", "score": 10},
            {"level": "Khá", "description": "Tham gia và hoàn thành phần lớn hoạt động", "score": 8},
            {"level": "Đạt", "description": "Có tham gia nhưng đóng góp chưa đều", "score": 6},
            {"level": "Chưa đạt", "description": "Ít tham gia hoặc vắng không lý do", "score": 4},
        ]},
        "assignment": {"criteria": [
            {"level": "Xuất sắc", "description": "Vận dụng đúng, giải thích được lựa chọn", "score": 10},
            {"level": "Khá", "description": "Hoàn thành đúng yêu cầu, còn lỗi nhỏ", "score": 8},
            {"level": "Đạt", "description": "Đạt phần cốt lõi của bài tập", "score": 6},
            {"level": "Chưa đạt", "description": "Thiếu phần quan trọng hoặc sai logic", "score": 4},
        ]},
        "final_exam": {"criteria": [
            {"level": "Xuất sắc", "description": "Phân tích và thiết kế giải pháp có lập luận", "score": 10},
            {"level": "Khá", "description": "Giải quyết đúng phần lớn yêu cầu", "score": 8},
            {"level": "Đạt", "description": "Nắm được kiến thức nền và áp dụng cơ bản", "score": 6},
            {"level": "Chưa đạt", "description": "Chưa đạt chuẩn đầu ra tối thiểu", "score": 4},
        ]},
    }

    weekly_schedule = merge_weeks(weeks_skeleton, activities)
    report = validate_consistency(weekly_schedule, payload.clos, rubrics, payload.total_weeks)
    if report.status == "FAIL":
        raise ValueError("Validation thất bại: " + "; ".join(report.errors))

    data = {
        "general_info": {
            "course_name": payload.course_info.course_name,
            "course_code": payload.course_info.course_code,
            "credits": payload.course_info.credits,
        },
        "course_summary": (
            "Môn học giới thiệu nền tảng của trí tuệ nhân tạo, từ cách biểu diễn bài toán "
            "và tìm kiếm đến học máy và ứng dụng thực tế. Người học được rèn luyện khả năng "
            "giải thích khái niệm, lựa chọn thuật toán, đánh giá kết quả và thiết kế một giải pháp "
            "AI nhỏ. Lộ trình 15 tuần sắp xếp kiến thức theo quan hệ tiên quyết, kết hợp thảo luận, "
            "tình huống và mini project để gắn hoạt động học tập với CLO và PLO."
        ),
        "plo_clo_matrix": build_plo_clo_matrix(payload.clos),
        "clo_time_allocation": [
            item.model_dump()
            for item in build_clo_time_allocation(weekly_schedule, payload.clos)
        ],
        "weekly_schedule": [item.model_dump() for item in weekly_schedule],
        "rubrics": rubrics,
        "references_list": payload.curriculum_structure.references,
        "validation_report": report.model_dump(),
    }
    return envelope(request, "success", data)


def build_offline_failure(request: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = SV5Input(**request["payload"])
        topological_order_topics(payload.curriculum_structure.topics)
    except Exception as exc:  # BaseAgent sẽ thực hiện việc này trong production
        return envelope(request, "failed", errors=[str(exc)])
    return envelope(request, "failed", errors=["Demo failure case không phát hiện được lỗi"])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    request = json.loads(FIXTURE.read_text(encoding="utf-8"))
    success = build_offline_success(request)
    data = success["data"]

    print("=" * 72)
    print("DEMO SV5 - SYLLABUS PLANNING AGENT (OFFLINE)")
    print("=" * 72)
    print("1) Envelope status:", success["status"])
    print("2) PLO-CLO matrix:", json.dumps(data["plo_clo_matrix"], ensure_ascii=False))
    print("3) Lịch 15 tuần:")
    for item in data["weekly_schedule"]:
        print(
            f"   Tuần {item['week']:>2}: {item['topics']:<34} "
            f"| {', '.join(item['clos_covered'])} | {item['teaching_methods']}"
        )
    print("4) Rubric:", ", ".join(data["rubrics"]))
    print(
        "5) CLO time allocation:",
        ", ".join(
            f"{item['clo_code']}={item['total_hours']}h"
            for item in data["clo_time_allocation"]
        ),
    )
    print("6) Validation:", data["validation_report"]["status"])

    cyclic_request = json.loads(CYCLIC_FIXTURE.read_text(encoding="utf-8"))
    failure = build_offline_failure(cyclic_request)
    print("\n7) Case lỗi prerequisite vòng:")
    print(json.dumps(failure, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
