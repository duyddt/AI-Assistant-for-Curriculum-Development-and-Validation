# SV5 — Pseudocode chuẩn hóa

## 1. Phạm vi và kiến trúc

SV5 nhận `clos` từ SV4 và `curriculum_structure` từ SV3. Bên ngoài chỉ expose một endpoint:

```text
POST /api/v1/agents/sv-5/execute
```

Bên trong có:

- `SV5SchedulerAgent`: Orchestrator, kế thừa `BaseAgent`.
- `Course Summary Agent`: dùng LLM để viết tóm tắt môn học.
- `Active Learning Agent`: dùng LLM để đề xuất hoạt động và bài tập.
- `Rubric Agent`: dùng LLM để sinh rubric.
- `Document RAG Module`: đọc PDF/DOCX/MD/TXT, chunking và truy xuất evidence có locator.
- `Content Sequencing Module`: Python thuần, topological sort và chia tuần.
- `Document Assembly Module`: Python thuần, merge và validate.

Các module Python thuần không được gọi là LLM agent vì đây là các phép biến đổi tất định. Cách tách này phù hợp Convention 11 của Ngọc Thành.

## 2. Document RAG Module

```text
FUNCTION ingest_documents(document_paths):
    IF document_paths rỗng:
        RAISE DocumentIngestionError

    chunks ← []
    FOR path IN document_paths:
        IF path là PDF:
            units ← extract_text_by_page(path)
        ELSE IF path là DOCX:
            units ← extract_paragraphs_and_table_rows(path)
        ELSE IF path là MD hoặc TXT:
            units ← read_utf8_text(path)
        ELSE:
            RAISE DocumentIngestionError("unsupported format")

        FOR unit IN units:
            chunks.ADD(split(unit.text, size=900, overlap=140), unit.locator)

    IF chunks rỗng:
        RAISE DocumentIngestionError("không trích xuất được văn bản")
    RETURN chunks

FUNCTION retrieve_sv5_evidence(document_paths, course_name, clos, topics):
    chunks ← ingest_documents(document_paths)
    queries ← {
        course_summary: course_name + clos.description,
        weekly_schedule: course_name + topics + clos.description,
        rubrics: course_name + clos.description
    }

    evidence ← []
    FOR purpose, query IN queries:
        hits ← lexical_tfidf_bm25_search(chunks, query, top_k=3)
        evidence.ADD_UNIQUE(hits, used_for=purpose)

    IF evidence rỗng:
        RAISE DocumentIngestionError("tài liệu không liên quan")
    RETURN ingestion_summary, evidence
```

Mỗi evidence giữ `source_file`, `chunk_id`, `page` hoặc `location`, `excerpt`, `score` và `used_for`. Trong production, retriever cục bộ được thay bằng API RAG của SV1 nhưng contract evidence không đổi.

## 3. Orchestrator

