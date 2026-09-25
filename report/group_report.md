# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                      |
| ------------------ | -------------------------------------------------------------- |
| Khóa/Lớp         | K4                                                             |
| Tên nhóm         | MegaLive                                                       |
| Repository         | https://github.com/diggoryQH/K4-L3-DAY10-MegaLive-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                     |

### Thành viên và phân công

| STT | Họ và tên       | MSSV        | Vai trò chính | Module/deliverable sở hữu                                                                                       |
| --: | ------------------ | ----------- | --------------- | ----------------------------------------------------------------------------------------------------------------- |
|   1 | Ngụy Quang Hùng  | 2A202602998 | Team Leader     | `src/ingestion/corruption.py`, `report/*.md`                                                                  |
|   2 | Đinh Xuân Quyền | 2A202602358 | Member          | `src/ingestion/cleaning.py`, `src/observability/quality.py`, `src/evaluation/testset.py`, `data/quality/` |
|   3 | Nguyễn Văn Việt | 2A202602904 | Member          | `script/run_phase1.py`, `src/pipelines/phase1.py`, `data/reports/phase1_report.md`                          |
|   4 | Hà Huy Nhất      | 2A202602401 | Member          | `script/run_corruption_flow.py`, `src/pipelines/corruption_flow.py`, `data/reports/corruption_report.md`    |

## 2. Tóm tắt kết quả

Nhóm MegaLive đã hoàn thành toàn bộ End-to-End Pipeline bao gồm Baseline Phase 1, Data Corruption giả lập lỗi dữ liệu và Idempotent Repair phục hồi 3 trạng thái.

- **Baseline pipeline** đã tạo ra thành công các artifact `data/clean/papers_clean.csv`, `data/eval/test_set.json` (10 câu hỏi), Chroma Index và báo cáo Phase 1. Hit Rate và F1 Token đều đạt mức 1.0.
- **Corruption** ảnh hưởng nặng nhất đến RAG Agent là lỗi *Blank Summary* và *Drop Latest Records*, khiến cho mô hình bị mất đoạn văn bản ngữ cảnh chứa câu trả lời. Hệ quả là Hit Rate giảm còn 0.60, Token F1 giảm còn 0.77.
- **Repair** đã tái thiết dữ liệu thành công từ Raw Records, khôi phục lại Data Quality (từ Failed về Passed) và kéo tất cả chỉ số Hit Rate / Token F1 phục hồi 100% về mức chuẩn 1.0 của Baseline.
- **Blocker quan trọng nhất:** Không có LLM API đủ mạnh nên việc gọi Judge thi thoảng chậm hoặc bị Rate Limit.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input            | Xử lý chính                        | Output/artifact                        | Owner                              |
| ----------------- | ---------------- | ------------------------------------- | -------------------------------------- | ---------------------------------- |
| Ingestion         | API/Snapshot     | Fetch, parse JSON data                | `data/raw/crossref_records.json`     | Hà Huy Nhất                      |
| Cleaning          | Raw Records      | Xóa duplicates, format datetime      | `data/clean/papers_clean.csv`        | Đinh Xuân Quyền                 |
| Embedding/index   | Clean Data       | SentenceTransformer MiniLM            | `data/chroma/`                       | Đinh Xuân Quyền                 |
| Evaluation        | Clean Data       | Sinh 10 câu hỏi test & Eval metrics | `data/results/baseline_metrics.json` | Nguyễn Văn Việt                 |
| Observability     | Clean Data       | GX 1.x & Freshness checks             | `data/quality/`                      | Đinh Xuân Quyền                 |
| Corruption/repair | Clean Data / Raw | Inject errors & Reparse từ đầu     | `corruption_log.json`                | Ngụy Quang Hùng                  |
| Orchestration     | Toàn bộ config | Gọi chuỗi hàm liên tiếp          | `data/reports/*.md`                  | Nguyễn Văn Việt & Hà Huy Nhất |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng                    |
| ---------------------------- | -------------------------------------- |
| `LLM_PROVIDER`             | gemini                                 |
| `LLM_MODEL`                | gemini-1.5-flash                       |
| Embedding model              | sentence-transformers/all-MiniLM-L6-v2 |
| Số lượng Crossref records | 24                                     |
| Retrieval`top_k`           | 4                                      |
| Freshness threshold          | 180 days (tối đa 25% quá hạn)      |
| Random seed, nếu có        | N/A                                    |

