import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = "D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx";
const output = "D:/Mega/files/SV5-Bao-Cao-Tuan-Nay-Final.pptx";

const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const slides = presentation.slides.items;

function shape(slideNumber, index) {
  return slides[slideNumber - 1].shapes.items[index];
}

function setShape(slideNumber, index, value) {
  shape(slideNumber, index).text = value;
}

function setTable(slideNumber, values) {
  const table = slides[slideNumber - 1].tables.items[0];
  for (let r = 0; r < table.rows.length; r += 1) {
    for (let c = 0; c < 3; c += 1) {
      table.cells.set(r, c, values[r]?.[c] ?? "");
    }
  }
}

function setNotes(slideNumber, text) {
  slides[slideNumber - 1].speakerNotes.textFrame.setText(text);
  slides[slideNumber - 1].speakerNotes.setVisible(true);
}

// Slide 1 — opening claim.
setShape(1, 2, "AAIR LAB  ·  SV5 — SYLLABUS PLANNING AGENT");
setShape(1, 3, "TỪ CLO VÀ GIÁO TRÌNH\nĐẾN LỊCH 15 TUẦN + RUBRIC");
setShape(1, 4, "Thuật toán tất định · 3 agent ngôn ngữ · Envelope chuẩn");
setShape(1, 7, "Bản cập nhật: khớp yêu cầu SV5, contract của SV7 và Convention 11");
setShape(1, 8, "Demo gồm case đúng và case lỗi để chứng minh cả output lẫn error handling.");
setNotes(1, "Mở đầu: Em trình bày prototype SV5 đã thu gọn theo đúng phạm vi thầy giao. Điểm chính là hệ thống không chỉ sinh lịch 15 tuần mà còn kiểm tra được dữ liệu sai.\n\n[Sources]\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf — nhiệm vụ SV5.\n- bao_cao_sv7_chi_tiet.md — Envelope và Convention 11.");

// Slide 2 — narrative.
setShape(2, 0, "Nội dung trình bày");
setShape(2, 4, "Xác định output và contract");
setShape(2, 5, "Input từ SV3/SV4 và output JSON chuẩn");
setShape(2, 8, "Kiến trúc và thuật toán");
setShape(2, 9, "Orchestrator, 3 agent ngôn ngữ, 2 module Python");
setShape(2, 12, "Demo end-to-end");
setShape(2, 13, "Case đúng: lịch 15 tuần + rubric");
setShape(2, 16, "Case lỗi và Convention");
setShape(2, 17, "Validation, runtime error và hướng tích hợp");
setNotes(2, "Em đi theo bốn câu hỏi: hệ thống nhận gì, xử lý thế nào, output ra sao và khi input sai thì phản hồi thế nào.\n\n[Sources]\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf.");

// Slide 3 — keep the 9-section reference structure, tighten the framing.
setShape(3, 1, "Đề cương chi tiết thực tế là tiêu chí để chọn output");
setShape(3, 2, "Từ mẫu 9 mục, SV5 chọn các phần có thể tự động hóa trực tiếp trong một syllabus JSON.");
setNotes(3, "Mẫu đề cương gồm các phần thông tin chung, CLO/PLO, tóm tắt, ma trận, lịch tuần, phương pháp dạy, đánh giá và tài liệu tham khảo. SV5 tập trung vào các phần tạo ra từ CLO và giáo trình.\n\n[Sources]\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf.\n- Slide mẫu đề cương chi tiết đã được nhóm tham khảo.");

// Slide 4 — output contract.
setShape(4, 1, "Output được chốt theo contract, không phụ thuộc plo_data riêng");
setShape(4, 6, "Ma trận dùng trực tiếp clos[].mapped_plos từ SV4; contract field là plo_clo_matrix.");
setTable(4, [
  ["Dạng output", "Định dạng", "Nguồn"],
  ["general_info", "Tên, mã môn, tín chỉ", "SV5 input"],
  ["course_summary", "Đoạn tóm tắt 120–150 từ", "CLO + thông tin môn"],
  ["plo_clo_matrix", "PLO → danh sách CLO", "clos[].mapped_plos"],
  ["knowledge_matrix", "CLO → các tuần", "weekly_schedule"],
  ["weekly_schedule", "15 tuần: topic, CLO, hoạt động, homework", "SV3 + SV4"],
  ["references_list", "Tài liệu tham khảo", "SV3"],
  ["rubrics", "3 cột điểm × 4 mức", "CLO + activities"],
]);
setNotes(4, "Điểm em đã sửa so với bản trước là không yêu cầu plo_data riêng. SV4 đã cung cấp mapped_plos trong từng CLO, nên SV5 có thể tính ma trận PLO-CLO ngay.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — SV5 output dùng plo_clo_matrix.\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf — output syllabus 15 tuần và rubric.");

