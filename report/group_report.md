# Group Report - Day 10: Data Pipeline & Data Observability

## 1. Thong Tin Bai Nop

| Thong tin | Noi dung |
| --- | --- |
| Khoa/Lop | K4 |
| Ten nhom | Can bo sung |
| Repository | Can bo sung |
| Ngay hoan thanh | 2026-09-25 |

### Thanh Vien Va Phan Cong

Nhom can dien ho ten, MSSV va link bao cao ca nhan truoc khi nop LMS. Phan cong ky thuat khuyen nghi:

| Vai tro | Module/deliverable |
| --- | --- |
| Source owner | `src/ingestion/crossref.py`, `data/raw/` |
| Data model owner | `src/ingestion/cleaning.py`, `data/clean/`, `data/eval/test_set.json` |
| Observability owner | `src/observability/quality.py`, `data/quality/` |
| Integration owner | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `data/results/`, `data/reports/` |

## 2. Tom Tat Ket Qua

Pipeline da hoan thanh luong end-to-end cho du lieu Crossref snapshot/local fallback: raw preservation, cleaning, quality gate Great Expectations 1.x, freshness SLA, Chroma index, evaluation baseline, synthetic corruption, repair tu raw records va bao cao so sanh 3 trang thai. Baseline tao du 24 clean records, 10 cau hoi benchmark va dat `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`. Corruption suite tiem du 6 loi: drop latest records, blank summary, inject noise, truncate title, stale date va duplicate rows. Sau corruption, quality gate fail, freshness fail, retrieval hit rate giam xuong `0.5`, token F1 giam xuong `0.5121`. Repair doc lai `data/raw/crossref_records.json`, build lai clean dataset 24 dong va phuc hoi metrics ve baseline.

## 3. Kien Truc Va Luong Du Lieu

```text
Crossref snapshot/API
    -> data/raw/crossref_response.json
    -> data/raw/crossref_records.json
    -> data/clean/papers_clean.*
    -> data/chroma + data/embeddings/papers_embeddings.json
    -> data/eval/test_set.json
    -> data/results/baseline_metrics.json
    -> data/quality/baseline_quality_report.json
    -> corruption + re-index + re-evaluate
    -> repair from raw records
    -> data/reports/corruption_report.md
```

| Khoi | Input | Xu ly chinh | Output |
| --- | --- | --- | --- |
| Ingestion | Crossref API hoac snapshot | Retry/fallback, parse DOI/title/abstract/authors/date | `data/raw/crossref_records.json` |
| Cleaning | Raw records | Normalize text, remove duplicates, compute `age_days`, build `text_for_embedding` | `data/clean/papers_clean.csv/json` |
| Index | Clean dataframe | Embed documents, create Chroma collection | `data/chroma/`, `data/embeddings/` |
| Evaluation | Test set + index | Retrieval hit, token F1, heuristic/LLM judge | `data/results/*_metrics.json` |
| Observability | Dataframe | GX 1.x expectations + freshness SLA | `data/quality/` |
| Corruption/repair | Clean/raw data | Inject 6 corruptions, repair from raw | `corruption_log.json`, repaired artifacts |

## 4. Cach Tai Hien Ket Qua

```bash
source .venv/bin/activate
python script/run_phase1.py
python script/run_corruption_flow.py
```

Da kiem chung thanh cong tren Python `3.12.14`.

| Lenh | Trang thai | Bang chung |
| --- | --- | --- |
| `python script/run_phase1.py` | Thanh cong | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| `python script/run_corruption_flow.py` | Thanh cong | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Cau Hinh

