from pyspark.sql import SparkSession
from pyspark.sql.functions import (from_json, col, to_timestamp, lit,
                                   when, coalesce, concat_ws)
from pyspark.sql.types import *

spark = (SparkSession.builder
    .appName("upi-fraud")
    .master("local[2]")
    .config("spark.driver.memory", "1g")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,"
            "org.postgresql:postgresql:42.7.3")
    .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

JDBC_URL = "jdbc:postgresql://localhost:5432/upidb"
PROPS = {"user": "upi", "password": "upi", "driver": "org.postgresql.Driver"}

def read_pg(query):
    return spark.read.jdbc(JDBC_URL, f"({query}) AS t", properties=PROPS)

row = StructType([
    StructField("txn_id", LongType()),
    StructField("user_id", IntegerType()),
    StructField("device_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("merchant", StringType()),
    StructField("city", StringType()),
    StructField("status", StringType()),
    StructField("created_at", StringType()),
])
envelope = StructType([StructField("after", row), StructField("op", StringType())])

raw = (spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:19092")
    .option("subscribe", "upi.public.transactions")
    .option("startingOffsets", "latest")
    .load())

txns = (raw.select(from_json(col("value").cast("string"), envelope).alias("e"))
    .where("e.op = 'c'")
    .select("e.after.*")
    .withColumn("event_time", to_timestamp(col("created_at"))))

def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    # Reference data from Postgres
    velocity = read_pg("SELECT user_id AS v_user, COUNT(*) AS txn_last_min "
                       "FROM transactions "
                       "WHERE created_at > now() - interval '60 seconds' "
                       "GROUP BY user_id")
    avgs = read_pg("SELECT user_id AS a_user, AVG(amount)::float8 AS avg_amount "
                   "FROM transactions "
                   "WHERE created_at < now() - interval '1 minute' "
                   "GROUP BY user_id")
    known = read_pg("SELECT device_id AS known_device FROM devices")

    b = (batch_df
        .join(velocity, batch_df.user_id == velocity.v_user, "left")
        .join(avgs, batch_df.user_id == avgs.a_user, "left")
        .join(known, batch_df.device_id == known.known_device, "left"))

    b = (b
        .withColumn("r_velocity", coalesce(col("txn_last_min") > 5, lit(False)))
        .withColumn("r_amount", coalesce((col("amount") > 5 * col("avg_amount"))
                                         & (col("amount") > 5000), lit(False)))
        .withColumn("r_device", col("known_device").isNull()
                                & (col("amount") > 10000))
        .withColumn("reasons", concat_ws(",",
            when(col("r_velocity"), lit("VELOCITY")),
            when(col("r_amount"), lit("HIGH_AMOUNT")),
            when(col("r_device"), lit("NEW_DEVICE")))))

    flagged = b.where(col("reasons") != "")
    if not flagged.isEmpty():
        print(f"\n*** FRAUD ALERT (batch {batch_id}) ***")
        flagged.select("txn_id", "user_id", "device_id", "amount",
                       "txn_last_min", "reasons").show(truncate=False)

(txns.writeStream
    .foreachBatch(process_batch)
    .trigger(processingTime="2 seconds")
    .option("checkpointLocation", "/tmp/spark-chk-fraud")
    .start().awaitTermination())
