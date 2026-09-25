# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Văn Việt             |
| MSSV               | 2A202602904                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | MegaLive     |
| Vai trò chính    | Member (Checkpoint 3)                 |
| Repository         | https://github.com/diggoryQH/K4-L3-DAY10-MegaLive-DataPipeline |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Baseline Pipeline End-to-End      | `src/pipelines/phase1.py`           | Settings, Clean Data          | Evaluation Baseline, Report | Hoàn thành |
| Runner script      | `script/run_phase1.py`           | None          | Chạy pipeline | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Debug Evaluate Pipeline | Hà Huy Nhất | Sửa lỗi sai thứ tự truyền tham số trong hàm evaluate_pipeline |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Chạy luồng baseline | `script/run_phase1.py` | Pipeline chạy thành công | Terminal không có lỗi |
| Báo cáo Phase 1 | `data/reports/phase1_report.md` | Báo cáo Markdown Baseline | Mở file xem Hit Rate |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tạo ra `data/reports/phase1_report.md` thể hiện các chỉ số Hit Rate, F1, Data Quality Passed, là thước đo tiêu chuẩn để đo lường độ sụt giảm ở các pha sau.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Cần một pipeline tự động để chạy lần lượt các bước: Load data, build Index, generate test set, đánh giá test set, check data quality, tạo report, thay vì chạy tay từng file.

### Cách triển khai
Viết hàm `main()` trong `phase1.py`:
- Gọi `load_raw_records` -> `build_clean_dataframe`.
- Gọi `LocalEmbeddingIndex.build`.
- Gọi `build_test_set`.
- Gọi `evaluate_pipeline`.
- Gọi `run_data_quality_checks` và `build_freshness_report`.
- Gọi `generate_phase1_report`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `Settings` từ core config           |
| Output                         | Artifacts files (JSON, CSV, MD) |
| Module phụ thuộc             | `src.evaluation`, `src.ingestion`, `src.retrieval`                    |
| Module sử dụng output        | `script/run_phase1.py`                    |
| Điều kiện lỗi cần xử lý | Lỗi thiếu file raw json, lỗi API LLM đánh giá                   |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Quá trình đánh giá chạy thành công và báo cáo Phase 1 được lưu.
- **Kết quả thực tế:** Code 0, xuất ra báo cáo.
- **Artifact/log:** `data/reports/phase1_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Vấn đề truyền Dataframe hay truyền Index vào evaluate_pipeline.
- **Các phương án đã cân nhắc:** Trong code ban đầu bị truyền nhầm `df_clean` thay vì `index`.
- **Phương án đã chọn:** Sửa đúng signature `evaluate_pipeline(settings, index, test_set_path, metrics_out, answers_out)`.
- **Lý do:** Bắt buộc phải truyền đúng `LocalEmbeddingIndex` vì hàm QA cần gọi hàm `.search()` của index.
- **Bằng chứng quyết định phù hợp:** Chạy không còn lỗi AttributeError.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** AttributeError: 'DataFrame' object has no attribute 'lookup'
- **Nguyên nhân gốc:** Hàm được mong đợi một đối tượng Index nhưng tôi lại truyền nhầm một Pandas DataFrame vào.
- **Cách xử lý:** Đổi vị trí tham số truyền vào hàm `evaluate_pipeline`.
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_phase1.py` thành công.
- **Điều học được:** Cần sử dụng Type Hint đầy đủ và kiểm tra kỹ signature của hàm.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Từ JSON qua API -> lưu file raw -> Pandas Dataframe (được clean, xoá trùng, nối text) -> lưu thành CSV -> dùng Chroma client và SentenceTransformer để nhúng thành vector -> lưu `data_level0.bin`.
2. Các test set được sinh dựa trên dữ liệu ban đầu. Ground-truth ID giúp đối chiếu xem khi search, Chroma có trả ra đúng doc đó không (Hit Rate). Còn Answer Quality thì dùng một LLM Prompt làm giám khảo (Judge) chấm điểm câu trả lời của mô hình với Reference.
3. Quality Checks (GX) kiểm tra về cấu trúc (schema, null, length), còn Freshness SLA kiểm tra về tính thời sự (ngày publish so với hiện tại).
4. Để đảm bảo tính nhất quán (control variable). Nếu đổi test set thì sẽ không biết hiệu năng giảm là do test khó hơn hay do dữ liệu bị bẩn.
5. Khi Hit Rate và F1 Token score quay trở về mức 1.0 (như lúc baseline) trong file `corruption_report.md`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.6 |      1.0 | Sụt giảm mạnh khi corrupt do nhiễu và xoá summary |
| `mean_token_f1`      |      1.0 |       0.77 |      1.0 | Sụt giảm tương ứng vì không có context tốt |
| `judge_accuracy`     |      1.0 |       0.5 |      1.0 | Tỉ lệ trả lời sai 1 nửa |
| `mean_judge_score`   |      5.0 |       2.8 |      5.0 | Điểm thấp khi bị corrupted |
| Quality checks         |      Passed |       Failed |      Passed | GX phát hiện được dữ liệu sai |
| Freshness status       |      Passed |       Passed |      Passed | Stale records không bị bẫy ở corrupt |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → quality signal Failed → agent metric (F1/Hit Rate) giảm sút 40%.
2. Repair action → quality signal phục hồi (Passed) → agent metric phục hồi nguyên vẹn 100%.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Lỗi Truncate title khiến cho các thông tin quan trọng bị cụt lủn và Blank Summary ảnh hưởng mạnh nhất đến Agent. Không có dữ liệu, Agent mất hoàn toàn khả năng search.

Kết quả nào khác với kỳ vọng ban đầu?

Tôi nghĩ Hit Rate sẽ giảm về 0 nhưng cuối cùng nó chỉ giảm còn 0.6. Điều này chứng tỏ vector model vẫn cố gắng lấy ra các tài liệu liên quan thông qua trường authors và categories.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của Data Observability. Lỗi silent failure (API chạy được nhưng trả lời sai do data bẩn) cực kỳ nguy hiểm.
2. Việc sử dụng Great Expectations để bắt lỗi schema trước khi nạp vào VectorDB là bắt buộc.
3. Cách vận hành End-to-End Pipeline tự động hoá.

### Nếu có thêm thời gian

Tôi sẽ viết unit test chi tiết cho từng Pipeline function.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Việt
**Ngày xác nhận:** 2026-09-25
