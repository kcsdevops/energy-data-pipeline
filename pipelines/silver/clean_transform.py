"""Silver layer: cleaning, validation, dedup and upsert for meter readings.

Reads raw JSON from the bronze layer, applies type casts and basic data
quality rules, deduplicates by meter and reading timestamp, and merges
(upsert) into a Delta table. Uses a merge for incremental runs and a plain
write for the first run when the Delta table does not exist yet.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col
from delta.tables import DeltaTable


def clean_meter_readings(spark: SparkSession, bronze_path: str, silver_path: str) -> None:
    """Clean, validate, dedupe and upsert bronze meter readings into silver.

    Args:
        spark: active SparkSession.
        bronze_path: path to the bronze smart_meter_readings dataset.
        silver_path: path to the silver Delta table.
    """
    raw: DataFrame = spark.read.json(bronze_path)

    clean = (
        raw
        .withColumn("consumption_kwh", col("consumption_kwh").cast("double"))
        .withColumn("voltage", col("voltage").cast("double"))
        .withColumn("reading_ts_utc", col("reading_ts_utc").cast("timestamp"))
        .filter(col("consumption_kwh") >= 0)
        .filter((col("voltage") >= 180) & (col("voltage") <= 260))
        .dropDuplicates(["meter_id", "reading_ts_utc"])
    )

    if DeltaTable.isDeltaTable(spark, silver_path):
        target = DeltaTable.forPath(spark, silver_path)
        (
            target.alias("t")
            .merge(clean.alias("s"), "t.meter_id = s.meter_id AND t.reading_ts_utc = s.reading_ts_utc")
            .whenNotMatchedInsertAll()
            .execute()
        )
        print(f"Merged {clean.count()} rows into existing silver table at {silver_path}")
    else:
        (
            clean.write
            .format("delta")
            .partitionBy("ingestion_date")
            .save(silver_path)
        )
        print(f"Created silver table at {silver_path} with {clean.count()} rows")


if __name__ == "__main__":
    spark = SparkSession.builder.appName("silver-clean-transform").getOrCreate()

    clean_meter_readings(
        spark,
        bronze_path="abfss://bronze@energydatalakeprod.dfs.core.windows.net/smart_meter_readings",
        silver_path="abfss://silver@energydatalakeprod.dfs.core.windows.net/meter_readings",
    )