// Slide 5 — input/output overview.
setShape(5, 1, "Input và output của một lần chạy SV5");
setShape(5, 5, "CLOs từ SV4");
setShape(5, 6, "code, description, bloom_level, mapped_plos");
setShape(5, 8, "Curriculum từ SV3");
setShape(5, 9, "topics, prerequisites, references");
setShape(5, 12, "ENVELOPE");
setShape(5, 13, "run_id · agent_id · program_id · payload · context");
setShape(5, 14, "Không gọi trực tiếp agent khác; input/output đi qua contract và Store ở lớp tích hợp.");
setShape(5, 16, "OUTPUT — SV5Output");
setShape(5, 17, "1. general_info\n\n2. course_summary\n\n3. plo_clo_matrix\n\n4. knowledge_matrix\n\n5. weekly_schedule[15]\n\n6. references_list\n\n7. rubrics\n\n8. validation_report");
setNotes(5, "Mỗi request đi qua envelope chuẩn. Payload riêng của SV5 chỉ gồm thông tin môn, CLO và curriculum. Response có bảy nhóm output syllabus cùng validation report.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — Convention 1 và đặc tả SV5.");

// Slide 6 — nine functions, now aligned to implementation.
setShape(6, 1, "Từ output đến 9 chức năng có thể kiểm thử");
setShape(6, 6, "9 chức năng; 3 agent dùng LLM, các bước tất định dùng Python thuần theo Convention 11.");
setTable(6, [
  ["#", "Chức năng", "Output"],
  ["F1", "Sinh thông tin chung", "general_info"],
  ["F2", "Viết tóm tắt môn học", "course_summary"],
  ["F3", "Topological sort + chia 15 tuần", "weekly_schedule skeleton"],
  ["F4", "Pivot ma trận kiến thức", "knowledge_matrix"],
  ["F5", "Tính PLO-CLO từ mapped_plos", "plo_clo_matrix"],
  ["F6", "Đề xuất hoạt động và bài tập", "class_activities, homework"],
  ["F7", "Tổng hợp tài liệu tham khảo", "references_list"],
  ["F8", "Sinh rubric 3 cột điểm", "rubrics"],
  ["F9", "Merge và validate", "validation_report"],
]);
setNotes(6, "Em tách chức năng theo mức độ cần suy luận. F2, F6, F8 dùng ngôn ngữ tự nhiên nên giao agent LLM. F1, F3, F4, F5, F7, F9 là biến đổi có thể kiểm tra bằng code nên không thêm overhead CrewAI.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — Convention 11.");

// Slide 7 — honest internal components.
setShape(7, 1, "Một endpoint bên ngoài, các thành phần nội bộ rõ trách nhiệm");
setShape(7, 6, "Kết luận: 1 endpoint Black Box + 3 agent ngôn ngữ + 2 module Python tất định.");
setTable(7, [
  ["Thành phần", "Loại", "Trách nhiệm"],
  ["SV5SchedulerAgent", "Orchestrator", "Envelope, điều phối, tổng hợp, trả SV5Output"],
  ["Course Summary", "LLM agent", "Tóm tắt môn học dựa trên CLO"],
  ["Active Learning", "LLM agent", "Hoạt động trên lớp và bài tập tuần"],
  ["Rubric Generator", "LLM agent", "Rubric attendance/assignment/final_exam"],
  ["Sequencing + Assembly", "Python module", "Topological sort, merge, matrix, validation"],
]);
setNotes(7, "Ở bản này em không gọi các hàm merge và topological sort là agent LLM. Đây là cách trung thực với code và đúng Convention 11: chỉ dùng framework multi-agent khi có suy luận vai trò thực sự.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — Convention 11 Black Box Integration Pattern.");

