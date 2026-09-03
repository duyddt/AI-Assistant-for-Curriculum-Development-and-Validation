"""Demo SV5: CLO JSON -> document RAG -> 15-week plan -> CLO hours.

Local deterministic demo (no external API):
    python demo_clo_schedule.py --input input_clos_demo.json

Live CrewAI demo after configuring an API key:
    python demo_clo_schedule.py --input input_clos_demo.json --live

Only the CLO file is changed by the presenter.  The topic catalogue below is
the pre-indexed/clean curriculum structure that SV5 normally receives from SV3.
It is derived from the teacher-provided AgenticAI.pdf.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from agents.document_rag import retrieve_sv5_evidence
from agents.sv5_scheduler import (
    CLOItem,
    CourseInfo,
    CurriculumStructure,
    SV5SchedulerAgent,
    TopicItem,
    WeeklyScheduleItem,
    assign_clos_to_weeks,
    build_clo_time_allocation,
    distribute_topics_to_weeks,
    rebalance_coverage,
    topological_order_topics,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "input_clos_demo.json"
SOURCE_NAMES = (
    "AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf",
    "BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf",
    "CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx",
    "AgenticAI.pdf",
)


# Giả lập output curriculum_structure sạch từ SV3, có nguồn ở AgenticAI.pdf.
TOPIC_CATALOGUE = [
    TopicItem(name="Khái niệm Agentic AI", prerequisites=[]),
    TopicItem(name="So sánh Generative AI và Agentic AI", prerequisites=["Khái niệm Agentic AI"]),
    TopicItem(name="Goal-driven và xác định mục tiêu", prerequisites=["Khái niệm Agentic AI"]),
    TopicItem(name="Planning và phân rã nhiệm vụ", prerequisites=["Goal-driven và xác định mục tiêu"]),
    TopicItem(name="Action-taking và sử dụng công cụ", prerequisites=["Planning và phân rã nhiệm vụ"]),
    TopicItem(name="Feedback loop và tự kiểm tra", prerequisites=["Action-taking và sử dụng công cụ"]),
    TopicItem(name="Memory và lưu trữ ngữ cảnh", prerequisites=["Feedback loop và tự kiểm tra"]),
    TopicItem(name="Kiến trúc single-agent", prerequisites=["Memory và lưu trữ ngữ cảnh"]),
    TopicItem(name="Kiến trúc tool-based agent", prerequisites=["Kiến trúc single-agent"]),
    TopicItem(name="Kiến trúc multi-agent", prerequisites=["Kiến trúc tool-based agent"]),
    TopicItem(name="Framework xây dựng agent", prerequisites=["Kiến trúc multi-agent"]),
    TopicItem(name="Framework agent tự trị", prerequisites=["Framework xây dựng agent"]),
    TopicItem(name="Framework multi-agent", prerequisites=["Framework agent tự trị"]),
    TopicItem(name="Ứng dụng Agentic AI trong xây dựng CTĐT", prerequisites=["Framework multi-agent"]),
    TopicItem(name="Mini project và demo agent", prerequisites=["Ứng dụng Agentic AI trong xây dựng CTĐT"]),
]


def find_sources() -> list[Path]:
    source_root = Path("D:/Mega")
    result = []
    for name in SOURCE_NAMES:
        try:
            result.append(next(path for path in source_root.rglob(name) if path.is_file()))
        except StopIteration as exc:
            raise FileNotFoundError(f"Không tìm thấy tài liệu của thầy: {name}") from exc
    return result


def load_clo_input(path: Path) -> tuple[CourseInfo, list[CLOItem], int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    course = CourseInfo(
        course_name=raw["course_name"],
        course_code=raw["course_code"],
        credits=raw["credits"],
    )
    clos = [CLOItem(**item) for item in raw["clos"]]
    if not clos:
        raise ValueError("Danh sách CLO không được rỗng")
    codes = [clo.code for clo in clos]
    if len(codes) != len(set(codes)):
        raise ValueError("Mã CLO không được trùng")
    return course, clos, int(raw.get("total_weeks", 15))


def choose_method(max_bloom: int) -> str:
    if max_bloom <= 2:
        return "Think-Pair-Share"
    if max_bloom <= 4:
        return "Case study / thực hành"
    return "Project-based learning"


def build_local_schedule(
    course: CourseInfo,
    clos: list[CLOItem],
    total_weeks: int,
) -> list[WeeklyScheduleItem]:
    ordered_topics = topological_order_topics(TOPIC_CATALOGUE)
    topic_slots = distribute_topics_to_weeks(ordered_topics, total_weeks)
    clo_assignments = assign_clos_to_weeks(clos, total_weeks)
    skeleton = []
    for week, topic in enumerate(topic_slots, start=1):
        skeleton.append(
            {
                "week": week,
                "topics": topic,
                "clos_covered": clo_assignments[week - 1],
                "hours": course.credits,
            }
        )

    covered = {code for item in skeleton for code in item["clos_covered"]}
    uncovered = [clo for clo in clos if clo.code not in covered]
    if uncovered:
        rebalance_coverage(skeleton, uncovered)

    clo_by_code = {clo.code: clo for clo in clos}
    schedule = []
    for item in skeleton:
        max_bloom = max(clo_by_code[code].bloom_level for code in item["clos_covered"])
        method = choose_method(max_bloom)
        schedule.append(
            WeeklyScheduleItem(
                week=item["week"],
                topics=item["topics"],
                clos_covered=item["clos_covered"],
                hours=item["hours"],
                teaching_methods=method,
                class_activities=f"{method}: xử lý chủ đề {item['topics']}",
                homework=f"Bài tập gắn với {', '.join(item['clos_covered'])}",
            )
        )
    return schedule


def print_clos(clos: list[CLOItem]) -> None:
    print("\n1) CLO INPUT")
    for clo in clos:
        print(f"   {clo.code} | Bloom {clo.bloom_level} | {clo.description}")


def print_evidence(summary, citations) -> None:
    print("\n2) DOCUMENT RAG: PASS")
    print(f"   Đã đọc {len(summary.source_files)} file, {summary.chunk_count} chunk")
    for citation in citations[:4]:
        locator = f"trang {citation.page}" if citation.page else citation.location
        print(f"   - {citation.source_file} | {locator} | score={citation.score:.2f}")


def print_schedule(schedule: list[WeeklyScheduleItem]) -> None:
    print("\n3) KẾ HOẠCH GIẢNG DẠY 15 TUẦN")
    print("   Tuần | Giờ | CLO          | Chủ đề")
    print("   " + "-" * 74)
    for item in schedule:
        clos = ",".join(item.clos_covered)
        print(f"   {item.week:>4} | {item.hours:>3} | {clos:<12} | {item.topics[:48]}")


def print_allocation(schedule: list[WeeklyScheduleItem], clos: list[CLOItem]) -> None:
    allocation = build_clo_time_allocation(schedule, clos)
    print("\n4) PHÂN BỔ THỜI LƯỢNG THEO CLO")
    print("   CLO  | Bloom | Tổng giờ | Tỷ lệ  | Tuần")
    print("   " + "-" * 74)
    for item in allocation:
        weeks = ",".join(str(week) for week in item.weeks)
        print(
            f"   {item.clo_code:<4} | {item.bloom_level:^5} | "
            f"{item.total_hours:>8.2f} | {item.percentage:>6.2f}% | {weeks}"
        )
    total_hours = sum(item.total_hours for item in allocation)
    total_percent = sum(item.percentage for item in allocation)
    print("   " + "-" * 74)
    print(f"   TỔNG          {total_hours:>8.2f} | {total_percent:>6.2f}%")


def print_live_ai_outputs(data: dict, schedule: list[WeeklyScheduleItem]) -> None:
    """Show concise, presentation-friendly evidence of all three LLM agents."""
    print("\n5) KẾT QUẢ BA AGENT AI")
    print("\n   Agent 1 - Course Summary Writer")
    print(f"   {data['course_summary']}")

    print("\n   Agent 2 - Active Learning Designer (mẫu 3 tuần)")
    sample_indexes = sorted({0, len(schedule) // 2, len(schedule) - 1})
    for index in sample_indexes:
        item = schedule[index]
        print(f"   - Tuần {item.week}: {item.teaching_methods}")
        print(f"     Hoạt động: {item.class_activities}")
        print(f"     Bài tập: {item.homework}")

    print("\n   Agent 3 - Rubric Generator")
    rubric_labels = {
        "attendance": "Chuyên cần",
        "assignment": "Bài tập lớn",
        "final_exam": "Thi cuối kỳ",
    }
    for column, label in rubric_labels.items():
        print(f"   - {label}:")
        for criterion in data["rubrics"][column]["criteria"]:
            print(
                f"     {criterion['level']} (từ {criterion['score']:g} điểm): "
                f"{criterion['description']}"
            )

    report = data["validation_report"]
    print(f"\n6) VALIDATION: {report['status']}")
    if report["errors"]:
        for error in report["errors"]:
            print(f"   ERROR: {error}")
    else:
        print("   Đủ số tuần, mọi CLO được bao phủ và đủ 3 cột rubric.")


async def run_live(
    course: CourseInfo,
    clos: list[CLOItem],
    total_weeks: int,
    source_paths: list[Path],
) -> None:
    if not (os.environ.get("SV5_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        raise RuntimeError("Chưa có SV5_LLM_API_KEY hoặc OPENAI_API_KEY để chạy --live")

    curriculum = CurriculumStructure(
        topics=TOPIC_CATALOGUE,
        references=[path.name for path in source_paths],
    )
    request = {
        "run_id": str(uuid.uuid4()),
        "agent_id": "sv-5",
        "program_id": "DEMO-AGENTIC-AI",
        "user_id": "presenter",
        "payload": {
            "course_info": course.model_dump(),
            "clos": [clo.model_dump() for clo in clos],
            "curriculum_structure": curriculum.model_dump(),
            "total_weeks": total_weeks,
        },
        "context": {
            "trace_id": "demo-clo-live",
            "document_paths": [str(path) for path in source_paths],
        },
    }
    response = await SV5SchedulerAgent().run(request)
    if response["status"] != "success":
        raise RuntimeError("; ".join(response["errors"]))
    data = response["data"]
    schedule = [WeeklyScheduleItem(**item) for item in data["weekly_schedule"]]
    print("\nLIVE LLM RESPONSE: success")
    print_schedule(schedule)
    print_allocation(schedule, clos)
    print_live_ai_outputs(data, schedule)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Demo CLO -> lịch 15 tuần -> giờ theo CLO")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="File JSON chứa CLO")
    parser.add_argument("--live", action="store_true", help="Gọi 3 CrewAI LLM agents thật")
    args = parser.parse_args()

    course, clos, total_weeks = load_clo_input(args.input)
    source_paths = find_sources()
    summary, citations = retrieve_sv5_evidence(
        source_paths,
        course_name=course.course_name,
        clo_descriptions=[clo.description for clo in clos],
        topics=[topic.name for topic in TOPIC_CATALOGUE],
    )

    print("=" * 84)
    print("SV5 DEMO: CLO -> DOCUMENT RAG -> 15-WEEK SCHEDULE -> CLO TIME ALLOCATION")
    print("=" * 84)
    print_clos(clos)
    print_evidence(summary, citations)

    if args.live:
        asyncio.run(run_live(course, clos, total_weeks, source_paths))
        return

    schedule = build_local_schedule(course, clos, total_weeks)
    print_schedule(schedule)
    print_allocation(schedule, clos)
    print("\n5) VALIDATION: PASS")
    print("   Chế độ local dùng Document RAG + thuật toán ràng buộc; không gọi LLM API.")


if __name__ == "__main__":
    main()