### Lệnh cài đặt

```bash
pip install -e .
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng                          |
| ----------------- | ------------ | ----------------------------- | ------------------------------------- |
| Baseline pipeline | Thành công | 2026-09-25 15:30:00           | `data/reports/phase1_report.md`     |
| Corruption flow   | Thành công | 2026-09-25 15:35:00           | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                                   |
| --------------------------- | ------------------------------------------- |
| Source                      | Crossref API endpoint (Local Fallback)      |
| Query/filter                | Data Engineering, AI                        |
| Thời điểm lấy dữ liệu | 2026-09-25                                  |
| Số record nhận được    | 24                                          |
| Cơ chế retry/backoff      | Exponential backoff 3 lần nếu API timeout |

### Raw và clean schema

| Trường      | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa                 | Xử lý khi thiếu/sai                                     |
| ------------- | --------------- | ----------- | ------------------------- | ---------------------------------------------------------- |
| `paper_id`  | Chuỗi (str)    | Có         | ID duy nhất bài báo    | Loại bỏ nếu trùng (Drop duplicates)                    |
| `title`     | Chuỗi          | Có         | Tên bài báo            | Chuyển thành chuỗi rỗng nếu thiếu                    |
| `summary`   | Chuỗi          | Không      | Phần tóm tắt nội dung | Cắt bớt nếu quá dài, điền rỗng nếu mất           |
| `published` | Datetime        | Có         | Ngày xuất bản          | Cố gắng parse qua thư viện datetime, tính`age_days` |

### Quy tắc cleaning

| Quy tắc                       | Quality dimension liên quan | Số record bị tác động | Cách xác minh               |
| ------------------------------ | ---------------------------- | -------------------------: | ----------------------------- |
| Loại bỏ paper_id trùng lặp | Uniqueness                   |                          0 | ExpectColumnValuesToBeUnique  |
| Check trường title bị null  | Completeness                 |                          0 | ExpectColumnValuesToNotBeNull |

**Cách nhóm tạo `text_for_embedding`, document ID và `age_days`:**

- `text_for_embedding`: Nối thủ công các trường quan trọng theo format định sẵn `Title: ... \n Authors: ... \n Published: ... \n Categories: ... \n Summary: ...`. Điều này giúp mô hình nhúng (embedding model) có đủ context.
- `document ID`: Dùng chính `paper_id` từ API trả về (DOI).
- `age_days`: Tính bằng cách trừ ngày giờ lúc chạy pipeline (`run_date`) cho `published`. Dùng timedelta để lấy ra chính xác số ngày.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế                                           |
| ---------------------------------------- | -------------------------------------------------------------- |
| Số câu hỏi                            | 10                                                             |
| Các`question_type`                    | summary, authors, date, categories                             |
| Ground-truth document ID                 | Dùng paper_id ngẫu nhiên trích xuất từ testset generator |
| Embedding model                          | sentence-transformers/all-MiniLM-L6-v2                         |
| Vector store/collection                  | ChromaDB (`papers-baseline`)                                 |
| Retrieval`top_k`                       | 4                                                              |
| LLM provider/model                       | gemini / gemini-1.5-flash                                      |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json`                                    |

**Vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:**
Đây là phương pháp **Control Variable** (biến kiểm soát). Nếu testset thay đổi giữa 3 lần chạy, nhóm sẽ không thể biết được sự tụt giảm của điểm số F1 là do testset đợt sau khó hơn, hay do data thực sự bị bẩn. Bằng cách chốt cố định test set, mọi sự chênh lệch trong kết quả hoàn toàn đến từ chất lượng của Knowledge Base.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú                         |
| ------------------------ | -------------------------------------- | ------------ | -------------------------------- |
| Raw response/records     | `data/raw/`                          | Có          | Đủ 2 file json                 |
| Cleaned dataset          | `data/clean/`                        | Có          | Đủ csv, json                   |
| Embedding manifest/index | `data/embeddings/`                   | Có          | Các file json embedding mapping |
| Evaluation set           | `data/eval/`                         | Có          | 10 câu test                     |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có          | Chứa kết quả đánh giá      |
| Quality/freshness        | `data/quality/`                      | Có          | Báo cáo GX                     |
| Baseline report          | `data/reports/phase1_report.md`      | Có          | Báo cáo Markdown               |

### Baseline metrics

| Metric                 | Giá trị | Diễn giải                                                              |
| ---------------------- | --------: | ------------------------------------------------------------------------ |
| `retrieval_hit_rate` |       1.0 | 100% ChromaDB trả về đúng tài liệu chứa ground truth              |
| `mean_token_f1`      |       1.0 | Câu trả lời của mô hình khớp hoàn toàn với câu trả lời gốc |
| `judge_accuracy`     |       1.0 | Giám khảo LLM chấm điểm sai số thấp                               |
| `mean_judge_score`   |       5.0 | Điểm tuyệt đối từ Giám khảo LLM                                  |
| Ragas, nếu có        |       N/A | Dùng custom judge heuristic nội bộ thay vì Ragas gốc                |

## 8. Data quality và freshness

### Quality checks

| Check                               | Quality dimension | Ngưỡng/kỳ vọng            | Kết quả baseline | Bằng chứng                 |
| ----------------------------------- | ----------------- | ----------------------------- | ------------------ | ---------------------------- |
| ExpectTableRowCountToBeBetween      | Volume            | 5 - 5000                      | Pass (24 records)  | baseline_quality_report.json |
| ExpectColumnValuesToNotBeNull       | Completeness      | Không null (paper_id, title) | Pass               | baseline_quality_report.json |
| ExpectColumnValuesToBeUnique        | Uniqueness        | paper_id là duy nhất        | Pass               | baseline_quality_report.json |
| ExpectColumnValueLengthsToBeBetween | Completeness      | summary >= 30 kí tự         | Pass               | baseline_quality_report.json |

### Freshness

| Thuộc tính               | Giá trị                                                                |
| -------------------------- | ------------------------------------------------------------------------ |
| Freshness được đo tại | `papers_clean` dataframe                                               |
| Timestamp mới nhất       | 2026-06-12 (Tùy dataset API lúc gọi)                                  |
| Ngưỡng freshness         | Tối đa 25% quá 180 ngày                                              |
| Trạng thái baseline      | Fresh                                                                    |
| Lý do                     | Tỉ lệ bài báo cũ (stale_ratio) chỉ ở mức dưới ngưỡng (<25%). |

## 9. Corruption scenarios và repair

| Corruption          | Cách tạo                    | Record bị tác động | Quality signal kỳ vọng      | Tác động thực tế                           | Cách repair        |
| ------------------- | ----------------------------- | ---------------------: | ----------------------------- | ----------------------------------------------- | ------------------- |
| Drop latest records | Cắt bỏ head records         |                      5 | Freshness cảnh báo cũ hơn | Hit rate sụt giảm mạnh                       | Đọc lại raw gốc |
| Blank summary       | Thay summary bằng rỗng      |                      3 | GX Length fail                | Trả lời không có căn cứ (F1 giảm)        | Đọc lại raw gốc |
| Inject noise        | Chèn token vô nghĩa        |                      3 | Không bắt được ở schema | Vector rối, trả về sai văn bản             | Đọc lại raw gốc |
| Truncate title      | Cắt title < 8 kí tự        |                      4 | N/A                           | Mất ngữ nghĩa tựa đề                      | Đọc lại raw gốc |
| Stale date          | Trừ đi 365 ngày xuất bản |                      8 | Freshness Fail                | Freshness Failed trong corrupted_quality_report | Đọc lại raw gốc |
| Duplicate rows      | Nhân bản 2 dòng cuối      |                      2 | Uniqueness Fail               | Báo lỗi Duplicate ở GX                       | Đọc lại raw gốc |