| Cau hinh | Gia tri |
| --- | --- |
| LLM provider | `gemini` mac dinh; evaluator fallback heuristic khi khong co API key |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` voi fallback hashing offline |
| Records | 24 raw records, 24 clean records |
| Test set | 10 cau hoi, 4 loai: summary/authors/date/categories |
| Vector store | ChromaDB persistent local |
| Collections | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| `top_k` | 4 |
| Freshness threshold | 180 days, max stale ratio 25% |

## 6. Baseline Metrics

| Metric | Gia tri |
| --- | ---: |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5.0000 |

Baseline quality: `success=True`, `gx_success=True`, `freshness_success=True`, row count `24`.

## 7. Quality Va Freshness

Great Expectations 1.x duoc chay voi ephemeral context va pandas datasource. Cac checks chinh:

| Check | Ky vong |
| --- | --- |
| Row count | 5 den 5000 |
| Not null | `paper_id`, `title`, `text_for_embedding` |
| Unique | `paper_id` |
| Summary length | `summary` toi thieu 30 ky tu, `mostly=0.95` |

Freshness baseline: latest `2026-07-22`, oldest `2026-03-28`, stale rows `1/24`, stale ratio `4.17%`, status fresh.

## 8. Corruption Va Repair

| Corruption | Record bi tac dong | Signal ky vong |
| --- | ---: | --- |
| Drop latest records | 5 | Missing fresh docs, lower retrieval hit |
| Blank summary | 3 | Summary length failure, weaker answers |
| Inject noise | 3 | Lower semantic quality |
| Truncate title | 4 | Exact title lookup broken |
| Stale date | 7 | Freshness failure |
| Duplicate rows | 2 | Unique `paper_id` failure |

Corrupted quality: `success=False`, `gx_success=False`, `freshness_success=False`, row count `21`, stale ratio `42.86%`.

Repair strategy: rebuild clean dataframe from `data/raw/crossref_records.json`, regenerate Chroma collection `papers-repaired`, then evaluate with the same `data/eval/test_set.json`.

## 9. So Sanh 3 Trang Thai

| Metric/signal | Baseline | Corrupted | Repaired | Ket luan |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | Corruption lam mat nua ground-truth retrieval hits |
| `mean_token_f1` | 1.0000 | 0.5121 | 1.0000 | Blank/noisy/missing data lam cau tra loi kem hon |
| `judge_accuracy` | 1.0000 | 0.5000 | 1.0000 | Chat luong answer phuc hoi sau repair |
| `mean_judge_score` | 5.0000 | 2.8000 | 5.0000 | Repair dua score ve baseline |
| Quality success | True | False | True | GX bat duoc duplicate va summary length |
| Freshness success | True | False | True | Stale ratio vuot nguong trong corrupted |

Hai chuoi nhan qua chinh:

1. Drop latest records + truncate titles + blank summaries -> quality/freshness fail va context thieu -> retrieval hit rate giam tu `1.0` xuong `0.5`.
2. Repair tu raw records -> clean schema/freshness tro lai pass -> hit rate, token F1 va judge score phuc hoi ve baseline.

## 10. Gioi Han Va Huong Cai Thien

| Gioi han | Anh huong | Huong cai thien |
| --- | --- | --- |
| Khong co API key trong repo | LLM judge that fallback heuristic | Dien key cuc bo trong `.env`, khong commit secret |
| MiniLM co the chua cache tren may moi | Fallback hashing giup demo offline nhung khong thay the embedding san xuat | Set `ALLOW_MODEL_DOWNLOAD=1` de tai MiniLM khi co mang |
| Bao cao ca nhan chua dien | Chua du dieu kien nop LMS | Moi thanh vien tao `report/<MSSV>_HoTen.md` |

## 11. Checklist Truoc Khi Nop

- [x] `python script/run_phase1.py` exit code 0.
- [x] `python script/run_corruption_flow.py` exit code 0.
- [x] Baseline/corrupted/repaired dung cung evaluation set.
- [x] Metrics khop voi `data/results/*.json`.
- [x] Quality/freshness khop voi `data/quality/*.json`.
- [ ] Dien thong tin nhom, MSSV, repository.
- [ ] Moi thanh vien hoan thanh bao cao ca nhan.
- [ ] Kiem tra khong commit `.env` hoac API key.
