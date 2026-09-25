from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the baseline phase report from actual pipeline artifacts."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in source_summary.items():
        lines.append(f"| `{key}` | {_fmt(value)} |")

    lines.extend(
        [
            "",
            "## Evaluation Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| `samples` | {_fmt(metrics.get('samples'))} |",
            f"| `retrieval_hit_rate` | {_pct(metrics.get('retrieval_hit_rate'))} |",
            f"| `mean_token_f1` | {_pct(metrics.get('mean_token_f1'))} |",
            f"| `judge_accuracy` | {_pct(metrics.get('judge_accuracy'))} |",
            f"| `mean_judge_score` | {_num(metrics.get('mean_judge_score'))} |",
            f"| `ragas` | {_fmt(metrics.get('ragas'))} |",
            "",
            "## Data Quality",
            "",
            f"- Overall success: **{quality.get('success')}**",
            f"- GX success: **{quality.get('gx_success')}**",
            f"- Freshness success: **{quality.get('freshness_success')}**",
            f"- Row count: **{quality.get('row_count')}**",
            "",
            "| Expectation | Success | Observed | Unexpected |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for item in quality.get("expectations", []):
        lines.append(
            "| "
            f"`{item.get('expectation_type')}` | "
            f"{item.get('success')} | "
            f"{_fmt(item.get('observed_value'))} | "
            f"{_fmt(item.get('unexpected_count'))} |"
        )

    lines.extend(
        [
            "",
            "## Freshness SLA",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in freshness.items():
        lines.append(f"| `{key}` | {_fmt(value)} |")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "The baseline run preserves raw lineage, produces a cleaned embedding dataset, "
            "indexes the corpus, evaluates the same benchmark set used later for comparison, "
            "and records data quality plus freshness signals for observability.",
            "",
        ]
    )
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write the three-state corruption and repair comparison report."""
    rows = []
    for metric in ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]:
        baseline = baseline_metrics.get(metric)
        corrupted = corrupted_metrics.get(metric)
        repaired = repaired_metrics.get(metric)
        rows.append(
            [
                f"`{metric}`",
                _metric(metric, baseline),
                _metric(metric, corrupted),
                _metric(metric, repaired),
                _delta(metric, baseline, corrupted),
                _delta(metric, corrupted, repaired),
            ]
        )

    lines = [
        "# Corruption, Repair, and Impact Report",
        "",
        "## Metric Comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Corruption Delta | Repair Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## Quality Signals",
            "",
            "| Signal | Corrupted | Repaired |",
            "| --- | --- | --- |",
            f"| Overall quality success | {corrupted_quality.get('success')} | {repaired_quality.get('success')} |",
            f"| GX success | {corrupted_quality.get('gx_success')} | {repaired_quality.get('gx_success')} |",
            f"| Freshness success | {corrupted_quality.get('freshness_success')} | {repaired_quality.get('freshness_success')} |",
            f"| Row count | {corrupted_quality.get('row_count')} | {repaired_quality.get('row_count')} |",
            f"| Stale ratio | {_pct(corrupted_freshness.get('stale_ratio'))} | {_pct(repaired_freshness.get('stale_ratio'))} |",
            f"| Stale rows | {corrupted_freshness.get('stale_rows')} | {repaired_freshness.get('stale_rows')} |",
            "",
            "## Corrupted Expectations",
            "",
            "| Expectation | Success | Observed | Unexpected |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for item in corrupted_quality.get("expectations", []):
        lines.append(
            "| "
            f"`{item.get('expectation_type')}` | "
            f"{item.get('success')} | "
            f"{_fmt(item.get('observed_value'))} | "
            f"{_fmt(item.get('unexpected_count'))} |"
        )

    lines.extend(
        [
            "",
            "## Repair Interpretation",
            "",
            "The corrupted run intentionally removes recent records, blanks summaries, injects noise, "
            "truncates titles, makes records stale, and duplicates rows. The quality gate is expected "
            "to fail on completeness, uniqueness, length, or freshness signals. Repair rebuilds the "
            "clean dataset from the preserved raw records and reuses the same evaluation set, so metric "
            "changes are attributable to data state rather than test drift.",
            "",
        ]
    )
    write_text(report_path, "\n".join(lines))


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return _num(value)
    if value is None:
        return "N/A"
    text = str(value).replace("\n", " ")
    return text if len(text) <= 120 else text[:117] + "..."


def _num(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return _fmt(value)


def _pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.2f}%"
    return _fmt(value)


def _metric(metric: str, value: Any) -> str:
    return _num(value) if metric == "mean_judge_score" else _pct(value)


def _delta(metric: str, before: Any, after: Any) -> str:
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return "N/A"
    delta = float(after) - float(before)
    if metric == "mean_judge_score":
        return f"{delta:+.4f}"
    return f"{delta * 100:+.2f} pp"
