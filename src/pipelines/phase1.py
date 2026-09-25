from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the baseline data pipeline end-to-end."""
    settings = load_settings()

    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    clean_df = build_clean_dataframe(records, now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
    else:
        test_set = read_json(settings.paths.eval_testset)

    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(records),
        "clean_rows": int(len(clean_df)),
        "evaluation_questions": len(test_set),
        "embedding_model": settings.embedding_model,
        "embedding_backend": index.embedding_backend,
        "collection_name": index.collection_name,
        "top_k": settings.top_k,
        "run_timestamp_utc": pd.Timestamp.utcnow().isoformat(),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    print("Phase 1 baseline pipeline complete.")
    print(f"Clean rows: {len(clean_df)}")
    print(f"Evaluation questions: {len(test_set)}")
    print(f"Retrieval hit rate: {bundle.summary['retrieval_hit_rate']:.3f}")
    print(f"Mean token F1: {bundle.summary['mean_token_f1']:.3f}")
