"""
Bronze layer - raw ingestion.

Pulls smart-meter readings, field-sensor telemetry and billing exports from
source systems and lands them AS-IS into ADLS Gen2 bronze/, partitioned by
ingestion date. No transformation happens here - bronze is the immutable,
audit-friendly record of exactly what was received.
"""
from datetime import datetime, timezone
from pyspark.sql import SparkSession


def ingest(source_paths: dict, bronze_root: str) -> None:
      spark = SparkSession.builder.appName("bronze-ingest-energy").getOrCreate()
      run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for source_name, path in source_paths.items():
              df = spark.read.option("multiline", "true").json(path)
              target = f"{bronze_root}/{source_name}/ingestion_date={run_date}"
              df.write.mode("append").json(target)
              print(f"[bronze] {source_name}: {df.count()} records -> {target}")


if __name__ == "__main__":
      ingest(
                source_paths={
                              "smart_meter_readings": "abfss://landing@energydatalakeprod.dfs.core.windows.net/meters/",
                              "field_sensor_telemetry": "abfss://landing@energydatalakeprod.dfs.core.windows.net/sensors/",
                              "billing_export": "abfss://landing@energydatalakeprod.dfs.core.windows.net/billing/",
                },
                bronze_root="abfss://bronze@energydatalakeprod.dfs.core.windows.net",
      )
  
