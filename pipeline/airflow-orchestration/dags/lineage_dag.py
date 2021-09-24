
import datetime
import os

from openlineage.airflow import DAG
from airflow.models import Variable
from airflow.contrib.sensors.gcs_sensor import GoogleCloudStorageObjectSensor
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocDeleteClusterOperator,
    DataprocSubmitJobOperator
)

PROJECT_ID = Variable.get("project_id")
DATAPROC_CLUSTER_NAME = Variable.get("dataproc_cluster_name")
DATAPROC_REGION = Variable.get("dataproc_region")
GCS_BUCKET = Variable.get("gcs_bucket")
OPENLINEAGE_URL = os.getenv('OPENLINEAGE_URL')


# [START composer_simple_define_dag]
default_dag_args = {
    'start_date': datetime.datetime(2021, 1, 1),
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=2),
    'project_id': PROJECT_ID
}

today = datetime.datetime.today()
file_date=today.strftime('%Y%m%d')

input_file_prefix="input"
input_file_suffix="confirmed-cases.parquet"
input_full_path_today="{}/{}-{}".format(input_file_prefix, file_date, input_file_suffix)

output_prefix="output"
output_suffix="summary-state"
output_full_path_today="{}/{}-{}".format(output_prefix, file_date, output_suffix)

with DAG(
    'lineage_dag',
    schedule_interval=None, #datetime.timedelta(days=1),
    default_args=default_dag_args) as dag:

    # [START gcs_today_file_sensor]
    gcs_file_sensor = GoogleCloudStorageObjectSensor(
        task_id='gcs_today_file_sensor',
        bucket=GCS_BUCKET,
        object=input_full_path_today, 
        timeout=30)      
    # [END gcs_today_file_sensor]

    # [START create_cluster]
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_cluster",
        project_id=PROJECT_ID,
        cluster_config={
            "master_config": {
                "num_instances": 1,
                "machine_type_uri": "n1-standard-2",
                "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 50}
            },
            "worker_config": {
                "num_instances": 2,
                "machine_type_uri": "n1-standard-4",
                "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 50}
            }
        },
        region=DATAPROC_REGION,
        location=DATAPROC_REGION,
        cluster_name=DATAPROC_CLUSTER_NAME,
    )
    # [END create_cluster]    

    # [START spark_task]
    spark_task = DataprocSubmitJobOperator(
        task_id="spark_task", 
        job={
            "reference": {"project_id": PROJECT_ID},
            "placement": {
                "cluster_name": DATAPROC_CLUSTER_NAME
            },
            "spark_job": {
                "jar_file_uris": [
                    "gs://{}/jars/spark-lineage-sample_2.12-0.1.jar".format(GCS_BUCKET),
                    "gs://{}/jars/openlineage-spark-0.2.2.jar".format(GCS_BUCKET)
                ],
                "main_class": "org.spark.lineage.LineageApp",
                "args": [
                    "gs://{}/{}".format(GCS_BUCKET, input_full_path_today),
                    "gs://{}/{}".format(GCS_BUCKET, output_full_path_today)
                ],
                "properties": [
                    ("spark.extraListeners", "io.openlineage.spark.agent.OpenLineageSparkListener"),
                    ("spark.openlineage.host", OPENLINEAGE_URL),
                    ("spark.openlineage.namespace", "covid-demo"),
                    ("spark.openlineage.parentJobName", "lineage_dag.spark_task")
                ]
            },
        }, 
        region=DATAPROC_REGION,
        project_id=PROJECT_ID,
        location=DATAPROC_REGION
    )    
    # [END spark_task]    

    # [START delete_cluster]
    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_cluster", 
        project_id=PROJECT_ID, 
        cluster_name=DATAPROC_CLUSTER_NAME, 
        region=DATAPROC_REGION,
        location=DATAPROC_REGION,
        trigger_rule="all_done"
    )
    # [END delete_cluster] 

    gcs_file_sensor >> create_cluster >> spark_task >> delete_cluster
# [END composer_simple]