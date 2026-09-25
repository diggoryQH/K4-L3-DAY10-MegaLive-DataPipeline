# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                      |
| ------------------ | -------------------------------------------------------------- |
| Họ và tên       | Ngụy Quang Hùng                                              |
| MSSV               | 2A202602998                                                    |
| Khóa/Lớp         | K4                                                             |
| Tên nhóm         | MegaLive                                                       |
| Vai trò chính    | Team Leader (Checkpoint 4, Report)                             |
| Repository         | https://github.com/diggoryQH/K4-L3-DAY10-MegaLive-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                     |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable   | File/hàm phụ trách           | Input nhận vào                 | Output bàn giao                                         | Trạng thái |
| -------------------- | ------------------------------- | -------------------------------- | -------------------------------------------------------- | ------------ |
| Fake corruption data | `src/ingestion/corruption.py` | Dataframe`papers_clean`        | Dataframe corrupted,`data/results/corruption_log.json` | Hoàn thành |
| Tổng hợp Report    | `report/group_report.md`      | Artifacts, code, kết quả chạy | File báo cáo đầy đủ thông tin nhóm               | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                           | Thành viên/module được hỗ trợ | Kết quả                                                                                       |
| -------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Hỗ trợ ghép nối Code (Integration) | Toàn nhóm (CP3, CP5)               | Tích hợp thành công luồng`run_phase1.py` và `run_corruption_flow.py` không gặp lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện    | File/hàm/artifact liên quan        | Kết quả bàn giao             | Cách xác minh                                               |
| ------------------------------ | ------------------------------------ | ------------------------------- | ------------------------------------------------------------- |
| Cố tình tiêm lỗi vào data | `src/ingestion/corruption.py`      | Hàm`corrupt_clean_dataframe` | Chạy`python script/run_corruption_flow.py` thấy GX failed |
| Ghi log lỗi                   | `data/results/corruption_log.json` | File log ghi nhận 6 scenarios  | Mở file`corruption_log.json`                               |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tạo ra một file log `corruption_log.json` ghi lại toàn bộ 6 lỗi đã tiêm vào dữ liệu (như số lượng dòng bị xóa, số lượng dòng bị làm rỗng summary, v.v.). Output này chứng minh quá trình Corruption đã hoạt động.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Kiểm chứng xem hệ thống RAG và Data Quality Gate có phát hiện được sự sụt giảm chất lượng dữ liệu (Silent Failure) hay không thông qua việc cố ý làm bẩn dữ liệu.

### Cách triển khai

Tôi xây dựng hàm `corrupt_clean_dataframe` thực hiện một chuỗi các thao tác:

- Lấy 20% records mới nhất để xoá đi (Drop records).
- Lọc 10% dòng để xoá trường `summary` (Blank summary).
- Chèn chuỗi rác vào text (Inject noise).
- Chỉnh sửa `title` bằng cách cắt đi chỉ còn < 8 ký tự.
- Chỉnh sửa `published` bằng cách trừ đi 365 ngày (Stale date).
- Nhân đôi 1 bản ghi (Duplicate rows).

### Input, output và contract

| Thành phần                   | Mô tả                                                                     |
| ------------------------------ | --------------------------------------------------------------------------- |
| Input                          | `papers_clean` dataframe (chuẩn hóa từ CP1)                            |
| Output                         | `papers_corrupted` dataframe (dữ liệu bẩn) và file JSON log           |
| Module phụ thuộc             | `core.utils.write_json`                                                   |
| Module sử dụng output        | `src/pipelines/corruption_flow.py` (để đem đi evaluate)               |
| Điều kiện lỗi cần xử lý | Xử lý file input rỗng, đảm bảo`index` không bị lỗi out-of-bounds |

### Cách xác minh

