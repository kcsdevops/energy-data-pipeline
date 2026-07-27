# Architecture notes - Energy Data Platform

## Context

Built for an energy/utilities client processing smart-meter readings, field-sensor telemetry and billing exports at high volume. The goal: reliable, auditable data from raw ingestion through business-ready KPIs, without paying for compute that sits idle between processing windows.

## Design decisions

Medallion architecture (bronze/silver/gold) - bronze is the immutable source of truth for audit and reprocessing; silver enforces schema and data quality; gold is what BI and anomaly-detection consumers actually query.

AKS with a scale-to-zero job node pool - the system node pool stays up for cluster control-plane needs; the jobs node pool (tainted workload=etl-medallion) scales from 0 to N only while a bronze/silver/gold job is actually running, then back to 0.

Delta tables for silver/gold - ACID merges (MERGE INTO) let the silver stage upsert by meter_id + reading_ts_utc instead of blindly overwriting.

Anomaly flag in gold, not a separate ML pipeline - the initial anomaly signal (readings beyond 3 standard deviations from the substation's rolling average) is computed directly in the aggregation job.

## What would change for a larger deployment

- Introduce Azure Event Hubs ahead of bronze for true streaming ingestion.
- Move orchestration to Argo Workflows or Azure Data Factory once the DAG has conditional branches or needs backfill tooling.
- Add Great Expectations or a similar data-quality framework at the silver boundary.
