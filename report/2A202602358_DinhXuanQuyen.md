# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đinh Xuân Quyền             |
| MSSV               | 2A202602358                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | MegaLive     |
| Vai trò chính    | Member (Checkpoint 1, 2)                 |
| Repository         | https://github.com/diggoryQH/K4-L3-DAY10-MegaLive-DataPipeline |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Cleaning & Quality      | `src/ingestion/cleaning.py`, `src/observability/quality.py`           | Raw JSON          | Cleaned Dataframe & JSON Report | Hoàn thành |
| Benchmark Test Set      | `src/evaluation/testset.py`           | Cleaned Dataframe          | `test_set.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Support review dữ liệu Dataframe | Ngụy Quang Hùng | Bảng dữ liệu Corrupted được generate thành công, đúng format |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Làm sạch và thêm logic age_days | `src/ingestion/cleaning.py` | Dataframe chuẩn bị sẵn sàng | Kiểm tra length dòng, column |
| Sinh 10 câu hỏi đánh giá | `src/evaluation/testset.py` | `data/eval/test_set.json` | Mở file `test_set.json` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tạo ra `test_set.json` gồm 10 câu hỏi đa dạng (categories, summary, authors...) làm nền tảng cho việc Benchmark RAG, cung cấp ground_truth cho pha đánh giá sau.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu thô tải từ API thường có trùng lặp hoặc chứa null, cần được chuẩn hóa. Đồng thời cần một bộ công cụ bắt lỗi schema (Great Expectations) và tự động sinh testset để đánh giá RAG.

### Cách triển khai
- Dùng Pandas `drop_duplicates` dựa trên `paper_id`.
- Chuyển `published` sang datetime và tính `age_days` so với `run_date`.
- Khởi tạo GX 1.x `ephemeral` context, thiết lập `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique`.
- Lọc test set bằng cách pick random 2-3 row và generate câu hỏi tương ứng theo rule.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Dữ liệu raw tải từ CrossRef           |
| Output                         | DataFrame đã qua xử lý, Testset JSON |
| Module phụ thuộc             | `great_expectations`, `pandas`                    |
| Module sử dụng output        | `src/pipelines/phase1.py`                    |
| Điều kiện lỗi cần xử lý | Xử lý file ngày tháng dị dạng                   |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(f'Tín hiệu hoàn thành: Quality check status = {res[\"success\"]}')"
```

- **Kết quả mong đợi:** In ra True.
- **Kết quả thực tế:** `Tín hiệu hoàn thành: Quality check status = True`
- **Artifact/log:** Console log.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn mức ngưỡng Freshness SLA.
- **Các phương án đã cân nhắc:** Dùng ngưỡng 90 ngày (quá khó vì data cũ nhiều) hoặc 180 ngày.
- **Phương án đã chọn:** 180 ngày, và cho phép 25% số lượng bài báo được cũ hơn mốc này.
- **Lý do:** Trade-off giữa việc báo động giả (False positive) quá nhiều và độ khắt khe. CrossRef paper có thể ra đời từ lâu nên 180 ngày là hợp lý với domain này.
- **Bằng chứng quyết định phù hợp:** Baseline chạy freshness passed an toàn.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Lỗi version Great Expectations (attribute error).
- **Nguyên nhân gốc:** Phiên bản GX mới 1.0 thay đổi hoàn toàn API so với GX 0.18, dùng ephemeral thay vì FileDataContext cũ.
- **Cách xử lý:** Cập nhật lại Code khai báo Context theo Documentation của GX 1.x.
- **Cách xác minh sau khi sửa:** Chạy check không bị văng exception.
- **Điều học được:** Luôn đọc docs mới nhất khi dùng version package lớn.

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

Việc làm rỗng summary (Blank Summary) ảnh hưởng lớn nhất vì phần text vectorizer sẽ mất context chứa insight để search.

Kết quả nào khác với kỳ vọng ban đầu?

Tôi tưởng Duplicate Rows sẽ làm giảm độ chính xác của RAG do mô hình tìm thấy 2 bài giống hệt nhau, nhưng thực ra Vector DB tự handle khá tốt, chỉ có GX báo lỗi.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của Data Observability. Lỗi silent failure (API chạy được nhưng trả lời sai do data bẩn) cực kỳ nguy hiểm.
2. Việc sử dụng Great Expectations để bắt lỗi schema trước khi nạp vào VectorDB là bắt buộc.
3. Cần có Ground Truth rõ ràng thì mới tính toán độ đo tự động RAGAS được.

### Nếu có thêm thời gian

Thêm expectation kiểm tra grammar spelling cho summary.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đinh Xuân Quyền
**Ngày xác nhận:** 2026-09-25