```bash
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Quá trình chạy hiện lên thông báo "Run quality & freshness checks on corrupted data".
- **Kết quả thực tế:** Chương trình chạy và báo cáo Data Quality Failed.
- **Artifact/log:** `data/results/corruption_log.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cách giả lập lỗi cũ dữ liệu (Stale date).
- **Các phương án đã cân nhắc:** Đổi ngày của toàn bộ bảng về 1 năm trước, hoặc chỉ đổi một lượng nhỏ records (10%).
- **Phương án đã chọn:** Chỉ đổi của 1 lượng records đủ lớn (>25%) để đánh lừa SLA. Thực tế đổi 35%.
- **Lý do:** Trade-off: Giúp kiểm tra xem ngưỡng threshold (25% stale ratio) của hệ thống Freshness SLA có hoạt động chính xác không, nếu làm quá ít thì SLA sẽ không failed.
- **Bằng chứng quyết định phù hợp:** `corrupted_quality_report.json` báo failed về freshness.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Lỗi out of bounds khi cố tình tạo duplicate dòng nếu dataframe truyền vào bị rỗng.
- **Lệnh hoặc bước tái hiện:** Trực tiếp test bằng df.empty
- **Nguyên nhân gốc:** Hàm logic `.iloc[[0]]` không hoạt động nếu mảng rỗng.
- **Cách xử lý:** Thêm dòng kiểm tra `if len(df) > 0:` trước khi tạo duplicate.
- **Cách xác minh sau khi sửa:** Chạy lại file pipeline thấy qua mượt mà.
- **Điều học được:** Luôn phải phòng ngừa trường hợp corner-cases khi làm Data Pipeline.

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

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                               |
| ---------------------- | -------: | --------: | -------: | ------------------------------------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.6 |      1.0 | Sụt giảm mạnh khi corrupt do nhiễu và xoá summary |
| `mean_token_f1`      |      1.0 |      0.77 |      1.0 | Sụt giảm tương ứng vì không có context tốt     |
| `judge_accuracy`     |      1.0 |       0.5 |      1.0 | Tỉ lệ trả lời sai 1 nửa                            |
| `mean_judge_score`   |      5.0 |       2.8 |      5.0 | Điểm thấp khi bị corrupted                          |
| Quality checks         |   Passed |    Failed |   Passed | GX phát hiện được dữ liệu sai                    |
| Freshness status       |   Passed |    Passed |   Passed | Stale records không bị bẫy ở corrupt                |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → quality signal Failed → agent metric (F1/Hit Rate) giảm sút 40%.
2. Repair action → quality signal phục hồi (Passed) → agent metric phục hồi nguyên vẹn 100%.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Corruption ảnh hưởng rõ nhất là việc **Blank Summary** và **Drop Latest Records**, vì lúc này ChromaDB không có nội dung văn bản liên quan để match với câu hỏi (làm Hit Rate giảm mạnh).

Kết quả nào khác với kỳ vọng ban đầu?

Ban đầu tôi nghĩ rằng **Inject noise** sẽ làm điểm tụt mạnh nhất do đánh lừa LLM, nhưng thực tế LLM có khả năng lọc nhiễu rất tốt, nguyên nhân tụt điểm chính lại nằm ở việc ChromaDB không tìm được tài liệu gốc khi bị thiếu context (Hit Rate giảm).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của Data Observability. Lỗi silent failure (API chạy được nhưng trả lời sai do data bẩn) cực kỳ nguy hiểm.
2. Việc sử dụng Great Expectations để bắt lỗi schema trước khi nạp vào VectorDB là bắt buộc.
3. Reproductibility: Pipeline phải viết gọn gàng và có tính Idempotent, cho phép chạy lại từ Raw một cách dễ dàng.

### Nếu có thêm thời gian

Tôi sẽ viết thêm 1 rule Alert qua Slack hoặc Email khi Data Quality Failed.

## 10. Cam kết của thành viên

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngụy Quang Hùng
**Ngày xác nhận:** 2026-09-25
