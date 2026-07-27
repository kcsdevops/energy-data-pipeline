# Energy Data Platform - Medallion Architecture on AKS

Reference implementation of a data lake platform for an energy/utilities client: metering, consumption and grid-sensor data flowing through a bronze -> silver -> gold medallion pipeline, provisioned entirely with Infrastructure as Code and orchestrated in CI/CD via Azure DevOps.

> This repository is a portfolio/reference build reproducing the architecture and patterns used in a real energy-sector engagement, with client-identifying details removed.

## Why this exists

Energy/utilities data (smart meter readings, consumption telemetry, field equipment sensors) arrives high-volume, semi-structured and error-prone. This project shows how to take that raw data and turn it into governed, query-ready datasets for billing, anomaly detection and regulatory reporting - without keeping compute running 24x7.

## Medallion layers

| Layer | Purpose | Format | Notes |
|---|---|---|---|
| Bronze | Raw, immutable landing zone. Exactly what the source sent, no transformation. | JSON / CSV as received | Partitioned by ingestion date. Never overwritten. |
| Silver | Cleaned, validated, deduplicated, schema-enforced. | Delta / Parquet | Type casting, null handling, meter-ID reconciliation, timezone normalization. |
| Gold | Business-ready aggregates. | Delta / Parquet | Consumption by region/substation/customer segment, anomaly flags, regulatory KPIs. |

See pipelines/ for the transformation logic at each stage.

## Infrastructure as Code

All infrastructure is provisioned with Terraform under terraform/:

- modules/datalake - Azure Data Lake Storage Gen2 account with bronze, silver and gold containers, lifecycle policies (auto-tier raw data to cool/archive after N days), and access via managed identity.
- modules/aks - AKS cluster sized for batch/job workloads (system + user node pools), with the user pool configured for scale-to-zero - the pipeline provisions job nodes only when a run is triggered and they scale back down afterward, avoiding idle compute cost.
- environments/prod - environment composition wiring the modules together, with remote state and cost tags per project/cost center.

## Kubernetes jobs

Each medallion stage runs as its own Kubernetes workload under k8s/jobs:

- bronze-ingest-cronjob.yaml - scheduled ingestion from source systems into the bronze layer.
- silver-transform-job.yaml - triggered job that cleans and validates bronze data into silver.
- gold-aggregate-job.yaml - triggered job that aggregates silver data into gold KPIs.

Node pools scale up for the duration of each job and back down once it completes, so compute cost tracks actual processing time rather than a fixed cluster footprint.

## CI/CD - Azure DevOps

azure-pipelines/azure-pipelines.yml defines the full pipeline: terraform plan/apply for infra changes, build and push pipeline container images, deploy/trigger the bronze -> silver -> gold Kubernetes jobs in sequence, and scale the AKS user node pool back to zero after the run.

## Repository structure

- terraform/modules/aks - AKS cluster with scale-to-zero job node pool
- terraform/modules/datalake - ADLS Gen2 with bronze/silver/gold containers
- terraform/environments/prod - environment composition
- pipelines/bronze - raw ingestion
- pipelines/silver - cleaning and validation
- pipelines/gold - business aggregation
- k8s/jobs - Kubernetes CronJob/Job manifests
- azure-pipelines - Azure DevOps CI/CD pipeline
- docs/architecture.md - extended architecture notes

## License

MIT - see LICENSE.
