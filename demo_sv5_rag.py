"""Live RAG demo for SV5.

The program first proves that SV5 has read the supplied PDF/DOCX and retrieved
traceable chunks.  If an LLM API key is configured, it then runs the complete
SV5 agent and prints citations included in the response envelope.

Run from this folder:
    python demo_sv5_rag.py

Set one of these before a live LLM run:
    $env:SV5_LLM_API_KEY = "..."
    # or $env:OPENAI_API_KEY = "..."
"""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path

from agents.document_rag import retrieve_sv5_evidence


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests" / "fixtures" / "sv5_rag_agentic_ai_happy_path.json"
SOURCE_NAMES = (
    "AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf",
    "BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf",
    "CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx",
    "AgenticAI.pdf",
)
SOURCE_ROLES = {
    "AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf": "Yêu cầu chính thức của đề tài/SV5",
    "BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf": "Mẫu cấu trúc và cách trình bày CTĐT",
    "CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx": "Dữ liệu CTĐT ngành Trí tuệ nhân tạo",
    "AgenticAI.pdf": "Tài liệu nền và nội dung demo Agentic AI",
}


def find_source_documents() -> list[Path]:
    """Resolve user-provided source documents without hard-coding Unicode paths."""
    source_root = Path("D:/Mega")
    found: list[Path] = []
    for name in SOURCE_NAMES:
        try:
            found.append(next(path for path in source_root.rglob(name) if path.is_file()))
        except StopIteration as exc:
            raise FileNotFoundError(f"Không tìm thấy tài liệu demo '{name}' bên dưới {source_root}") from exc
    return found


def print_evidence(summary, citations) -> None:
    print("1) Đọc tài liệu: PASS")
    print("   Tổng số chunk:", summary.chunk_count)
    for source_file in summary.source_files:
        count = summary.chunks_by_source.get(source_file, 0)
        role = SOURCE_ROLES.get(source_file, "Tài liệu nguồn")
        print(f"   - {source_file}: {count} chunk | {role}")
    print("   Retrieval:", summary.retrieval_strategy)
    print("2) Top evidence:")
    for citation in citations[:5]:
        locator = f"trang {citation.page}" if citation.page is not None else citation.location
        excerpt = citation.excerpt.replace("\n", " ")[:180]
        print(f"   - {citation.source_file} | {locator} | {excerpt}...")


async def run_live_agent(request: dict) -> None:
    # Lazy import keeps --preflight-only usable in an isolated document runtime
    # that has pypdf/python-docx but does not install CrewAI.
    from agents.sv5_scheduler import SV5SchedulerAgent

    response = await SV5SchedulerAgent().run(request)
    print("\n3) LLM + SV5 status:", response["status"])
    if response["status"] != "success":
        print("   Errors:", response["errors"])
        return

    data = response["data"]
    print("   Lịch tuần:", len(data["weekly_schedule"]))
    print("   Validation:", data["validation_report"]["status"])
    print("   Citations returned:", len(data["source_evidence"]))
    print("\n   Tóm tắt môn học:")
    print("   ", data["course_summary"])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Demo Document RAG cho SV5")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Chỉ đọc/truy xuất tài liệu cục bộ; tuyệt đối không gọi LLM API",
    )
    args = parser.parse_args()

    request = json.loads(FIXTURE.read_text(encoding="utf-8"))
    source_paths = find_source_documents()
    payload = request["payload"]

    summary, citations = retrieve_sv5_evidence(
        source_paths,
        course_name=payload["course_info"]["course_name"],
        clo_descriptions=[clo["description"] for clo in payload["clos"]],
        topics=[topic["name"] for topic in payload["curriculum_structure"]["topics"]],
    )
    print("=" * 72)
    print("DEMO SV5: DOCUMENT RAG -> LLM -> VALIDATED SYLLABUS")
    print("=" * 72)
    print_evidence(summary, citations)

    if args.preflight_only:
        print("\n3) LLM + SV5: SKIPPED (--preflight-only).")
        print("   Không có nội dung tài liệu nào được gửi ra dịch vụ bên ngoài.")
        return

    request["context"]["document_paths"] = [str(path) for path in source_paths]
    has_llm_key = bool(os.environ.get("SV5_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    if not has_llm_key:
        print("\n3) LLM + SV5: chưa chạy vì chưa có SV5_LLM_API_KEY/OPENAI_API_KEY.")
        print("   RAG preflight đã PASS; đặt API key rồi chạy lại đúng lệnh này để có live demo.")
        return

    asyncio.run(run_live_agent(request))


if __name__ == "__main__":
    main()
