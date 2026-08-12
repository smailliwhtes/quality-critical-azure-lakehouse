"""Publish the current batch dimension independently of SCD2 history."""

import argparse

from common import spark
from pyspark.sql import Window
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--incident-mode", choices=["true", "false"], default="false")
args = parser.parse_args()

changes = spark.table(f"{args.catalog}.bronze.batch_change_events")
latest = Window.partitionBy("batch_id").orderBy(
    F.col("sequence_number").desc(), F.col("effective_at").desc()
)
current = (
    changes.withColumn("_rank", F.row_number().over(latest))
    .filter((F.col("_rank") == 1) & (F.col("operation") != "DELETE"))
    .select(
        "batch_id",
        "site_id",
        "product_id",
        "lot_number",
        "manufactured_at",
        "release_status",
        "effective_at",
        "sequence_number",
        "schema_version",
    )
)
current.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{args.catalog}.silver.batch_master_current"
)