// Slide 8 — update diagram labels without changing the inherited silhouette.
setShape(8, 1, "Luồng dữ liệu bên trong SV5");
setShape(8, 3, "CLOs\n(SV4)");
setShape(8, 5, "curriculum_structure\n(SV3)");
setShape(8, 7, "Envelope\n+ context");
setShape(8, 9, "Orchestrator\n(SV5)");
setShape(8, 11, "Content Sequencing\n(Python)");
setShape(8, 13, "Active Learning\n(LLM)");
setShape(8, 15, "Rubric Generation\n(LLM)");
setShape(8, 17, "Document Assembly\n(Python)");
setShape(8, 27, "SV5Output\n(15 tuần + rubric + validation)");
setNotes(8, "Luồng chạy thực tế trong prototype: Orchestrator validate input, sắp xếp chủ đề, gọi các task ngôn ngữ, sau đó merge và validate trước khi đóng envelope output.\n\n[Sources]\n- PSEUDOCODE.md và agents/sv5_scheduler.py trong deliverable SV5.");

// Slide 9 — orchestrator contract.
setShape(9, 1, "SV5 Scheduler Agent là điểm điều phối duy nhất");
setShape(9, 4, "Validate envelope/payload; chạy sequencing; gọi 3 task ngôn ngữ; merge, tạo ma trận và validate trước khi trả response.");
setShape(9, 7, "SV5Input\ncourse_info, clos, curriculum_structure, total_weeks");
setShape(9, 8, "Từ SV3 và SV4");
setShape(9, 9, "weeks_skeleton\n+ language outputs");
setShape(9, 10, "Kết quả trung gian nội bộ");
setShape(9, 13, "SV5Output");
setShape(9, 14, "7 nhóm output + validation_report");
setShape(9, 15, "Envelope response");
setShape(9, 16, "status, data, metadata, errors");
setShape(9, 17, "data = syllabus JSON");
setShape(9, 18, "Orchestrator không expose agent con ra ngoài");
setShape(9, 20, "Logic: validate → topological sort → 3 task ngôn ngữ → merge + matrix → validate → success/failed envelope.");
setNotes(9, "Đây là chỗ thể hiện Convention 2 và 11. Orchestrator kế thừa BaseAgent; bên ngoài chỉ thấy endpoint SV5 và response envelope, không cần biết bên trong có CrewAI hay Python thuần.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — Convention 1, 2, 8, 11.");

// Slide 10 — deterministic algorithm.
setShape(10, 1, "Content Sequencing dùng thuật toán kiểm chứng được");
setShape(10, 4, "Topological sort các topic theo prerequisite, chia thành các đoạn liên tiếp trong 15 tuần và gán CLO theo tiến trình Bloom.");
setShape(10, 7, "clos + topics + prerequisites");
setShape(10, 8, "Input đã validate theo Pydantic");
setShape(10, 9, "mapped_plos trong từng CLO");
setShape(10, 10, "Dùng trực tiếp, không cần plo_data riêng");
setShape(10, 13, "weeks_skeleton[15]");
setShape(10, 14, "topic, clos_covered, hours");
setShape(10, 15, "knowledge_matrix");
setShape(10, 16, "CLO → danh sách tuần");
setShape(10, 17, "plo_clo_matrix");
setShape(10, 18, "PLO → danh sách CLO");
setShape(10, 20, "Logic: kiểm tra prerequisite tồn tại → Kahn topological sort → chia liên tiếp, không round-robin → gán CLO → tạo 2 ma trận.");
setNotes(10, "Em đã sửa lỗi tiềm ẩn của bản trước: không chia topic theo round-robin vì có thể đưa topic C lên trước prerequisite B. Khi có chu trình hoặc prerequisite không tồn tại, thuật toán raise lỗi.\n\n[Sources]\n- PSEUDOCODE.md trong deliverable SV5.");