**Corruption log:**

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ 6 scenario, có mảng `paper_ids` mô tả cụ thể ID nào bị đổi.

**Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy:**
Thay vì nhóm cố gắng lọc và tìm các lỗi trong bảng corrupted để "sửa chữa thủ công", nhóm áp dụng triết lý Data Engineering chuẩn xác: **Idempotency**. Nghĩa là vứt bỏ toàn bộ dataframe bị hỏng và tạo lại từ đầu (`load_raw_records`) từ file JSON gốc tải từ Crossref ban đầu. Dữ liệu Raw này là Source of Truth bất di bất dịch, đảm bảo không bao giờ có lỗi ẩn nào còn sót lại.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét                                            |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ----------------------------------------------------- |
| `retrieval_hit_rate`   |      1.0 |      0.60 |      1.0 |                     -0.4 |            100% | Bị sụt giảm mạnh do Blank summary                 |
| `mean_token_f1`        |      1.0 |      0.77 |      1.0 |                    -0.23 |            100% | Agent không trả lời nổi khi thiếu văn bản      |
| `judge_accuracy`       |      1.0 |      0.50 |      1.0 |                     -0.5 |            100% | Trả lời sai tới 50%                                |
| `mean_judge_score`     |      5.0 |      2.80 |      5.0 |                     -2.2 |            100% | Điểm tụt xuống dưới mức trung bình            |
| Quality checks pass/fail |     Pass |      Fail |     Pass |                     Fail |            Pass | Bắt được lỗi duplicate và length                |
| Freshness status         |     Pass |      Pass |     Pass |                     Pass |            Pass | Ngưỡng 25% vẫn đủ an toàn ở corrupt đợt này |

**Kết luận có quan hệ nhân quả:**

1. Blank Summary + Inject Noise → Data Quality Schema Failed → Khiến ChromaDB nhúng vector rác → Không tìm ra tài liệu đúng (Hit Rate giảm) → Câu trả lời (F1) kém.
2. Repair từ file Raw JSON gốc → Data Quality Schema Passed trở lại → ChromaDB có lại vector sạch chuẩn → Agent Metric phục hồi 100% như cũ.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi code pipeline `run_phase1.py`, chương trình văng lỗi `AttributeError: 'DataFrame' object has no attribute 'lookup'`.
- **Nguyên nhân:** Hàm `evaluate_pipeline()` yêu cầu truyền tham số `index` (kiểu LocalEmbeddingIndex) ở vị trí thứ 2, nhưng trong code ban đầu truyền nhầm một Dataframe `df_clean` vào vị trí này. Do Python không có strict typing, nó nuốt Dataframe vào và văng lỗi ở tít bên trong hàm tìm kiếm qa.
- **Cách xử lý:** Đổi vị trí tham số khi gọi hàm: `evaluate_pipeline(settings, index, test_set_path, ...)`
- **Cách xác minh:** Chạy `python script/run_phase1.py` hoàn thành bình thường.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại           | Ảnh hưởng                           | Hướng cải thiện có thể kiểm chứng                                          |
| ------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| Thiếu cơ chế Caching LLM     | Pipeline chạy chậm do phải chờ API | Triển khai Redis Cache hoặc Local JSON store để lưu đáp án Judge đã sinh |
| Freshness threshold cứng ngắc | Stale ratio có khi không kích hoạt | Dùng Machine Learning anomaly detection để set threshold động                 |

## 13. Checklist trước khi nộp

- [X] Thông tin nhóm và repository chính xác.
- [X] Phân công khớp với module, artifact và kết quả thực tế.
- [X] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [X] Baseline, corrupted và repaired dùng cùng evaluation set.
- [X] Bảng metrics khớp với các file trong `data/results/`.
- [X] Quality/freshness conclusions khớp với `data/quality/`.
- [X] Các đường dẫn báo cáo và artifact truy cập được.
- [X] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [X] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
