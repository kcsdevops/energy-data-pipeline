"""Bronze layer: raw ingestion for the energy data medallion pipeline.

Reads raw source extracts (smart meter readings, field sensor telemetry,
billing export) and lands them as-is, partitioned by ingestion date, with
no transformation or validation. This preserves an auditable copy of the
data exactly as received from source systems.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import lit
from datetime import date


def ingest(spark: SparkSession, source_paths: dict, bronze_root: str) -> None:
    """Copy each raw source into the bronze layer, partitioned by ingestion_date.

    Args:
        spark: active SparkSession.
        source_paths: mapping of dataset name -> source path (JSON).
        bronze_root: root path of the bronze layer (e.g. abfss://bronze@...).
    """
    ingestion_date = date.today().isoformat()

    for dataset_name, source_path in source_paths.items():
        df: DataFrame = spark.read.json(source_path)
        df = df.withColumn("ingestion_date", lit(ingestion_date))
        target_path = f"{bronze_root}/{dataset_name}"
        (
            df.write
            .mode("append")
            .partitionBy("ingestion_date")
            .format("delta")
            .save(target_path)
        )
        print(f"Ingested {dataset_name} -> {target_path} (ingestion_date={ingestion_date})")


if __name__ == "__main__":
    spark = SparkSession.builder.appName("bronze-ingest-meter-readings").getOrCreate()

    source_paths = {
        "smart_meter_readings": "abfss://landing@energydatalakeprod.dfs.core.windows.net/smart_meter_readings/",
        "field_sensor_telemetry": "abfss://landing@energydatalakeprod.dfs.core.windows.net/field_sensor_telemetry/",
        "billing_export": "abfss://landing@energydatalakeprod.dfs.core.windows.net/billing_export/",
    }

    ingest(spark, source_paths, bronze_root="abfss://bronze@energydatalakeprod.dfs.core.windows.net")
