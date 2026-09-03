# SV5 - Kỹ thuật Document RAG và bộ test trình bày với giảng viên

## 1. Mục tiêu

SV5 không chỉ nhận dữ liệu JSON được chuẩn bị sẵn. Hệ thống có thể đọc tài liệu PDF/DOCX, tìm đoạn liên quan tới học phần/CLO/chủ đề, đưa các đoạn đó vào LLM và trả lại bằng chứng nguồn trong `SV5Output`.

Hai chế độ được tách rõ:

- `--preflight-only`: đọc và truy xuất cục bộ, tuyệt đối không gọi LLM API.
- Live LLM: gửi các đoạn đã truy xuất tới model sau khi người dùng cấu hình API key và chấp thuận việc truyền dữ liệu.

## 2. Luồng kỹ thuật

```text
PDF/DOCX/MD/TXT
      ↓
Document Parser
  - PDF: text theo trang
  - DOCX: paragraph và table row
      ↓
Chunking (900 ký tự, overlap 140)
      ↓
Lexical Retriever (TF-IDF + BM25-style saturation)
      ↓
Top-k evidence có filename + page/location + chunk_id
      ↓
Prompt grounding cho 3 LLM agent
  - Course Summary Writer
  - Active Learning Designer
  - Rubric Generator
      ↓
Content Sequencing bằng Python
  - topological sort
  - chia đủ 15 tuần
  - gán CLO theo Bloom
      ↓
Document Assembly + Pydantic validation
      ↓
SV5Output + source_evidence
```

## 3. Vì sao không giao toàn bộ cho LLM

LLM phù hợp với phần ngôn ngữ và đề xuất sư phạm, nhưng không đáng tin tuyệt đối cho các ràng buộc cứng. Vì vậy:

- LLM viết tóm tắt, Active Learning và rubric dựa trên evidence.
- Python bảo đảm prerequisite đúng thứ tự, đủ 15 tuần, CLO được bao phủ và rubric đủ ba cột.
- Nếu tài liệu không liên quan, parser lỗi, prerequisite có chu trình hoặc output LLM sai JSON, hệ thống trả `status=failed`; không tạo dữ liệu giả.

## 4. Cách retrieval được xây dựng

Mỗi tài liệu được chuyển thành `SourceChunk`:

```json
{
  "source_file": "AgenticAI.pdf",
  "chunk_id": "<document-hash>:0004",
  "page": 4,
  "location": "page 4",
  "text": "Đặc điểm của Agentic AI..."
}
```

Query được tạo từ tên môn học, mô tả CLO và danh sách chủ đề. Với từng từ khóa, retriever tính trọng số theo độ hiếm của từ trong toàn bộ corpus và mức xuất hiện trong chunk. Cụm từ khớp đầy đủ được cộng điểm. Top-k chunk được đưa vào prompt dưới dạng dữ liệu không tin cậy, kèm chỉ dẫn chống prompt injection: không thực thi mệnh lệnh nằm trong tài liệu.

Đây là retriever cục bộ có tính tất định để test được. Trong production, `DocumentRetriever` được thay bằng API của SV1 dùng embedding/vector database; phần còn lại của SV5 không đổi.

## 5. Output dùng để kiểm chứng

Khi có `context.document_paths`, output bổ sung:

```json
{
  "document_ingestion": {
    "source_files": [
      "AgenticAI.pdf",
      "AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf",
      "BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf",
      "CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx"
    ],
    "chunk_count": 1256,
    "chunks_by_source": {
      "AgenticAI.pdf": 15,
      "AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf": 14,
      "BM.QT.PDT.02.08 CTDT_HTTT (đã chỉnh).pdf": 100,
      "CHƯƠNG TRÌNH ĐÀO TẠO TRÍ TUỆ NHÂN TẠO.docx": 1127
    },
    "retrieval_strategy": "lexical_tfidf"
  },
  "source_evidence": [
    {
      "source_file": "AgenticAI.pdf",
      "page": 4,
      "location": "page 4",
      "chunk_id": "...",
      "used_for": ["course_summary", "weekly_schedule", "rubrics"]
    }
  ]
}
```

Giảng viên có thể mở đúng file và trang để so sánh với nội dung hệ thống dùng.

## 6. Test case

| Nhóm | Test case | Kỳ vọng |
|---|---|---|
| Đúng | Markdown có nội dung Agentic AI | Truy xuất được evidence và đủ ba mục đích sử dụng |
| Đúng | DOCX có paragraph liên quan | Trả đúng filename và `paragraph 1` |
| Đúng | PDF/DOCX thật của đề tài | Đọc thành công, trả trang/vị trí thật |
| Sai | Tài liệu không liên quan | Raise lỗi, không sinh kết quả không có căn cứ |
| Sai | File không tồn tại | Báo `Không tìm thấy tài liệu` |
| Sai | Định dạng CSV chưa hỗ trợ | Báo định dạng chưa hỗ trợ |
| Sai | PDF scan không có text | Báo cần OCR |
| Sai | Prerequisite vòng | Response envelope `status=failed` |
| Sai | CLO rỗng/Bloom sai | Pydantic chặn trước khi gọi LLM |
| Sai | LLM trả JSON không hợp lệ | BaseAgent trả `status=failed` |

## 7. Lệnh chạy

Preflight an toàn:

```powershell
python demo_sv5_rag.py --preflight-only
```

Toàn bộ test:

```powershell
pytest test_sv5.py test_document_rag.py -q
```

Live LLM sau khi được phép truyền tài liệu và có API key:

```powershell
$env:SV5_LLM_API_KEY = "YOUR_KEY"
python demo_sv5_rag.py
```

## 8. Kết quả đã xác minh cục bộ

- Đọc thành công đủ bốn file giảng viên cung cấp: tài liệu yêu cầu đề tài, mẫu CTĐT HTTT, CTĐT Trí tuệ nhân tạo và bài giảng Agentic AI.
- Tạo 1.256 chunk: 14 từ tài liệu đề tài, 100 từ mẫu CTĐT HTTT, 1.127 từ CTĐT Trí tuệ nhân tạo và 15 từ AgenticAI.
- Top evidence khớp các trang 4, 5 và 10 của `AgenticAI.pdf` về planning, feedback loop và multi-agent; trang 6 của tài liệu đề tài về nhiệm vụ SV5.
- Test: 29 passed, 1 skipped. Test bị skip là live LLM vì máy chưa có API key.
