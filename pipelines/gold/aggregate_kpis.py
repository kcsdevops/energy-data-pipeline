"""
Gold layer - business-ready aggregates.

Builds consumption KPIs by region/substation and flags statistical outliers
as candidate grid anomalies, ready for BI dashboards and the anomaly-review
workflow.
"""
from pyspark.sql import SparkSession, functions as F


def build_consumption_kpis(spark: SparkSession, silver_path: str, gold_path: str) -> None:
      silver = spark.read.format("delta").load(silver_path)

    kpis = (
              silver
              .groupBy("region", "substation_id", "ingestion_date")
              .agg(
                            F.sum("consumption_kwh").alias("total_consumption_kwh"),
                            F.avg("consumption_kwh").alias("avg_consumption_kwh"),
                            F.stddev("consumption_kwh").alias("stddev_consumption_kwh"),
                            F.count("*").alias("reading_count"),
              )
              .withColumn(
                            "anomaly_flag",
                            F.when(
                                              F.col("avg_consumption_kwh") > (F.col("avg_consumption_kwh") + 3 * F.col("stddev_consumption_kwh")),
                                              True,
                            ).otherwise(False),
              )
    )

    kpis.write.format("delta").partitionBy("ingestion_date").mode("overwrite").save(gold_path)
    print(f"[gold] wrote {kpis.count()} aggregated KPI rows -> {gold_path}")


if __name__ == "__main__":
      spark = SparkSession.builder.appName("gold-aggregate-energy").getOrCreate()
      build_consumption_kpis(
          spark,
          silver_path="abfss://silver@energydatalakeprod.dfs.core.windows.net/meter_readings/",
          gold_path="abfss://gold@energydatalakeprod.dfs.core.windows.net/consumption_kpis/",
      )
  