// Slide 11 — active learning.
setShape(11, 1, "Active Learning nối mức Bloom với hoạt động học tập");
setShape(11, 4, "Agent nhận weeks_skeleton và CLO; mỗi tuần có teaching_methods, class_activities và homework.");
setShape(11, 7, "weeks_skeleton[15] + CLO");
setShape(11, 8, "Từ Content Sequencing");
setShape(11, 11, "weeks_activities[15]");
setShape(11, 12, "teaching_methods, class_activities, homework");
setShape(11, 14, "Bloom 1–2 → thảo luận; Bloom 3–4 → case study; Bloom 5–6 → mini project.");
setNotes(11, "Phần này mới là nơi LLM tạo ngôn ngữ tự nhiên. Quy tắc chọn phương pháp vẫn được định hướng bằng Bloom để output không tách rời CLO.\n\n[Sources]\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf — yêu cầu Active Learning.\n- Bloom taxonomy — dùng trong đặc tả SV5.");

// Slide 12 — rubric.
setShape(12, 1, "Rubric được sinh theo 3 cột điểm mà thầy yêu cầu");
setShape(12, 4, "Rubric Generator nhận CLO và hoạt động đã thiết kế; mỗi cột có 4 mức đạt và mô tả gắn với CLO.");
setShape(12, 7, "clos + weeks_activities");
setShape(12, 8, "CLO và bằng chứng học tập");
setShape(12, 9, "attendance / assignment / final_exam");
setShape(12, 10, "Mỗi cột: Xuất sắc, Khá, Đạt, Chưa đạt");
setShape(12, 13, "rubrics");
setShape(12, 14, "criteria[level, description, score]");
setShape(12, 16, "Logic: nhóm CLO theo Bloom → chọn loại bằng chứng → mô tả 4 mức → validate đủ 3 cột.");
setNotes(12, "Rubric không chỉ là đoạn văn chung. Demo sẽ cho thấy đủ ba cột attendance, assignment và final_exam, mỗi cột có bốn mức.\n\n[Sources]\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf — yêu cầu rubric cho ba cột điểm.");

// Slide 13 — demo setup.
setShape(13, 0, "DEMO · MỘT INPUT, HAI KẾT QUẢ");
setShape(13, 1, "Demo offline để kiểm tra cả happy path và error path");
setShape(13, 4, "Chạy cùng pipeline với dữ liệu mẫu: một request hợp lệ và một request có prerequisite vòng.");
setShape(13, 7, "request envelope\nCLO + mapped_plos\ntopics + prerequisites");
setShape(13, 8, "JSON fixture trong tests/fixtures");
setShape(13, 9, "SV5Output\n15 tuần + rubric");
setShape(13, 10, "Case đúng: status=success");
setShape(13, 12, "error envelope");
setShape(13, 13, "cyclic dependency");
setShape(13, 14, "Case sai: status=failed + errors");
setShape(13, 15, "Không trả fallback giả");
setShape(13, 16, "Kết quả demo: PLO-CLO, lịch tuần, hoạt động, rubric và lỗi được in rõ trên terminal.");
setShape(13, 18, "python demo_sv5.py");
setNotes(13, "Chuyển sang demo. Em dùng chế độ offline để không phụ thuộc quota/API key trong lúc thuyết trình. Demo dùng cùng Pydantic schema và helper của SV5; phần LLM được thay bằng output mẫu có cấu trúc để kiểm tra pipeline.\n\n[Sources]\n- demo_sv5.py và tests/fixtures trong deliverable.");

// Slide 14 — demo success output.
setShape(14, 0, "DEMO CASE 1 · INPUT HỢP LỆ");
setShape(14, 1, "Kết quả đại diện của SV5Output");
setShape(14, 3, "Tuần");
setShape(14, 4, "Chủ đề + CLO");
setShape(14, 5, "Hoạt động");
setShape(14, 6, "Bản đầy đủ có 15 tuần; slide chỉ hiển thị 5 tuần đầu để đọc được trên màn hình.");
setTable(14, [
  ["Tuần", "Chủ đề + CLO", "Hoạt động"],
  ["1", "Giới thiệu về AI · CLO1", "Think-Pair-Share"],
  ["2", "Tìm kiếm · CLO1/CLO2", "Thảo luận nhóm"],
  ["3", "Tìm kiếm · CLO2", "Case ngắn"],
  ["4", "Học máy cơ bản · CLO3", "Case study"],
  ["5", "Học máy cơ bản · CLO3", "Bài tập tình huống"],
]);
setNotes(14, "Ở case hợp lệ, output có đủ 15 phần tử weekly_schedule. Mỗi tuần có topic, CLO, teaching_methods, class_activities và homework. Ngoài ra response có plo_clo_matrix và ba cột rubric.\n\n[Sources]\n- tests/fixtures/sv5_valid_happy_path.json.\n- demo_sv5.py.");

