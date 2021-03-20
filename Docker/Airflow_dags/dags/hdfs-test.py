from airflow import DAG
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.contrib.operators.sftp_operator import SFTPOperator
from datetime import datetime


default_args = {'owner': 'airflow',
                'depends_on_past': False,
                'provide_context': True,
                'start_date': datetime(2020, 3, 19, 0, 0),
                'email': ['airflow@airflow.com'],
                'email_on_failure': False,
                'email_on_retry': False,
                'retries': 0,
                'concurrency': 1
                }

dag_name = 'test_sensor_dag'

dag = DAG(
    dag_id=dag_name,
    default_args=default_args)

sftp_file_to_container_hdfs = SFTPOperator(
    task_id='sftp_file_to_container_hdfs',
    ssh_conn_id="ssh_default",
    local_filepath="/usr/local/spark/resources/1.log",
    remote_filepath="/hadoop/data/3.log",
    operation="put",
    dag=dag
)

put_file_in_hdfs = SSHOperator(
    task_id='put_file_in_hdfs',
    ssh_conn_id="ssh_default",
    command=' cd /hadoop/bin && ./hdfs dfs -put /hadoop/data/3.log /',
    dag=dag
)

sftp_file_to_container_hdfs
put_file_in_hdfs