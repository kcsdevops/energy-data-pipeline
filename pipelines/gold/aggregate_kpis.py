"""Gold layer: consumption KPIs and anomaly flags for the energy platform.

Aggregates cleaned silver meter readings into business-ready KPIs grouped
by region, substation and ingestion date, and flags statistical anomalies
so downstream dashboards and alerting can consume a single curated table.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


def build_consumption_kpis(spark: SparkSession, silver_path: str, gold_path: str) -> None:
    """Aggregate silver meter readings into gold consumption KPIs.

    Args:
        spark: active SparkSession.
        silver_path: path to the silver meter_readings Delta table.
        gold_path: path to the gold consumption_kpis Delta table.
    """
    silver: DataFrame = spark.read.format("delta").load(silver_path)

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
                F.abs(F.col("avg_consumption_kwh") - F.col("total_consumption_kwh") / F.col("reading_count"))
                > (3 * F.coalesce(F.col("stddev_consumption_kwh"), F.lit(0))),
                F.lit(True),
            ).otherwise(F.lit(False)),
        )
    )

    (
        kpis.write
        .format("delta")
        .mode("overwrite")
        .partitionBy("ingestion_date")
        .save(gold_path)
    )
    print(f"Wrote {kpis.count()} KPI rows to {gold_path}")


if __name__ == "__main__":
    spark = SparkSession.builder.appName("gold-aggregate-kpis").getOrCreate()

    build_consumption_kpis(
        spark,
        silver_path="abfss://silver@energydatalakeprod.dfs.core.windows.net/meter_readings",
        gold_path="abfss://gold@energydatalakeprod.dfs.core.windows.net/consumption_kpis",
    )