```text
FUNCTION SV5SchedulerAgent.execute(payload, context):
    # BaseAgent đã validate envelope, payload, cache và logging.

    document_ingestion ← NULL
    source_evidence ← []
    IF context.document_paths tồn tại:
        document_ingestion, source_evidence ← retrieve_sv5_evidence(
            context.document_paths,
            payload.course_info.course_name,
            payload.clos,
            payload.curriculum_structure.topics
        )
    source_context ← render_as_untrusted_prompt_context(source_evidence)

    ordered_topics ← topological_sort(payload.curriculum_structure.topics)
    week_topics ← distribute_contiguous(ordered_topics, payload.total_weeks)

    weeks_skeleton ← []
    FOR week_index FROM 1 TO payload.total_weeks:
        clos_for_week ← assign_clo_by_bloom_progression(
            payload.clos, week_index, payload.total_weeks
        )
        weeks_skeleton.APPEND({
            week: week_index,
            topics: week_topics[week_index],
            clos_covered: clos_for_week,
            hours: payload.course_info.credits
        })

    uncovered ← CLO chưa xuất hiện trong weeks_skeleton
    IF uncovered IS NOT EMPTY:
        rebalance_coverage(weeks_skeleton, uncovered)

    summary ← CourseSummaryAgent.generate(payload.course_info, payload.clos, source_context)
    activities ← ActiveLearningAgent.generate(weeks_skeleton, payload.clos, source_context)
    rubrics ← RubricAgent.generate(payload.clos, activities, source_context)

    weekly_schedule ← DocumentAssemblyModule.merge(weeks_skeleton, activities)
    plo_clo_matrix ← build_plo_clo_matrix(payload.clos)
    clo_time_allocation ← build_clo_time_allocation(weekly_schedule, payload.clos)
    validation_report ← DocumentAssemblyModule.validate(
        weekly_schedule, payload.clos, rubrics, payload.total_weeks
    )

    IF validation_report.status == "FAIL":
        RAISE ValueError(validation_report.errors)

    RETURN SV5Output(
        general_info = extract_general_info(payload.course_info),
        course_summary = summary,
        plo_clo_matrix = plo_clo_matrix,
        knowledge_matrix = pivot_clo_to_weeks(weekly_schedule),
        clo_time_allocation = clo_time_allocation,
        weekly_schedule = weekly_schedule,
        references_list = payload.curriculum_structure.references,
        rubrics = rubrics,
        validation_report = validation_report,
        document_ingestion = document_ingestion,
        source_evidence = source_evidence
    )
```

## 4. Content Sequencing Module

```text
FUNCTION topological_sort(topics):
    name_to_topic ← map topic.name → topic
    IF có prerequisite không tồn tại:
        RAISE ValueError("unknown prerequisite")

    in_degree ← số prerequisite của mỗi topic
    queue ← các topic có in_degree = 0
    ordered ← []

    WHILE queue không rỗng:
        current ← queue.pop_front()
        ordered.APPEND(current)
        FOR topic phụ thuộc current:
            giảm in_degree của topic
            IF in_degree == 0:
                queue.push(topic)

    IF len(ordered) != len(topics):
        RAISE ValueError("cyclic dependency")
    RETURN ordered

FUNCTION distribute_contiguous(ordered_topics, total_weeks):
    IF ordered_topics rỗng:
        RAISE ValueError("topics rỗng")

    # Chia thành các đoạn liên tiếp; không dùng round-robin.
    base, remainder ← divmod(len(ordered_topics), total_weeks)
    cursor ← 0
    slots ← []
    FOR week FROM 1 TO total_weeks:
        take ← base + 1 nếu week <= remainder, ngược lại base
        slots.APPEND(ordered_topics[cursor : cursor + take])
        cursor ← cursor + take

    FOR slot rỗng:
        slot ← "Ôn tập / Thực hành"
    RETURN slots

FUNCTION assign_clos_to_weeks(clos, total_weeks):
    assigned_count ← map clo.code → 0
    result ← []

    FOR week FROM 1 TO total_weeks:
        target_bloom ← max(1, round(week / total_weeks × 6))
        selected ← CLO có tuple nhỏ nhất:
            (abs(clo.bloom_level - target_bloom),
             assigned_count[clo.code],
             clo.code)
        result.APPEND([selected.code])
        assigned_count[selected.code] += 1

    RETURN result
```

## 5. Active Learning Agent

```text
FUNCTION generate_activities(weeks_skeleton, clos):
    result ← []
    FOR week IN weeks_skeleton:
        week_clos ← các CLO của week
        max_bloom ← mức Bloom cao nhất của week_clos

        IF max_bloom <= 2:
            method ← "Think-Pair-Share / thảo luận nhóm"
        ELSE IF max_bloom <= 4:
            method ← "Case study / bài tập tình huống"
        ELSE:
            method ← "Project-based learning / mini project"

        language_output ← LLM.generate(week.topics, week_clos, method)
        result.APPEND({
            week: week.week,
            teaching_methods: method,
            class_activities: language_output.class_activities,
            homework: language_output.homework
        })
    RETURN result
```

## 6. Course Summary Agent

