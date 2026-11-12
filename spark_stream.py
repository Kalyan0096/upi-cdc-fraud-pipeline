from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import *

spark = (SparkSession.builder
    .appName("upi-fraud")
    .master("local[2]")
    .config("spark.driver.memory", "1g")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
    .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

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
envelope = StructType([
    StructField("after", row),
    StructField("op", StringType()),
])

raw = (spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:19092")
    .option("subscribe", "upi.public.transactions")
    .option("startingOffsets", "latest")
    .load())

txns = (raw.select(from_json(col("value").cast("string"), envelope).alias("e"))
    .where("e.op = 'c'")
    .select("e.after.*")
    .withColumn("event_time", to_timestamp(col("created_at"))))

(txns.select("txn_id", "user_id", "device_id", "amount", "event_time")
    .writeStream.format("console")
    .outputMode("append")
    .option("truncate", "false")
    .start().awaitTermination())
