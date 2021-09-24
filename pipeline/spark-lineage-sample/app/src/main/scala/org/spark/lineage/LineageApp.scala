package org.spark.lineage

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object LineageApp {

  def main(args: Array[String]): Unit = {

    val sourceFile = args(0)
    val outputFile = args(1)

    // create Spark context with Spark configuration
    val spark: SparkSession = SparkSession.builder()
      .master("local[*]")
      .appName("Covid cases")
      .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    try {
      val covidCases =  spark.read.parquet(sourceFile)

      val top10States =
        covidCases
        .groupBy("state")
        .agg(count("*").as("cnt"))
        .orderBy(desc("cnt"))
        .limit(10)

      top10States.write.option("header", "true").mode("overwrite").csv(outputFile)
    }
    finally {
      spark.stop()
    }
  }
}