```text
FUNCTION generate_summary(course_info, clos):
    prompt ← "Viết tóm tắt môn học bằng tiếng Việt, 120–150 từ, "
              + "bám sát course_info và CLO, không thêm thông tin ngoài input"
    summary ← LLM.generate(prompt, course_info, clos)
    IF summary rỗng:
        RAISE ValueError("course summary rỗng")
    RETURN summary
```

## 7. Rubric Agent

```text
FUNCTION generate_rubrics(clos, activities):
    prompt ← "Sinh rubric cho attendance, assignment, final_exam. "
              + "Mỗi cột có 4 mức: Xuất sắc, Khá, Đạt, Chưa đạt; "
              + "mô tả phải liên hệ với CLO và hoạt động đã thiết kế."
    rubrics ← LLM.generate(prompt, clos, activities)

    IF thiếu một trong [attendance, assignment, final_exam]:
        RAISE ValueError("rubric thiếu cột")
    RETURN rubrics
```

## 8. Ma trận PLO–CLO

```text
FUNCTION build_plo_clo_matrix(clos):
    matrix ← {}
    FOR clo IN clos:
        FOR plo IN clo.mapped_plos:
            matrix[plo].append_unique(clo.code)
    RETURN matrix
```

Tên field `plo_clo_matrix` phải giữ đúng theo contract của SV7.

## 9. Document Assembly và validation

```text
FUNCTION merge(weeks_skeleton, activities):
    activity_by_week ← map activity.week → activity
    result ← []
    FOR week IN weeks_skeleton:
        activity ← activity_by_week[week.week]
        result.APPEND({
            week: week.week,
            topics: week.topics,
            clos_covered: week.clos_covered,
            hours: week.hours,
            teaching_methods: activity.teaching_methods,
            class_activities: activity.class_activities,
            homework: activity.homework
        })
    RETURN result

FUNCTION validate(schedule, clos, rubrics, total_weeks):
    errors ← []
    IF len(schedule) != total_weeks:
        errors.APPEND("sai số lượng tuần")

    covered ← flatten(schedule.clos_covered)
    FOR clo IN clos:
        IF clo.code NOT IN covered:
            errors.APPEND(clo.code + " chưa được bao phủ")

    FOR column IN [attendance, assignment, final_exam]:
        IF column thiếu hoặc criteria rỗng:
            errors.APPEND("rubric thiếu " + column)

    RETURN PASS nếu errors rỗng, ngược lại FAIL

FUNCTION build_clo_time_allocation(schedule, clos):
    breakdown ← map clo.code → []
    total_course_hours ← SUM(schedule.hours)

    FOR week IN schedule:
        covered ← unique(week.clos_covered)
        IF covered có CLO không tồn tại:
            RAISE ValueError

        # Nếu một tuần gắn nhiều CLO thì chia đều giờ của tuần đó.
        shares ← split_exactly(week.hours, len(covered))
        FOR clo_code, hours IN zip(covered, shares):
            breakdown[clo_code].APPEND({week: week.week, hours: hours})

    FOR clo IN clos:
        clo_total ← SUM(breakdown[clo.code].hours)
        result.APPEND({
            clo_code: clo.code,
            total_hours: clo_total,
            percentage: clo_total / total_course_hours × 100,
            weeks: breakdown[clo.code].week,
            weekly_breakdown: breakdown[clo.code]
        })
    RETURN result
```

## 10. Error handling và test case

- Envelope sai hoặc payload sai schema: BaseAgent trả `status=failed`.
- Dữ liệu đúng schema nhưng prerequisite vòng/không tồn tại: logic `raise ValueError`, BaseAgent bắt và trả `status=failed`.
- Không trả dữ liệu giả khi LLM lỗi hoặc output JSON sai.
- Tài liệu rỗng, không tồn tại, sai định dạng hoặc không liên quan: raise lỗi trước khi gọi LLM.
- Bộ test tối thiểu: happy path, validation error, runtime error, document ingestion, retrieval đúng nguồn, irrelevant-document rejection; thêm test giữ thứ tự prerequisite và kiểm tra field `plo_clo_matrix`.
