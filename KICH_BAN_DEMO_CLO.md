# Kịch bản demo: nhập CLO → lịch 15 tuần → thời lượng theo CLO

## Chuẩn bị

Mở hai file:

- `input_clos_demo.json`: file CLO sẽ cho thầy xem.
- Terminal tại thư mục `D:\Mega\files`.

Lệnh chạy live khuyến nghị (nhập key ẩn, không lưu key trong file):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Mega\files\run_demo_sv5.ps1"
```

## Lời nói khi bắt đầu

> “Trong demo này, em đóng vai trò đầu vào của Sinh viên 4. Em đưa danh sách CLO đã chuẩn hóa theo Bloom vào SV5. Cấu trúc chủ đề là dữ liệu sạch mà SV5 nhận từ Sinh viên 3, được chuẩn hóa từ tài liệu giảng viên cung cấp.”

Chỉ vào `input_clos_demo.json` và nói:

> “Mỗi CLO có mã, mô tả, Bloom level và PLO liên kết. Em có thể thay đổi file này mà không sửa code của agent.”

## Khi chạy Document RAG

> “Đầu tiên hệ thống đọc bốn tài liệu thầy cung cấp. Các tài liệu được chia thành chunk, sau đó retriever tìm các đoạn liên quan đến tên môn học, CLO và chủ đề. Output hiển thị filename, số trang và điểm retrieval để em có thể kiểm chứng AI đang sử dụng nguồn nào.”

> “Ở đây hệ thống tìm đúng các trang về planning, feedback loop, framework và kiến trúc multi-agent trong tài liệu AgenticAI.”

## Khi hiện lịch 15 tuần

> “Sau bước truy xuất, Content Sequencing sắp xếp chủ đề theo quan hệ prerequisite bằng Topological Sort. Kiến thức nền được đặt trước phần kiến trúc và mini project.”

> “CLO được gán theo tiến trình Bloom: những tuần đầu ưu tiên CLO mức hiểu, giữa kỳ ưu tiên phân tích, cuối kỳ ưu tiên CLO mức thiết kế và sáng tạo.”

> “Khi nhiều CLO có cùng Bloom level, thuật toán dùng số tuần đã được gán để cân bằng, tránh một CLO chiếm toàn bộ thời lượng.”

## Khi hiện bảng phân bổ thời lượng

> “Đây là phần thầy yêu cầu về ma trận phân bổ thời lượng. Mỗi tuần có ba giờ. Hệ thống cộng các giờ theo CLO và trả cả tổng giờ, tỷ lệ phần trăm và danh sách tuần.”

> “Tổng cộng môn học có 15 tuần nhân ba giờ bằng 45 giờ. Tổng thời lượng sau phân bổ vẫn bằng 45 giờ và tổng tỷ lệ bằng 100%, nên validation là PASS.”

## Phân biệt local và live LLM

> “Lệnh em vừa chạy là chế độ local: Document RAG và thuật toán ràng buộc chạy thật, không gửi tài liệu ra ngoài. Vì thế kết quả ổn định và có thể kiểm thử.”

Nếu chỉ muốn kiểm tra local, không gọi API, chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Mega\files\run_demo_sv5.ps1" -Local
```

Sau đó nói:

> “Ở chế độ live, ba CrewAI agent thật sẽ đọc context được RAG truy xuất để viết course summary, đề xuất Active Learning và sinh rubric. Phần sắp xếp tuần và tính giờ vẫn dùng Python để bảo đảm ràng buộc chính xác.”

## Nếu thầy hỏi “Chỉ đưa CLO thì chủ đề ở đâu?”

> “Theo contract chính thức, SV5 không tự nhận mỗi CLO. SV5 nhận hai nguồn: CLO từ SV4 và curriculum structure từ SV3. Trong demo, em chỉ sửa file CLO vì curriculum structure của môn Agentic AI đã được chuẩn hóa và index sẵn từ tài liệu nguồn. Như vậy demo đơn giản nhưng vẫn đúng luồng phụ thuộc của hệ thống.”