// Slide 15 — demo failure and conventions.
setShape(15, 1, "DEMO CASE 2 · INPUT ĐÚNG SCHEMA NHƯNG SAI LOGIC");
setShape(15, 6, "Cyclic dependency: A phụ thuộc B, B phụ thuộc A");
setShape(15, 7, "Thuật toán topological sort không thể tạo thứ tự hợp lệ");
setShape(15, 12, "ValueError: cyclic dependency");
setShape(15, 13, "Lỗi được raise tại logic");
setShape(15, 18, "BaseAgent trả envelope status=failed");
setShape(15, 19, "errors[] chứa thông báo để Orchestrator retry/DLQ ở lớp tích hợp");
setShape(15, 24, "Convention được chứng minh: schema validation, runtime error, không fallback giả");
setShape(15, 25, "Test suite: happy path · validation error · runtime error");
setNotes(15, "Case thứ hai có schema hợp lệ nhưng quan hệ prerequisite tạo chu trình. Đây là runtime error. Logic raise ValueError; BaseAgent bắt và trả status failed. Trong production, Orchestrator nhóm sẽ retry và đưa job vào DLQ theo convention.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md — Convention 6 và 9.\n- tests/fixtures/sv5_runtime_error_cyclic_topics.json.");

// Slide 16 — close with honest status and next integration step.
setShape(16, 1, "KẾT LUẬN");
setShape(16, 2, "Prototype SV5 đã khớp đề bài và contract chính");
setShape(16, 3, "Input: CLO + curriculum\nOutput: 15 tuần + hoạt động + rubric + plo_clo_matrix\nAlgorithm: topological sort, chia tuần liên tiếp, validation\nIntegration: một endpoint Black Box, BaseAgent, envelope chuẩn");
setShape(16, 5, "Bước tiếp theo sau prototype:\n1. Dùng BaseAgent/Store/Redis chung của repo nhóm.\n2. Gắn route vào router trung tâm.\n3. Nếu cần, thêm exporter Word/PDF sau khi JSON contract được chốt.");
setShape(16, 6, "Q&A — Em xin góp ý về contract và mức độ tích hợp với pipeline chung.");
setNotes(16, "Kết luận: em đã thu hẹp những gì chưa có trong code, sửa tên field theo SV7 và chuẩn bị demo có cả thành công lẫn thất bại. Phần còn lại là tích hợp hạ tầng chung của nhóm, không giấu dưới một claim rằng prototype đã production-ready.\n\n[Sources]\n- bao_cao_sv7_chi_tiet.md.\n- AI_HoTroXayDungChuongTrinhDaoTao_DeTai.pdf.");

// Imported deck contains a few connector shapes with negative extents. Keep
// their locations and normalize the bounding boxes so artifact-tool can export
// a valid PPTX while preserving the inherited diagram silhouette.
for (const slide of slides) {
  for (const item of slide.shapes.items) {
    const p = item.position;
    if (p && (p.width < 0 || p.height < 0)) {
      item.position = {
        left: p.width < 0 ? p.left + p.width : p.left,
        top: p.height < 0 ? p.top + p.height : p.top,
        width: Math.abs(p.width),
        height: Math.abs(p.height),
      };
    }
  }
}

// Clip inherited decorative circles to the slide canvas. They were designed
// to bleed past the edges in the source deck; clipping keeps the same motif
// while making QA deterministic for PowerPoint export.
slides[0].shapes.items[0].position = { left: 960, top: 0, width: 320, height: 320 };
slides[0].shapes.items[1].position = { left: 960, top: 432, width: 320, height: 288 };
slides[15].shapes.items[0].position = { left: 0, top: 432, width: 384, height: 288 };

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(output);
console.log(`Saved ${output}`);
