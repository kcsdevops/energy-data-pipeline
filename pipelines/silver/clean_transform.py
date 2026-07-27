"""
Silver layer - cleaning, validation and schema enforcement.

Reads the latest bronze partition, deduplicates by meter ID + reading
timestamp, normalizes timezones, casts types, drops records that fail basic
sanity checks (negative consumption, out-of-range voltage), and writes the
result as Delta tables partitioned by date and region.
"""
from pyspark.sql import SparkSession, functions as F
from delta.tables import DeltaTable


def clean_meter_readings(spark: SparkSession, bronze_path: str, silver_path: str) -> None:
      raw = spark.read.json(bronze_path)

    cleaned = (
              raw
              .withColumn("reading_ts_utc", F.to_utc_timestamp("reading_timestamp", "local_tz"))
              .withColumn("consumption_kwh", F.col("consumption_kwh").cast("double"))
              .filter(F.col("consumption_kwh") >= 0)
              .filter(F.col("voltage").between(180, 260))
              .dropDuplicates(["meter_id", "reading_ts_utc"])
              .withColumn("ingestion_date", F.to_date("reading_ts_utc"))
    )

    if DeltaTable.isDeltaTable(spark, silver_path):
              target = DeltaTable.forPath(spark, silver_path)
              (
                  target.alias("t")
                  .merge(cleaned.alias("s"), "t.meter_id = s.meter_id AND t.reading_ts_utc = s.reading_ts_utc")
                  .whenNotMatchedInsertAll()
                  .execute()
              )
else:
          cleaned.write.format("delta").partitionBy("ingestion_date", "region").mode("overwrite").save(silver_path)

    print(f"[silver] wrote {cleaned.count()} validated records -> {silver_path}")


if __name__ == "__main__":
      spark = SparkSession.builder.appName("silver-transform-energy").getOrCreate()
      clean_meter_readings(
          spark,
          bronze_path="abfss://bronze@energydatalakeprod.dfs.core.windows.net/smart_meter_readings/",
          silver_path="abfss://silver@energydatalakeprod.dfs.core.windows.net/meter_readings/",
      )
  
