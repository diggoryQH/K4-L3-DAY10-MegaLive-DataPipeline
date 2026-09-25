# Corruption, Repair, and Impact Report

## Metric Comparison

| Metric | Baseline | Corrupted | Repaired | Corruption Delta | Repair Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `retrieval_hit_rate` | 100.00% | 50.00% | 100.00% | -50.00 pp | +50.00 pp |
| `mean_token_f1` | 100.00% | 51.21% | 100.00% | -48.79 pp | +48.79 pp |
| `judge_accuracy` | 100.00% | 50.00% | 100.00% | -50.00 pp | +50.00 pp |
| `mean_judge_score` | 5.0000 | 2.8000 | 5.0000 | -2.2000 | +2.2000 |

## Quality Signals

| Signal | Corrupted | Repaired |
| --- | --- | --- |
| Overall quality success | False | True |
| GX success | False | True |
| Freshness success | False | True |
| Row count | 21 | 24 |
| Stale ratio | 42.86% | 4.17% |
| Stale rows | 9 | 1 |

## Corrupted Expectations

| Expectation | Success | Observed | Unexpected |
| --- | --- | ---: | ---: |
| `expect_table_row_count_to_be_between` | True | 21 | N/A |
| `expect_column_values_to_not_be_null` | True | N/A | 0 |
| `expect_column_values_to_be_unique` | False | N/A | 4 |
| `expect_column_values_to_not_be_null` | True | N/A | 0 |
| `expect_column_values_to_not_be_null` | True | N/A | 0 |
| `expect_column_value_lengths_to_be_between` | False | N/A | 3 |

## Repair Interpretation

The corrupted run intentionally removes recent records, blanks summaries, injects noise, truncates titles, makes records stale, and duplicates rows. The quality gate is expected to fail on completeness, uniqueness, length, or freshness signals. Repair rebuilds the clean dataset from the preserved raw records and reuses the same evaluation set, so metric changes are attributable to data state rather than test drift.
