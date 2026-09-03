# SV5 — Weekly Scheduler & Syllabus Agent

Prototype SV5 theo đề tài chính thức: nhận CLO từ SV4 và cấu trúc giáo trình từ SV3, đọc thêm PDF/DOCX bằng RAG, lập lịch 15 tuần, đề xuất Active Learning và sinh rubric có nguồn kiểm chứng.

## Kiến trúc đã chuẩn hóa

- Bên ngoài: một endpoint `POST /api/v1/agents/sv-5/execute` theo Black Box.
- Orchestrator: `SV5SchedulerAgent`, kế thừa `BaseAgent`.
- Agent con dùng LLM: Course Summary, Active Learning, Rubric.
- Document RAG: đọc PDF/DOCX/MD/TXT, chia chunk có locator, truy xuất và đưa evidence vào prompt.
- Module Python thuần: Content Sequencing và Document Assembly/Validation.
- Output contract dùng đúng tên `plo_clo_matrix` theo chuẩn SV7.
- Output có `clo_time_allocation`: tổng giờ, tỷ lệ và danh sách tuần của từng CLO.
- Khi có tài liệu, output trả thêm `document_ingestion` và `source_evidence`.

Retriever prototype dùng lexical TF-IDF/BM25-style trong bộ nhớ để dễ kiểm thử. Khi ghép repo nhóm, lớp `DocumentRetriever` là adapter để thay bằng dịch vụ RAG của SV1 (embedding + vector database) mà không đổi contract của SV5. Các bước tất định không dựng thêm CrewAI agent, phù hợp Convention 11.

## Cấu trúc

```text
PSEUDOCODE.md
agents/
  base_agent.py
  document_rag.py
  sv5_scheduler.py
tests/
  fixtures/
    sv5_valid_happy_path.json
    sv5_invalid_missing_course_info.json
    sv5_invalid_empty_clos.json
    sv5_invalid_out_of_range.json
    sv5_runtime_error_cyclic_topics.json
    sv5_rag_agentic_ai_happy_path.json
    rag_agentic_ai_source.md
    rag_irrelevant_source.md
test_sv5.py
test_document_rag.py
demo_sv5.py
demo_sv5_rag.py
demo_clo_schedule.py
input_clos_demo.json
RAG_KY_THUAT_VA_TEST.md
KICH_BAN_DEMO_CLO.md
```

## Demo offline

Demo không cần API key, dùng dữ liệu mẫu và output deterministic để thuyết trình:

```powershell
python demo_sv5.py
```

Demo trình bày cả:

1. Envelope `success`.
2. Ma trận `plo_clo_matrix`.
3. Lịch 15 tuần và hoạt động trên lớp.
4. Rubric cho attendance, assignment, final_exam.
5. Case lỗi prerequisite vòng trả `status=failed`.

## Demo đọc tài liệu thật

Cài dependency:

```powershell
python -m pip install -r requirements.txt
```

Kiểm tra hoàn toàn cục bộ, không gọi API và không gửi tài liệu ra ngoài:

```powershell
python demo_sv5_rag.py --preflight-only
```

Demo này đọc trực tiếp và phân vai nguồn:

- `AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf`: yêu cầu chính thức của đề tài/SV5.
- `BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf`: mẫu cấu trúc và cách trình bày CTĐT.
- `CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx`: dữ liệu CTĐT ngành AI.
- `AgenticAI.pdf`: tài liệu nền và nội dung demo Agentic AI.

Kết quả preflight phải hiển thị `Đọc tài liệu: PASS`, số chunk riêng cho từng nguồn và các đoạn nguồn kèm trang/vị trí.

Để chạy LLM thật, chỉ thực hiện khi được phép gửi nội dung tài liệu tới nhà cung cấp model.
Ví dụ với Gemini Free Tier (model ổn định dành cho tài khoản mới):

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_KEY"
$env:SV5_LLM_API_KEY = $env:GEMINI_API_KEY
$env:SV5_LLM_MODEL = "gemini/gemini-3.5-flash-lite"
python demo_sv5_rag.py
```

Luồng live: Document RAG → 3 CrewAI agents → Content Sequencing/Validation → response envelope có `source_evidence`.

## Demo nhập CLO và in lịch + thời lượng

Chỉ cần sửa danh sách CLO trong `input_clos_demo.json`, sau đó chạy:

```powershell
python demo_clo_schedule.py --input input_clos_demo.json
```

Output gồm:

1. CLO đầu vào và Bloom level.
2. Bằng chứng hệ thống đã đọc bốn tài liệu nguồn.
3. Kế hoạch giảng dạy đủ 15 tuần.
4. Bảng phân bổ tổng giờ, tỷ lệ và danh sách tuần theo từng CLO.
5. Tổng thời lượng phải bằng `15 × credits`; tổng tỷ lệ phải bằng 100%.

Trong demo này, presenter chỉ thay CLO. `TOPIC_CATALOGUE` là cấu trúc giáo trình sạch giả lập output của SV3, được chuẩn hóa từ `AgenticAI.pdf`. Đây đúng luồng phụ thuộc chính thức: SV5 nhận CLO từ SV4 và curriculum structure từ SV3.

Chạy ba LLM agent thật:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_KEY"
$env:SV5_LLM_API_KEY = $env:GEMINI_API_KEY
$env:SV5_LLM_MODEL = "gemini/gemini-3.5-flash-lite"
python demo_clo_schedule.py --input input_clos_demo.json --live
```

## Test

```powershell
pytest test_sv5.py test_document_rag.py -v
```

Test happy path gọi LLM thật chỉ chạy khi có `SV5_LLM_API_KEY` hoặc `OPENAI_API_KEY`. Các test schema, thuật toán, runtime error, document ingestion, retrieval, source locator và irrelevant-document rejection không cần API key.

## Giới hạn prototype cần nói rõ khi báo cáo

- `base_agent.py` hiện là bản độc lập để test; khi merge phải dùng BaseAgent chung của repo nhóm.
- Cache hiện là in-memory; production cần Redis theo Convention 5.
- Store MongoDB và router trung tâm cần được gắn vào repo nhóm theo Convention 4 và 8.
- Document Assembly hiện trả JSON; chưa tự xuất Word/PDF.
- Retriever hiện là lexical TF-IDF/BM25-style, chưa phải embedding/vector search của SV1.
- PDF scan không có text layer phải OCR trước khi ingest.
- DOCX trả locator theo paragraph/table; số trang vật lý chỉ đáng tin sau khi render.
