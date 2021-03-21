from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.contrib.operators.sftp_operator import SFTPOperator
from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
from datetime import datetime

spark_master = "spark://spark:7077"
spark_app_name = "Entrenamiento_modelos"
file_path = "/usr/local/airflow/airflow.cfg"

default_args = {'owner': 'airflow',
                'start_date': datetime(2020, 3, 19, 0, 0),
                }

dag_name = 'hdfs_transferv2'
file_names = ['sample_submission', 'test', 'train']

dag = DAG(
    dag_id=dag_name,
    default_args=default_args,
    schedule_interval=None)

start = DummyOperator(task_id="start", provide_context=True, dag=dag)
hito_files_hdfs = DummyOperator(task_id="hito_files_hdfs", dag=dag)
asd = [] 
for file_name in file_names:
    print("Filename: "+file_name)
    sftp_file_to_container_hdfs = SFTPOperator(
        task_id='pass_'+file_name+'_to_docker_hdfs',
        ssh_conn_id="ssh_default",
        local_filepath="/usr/local/spark/resources/{0}.csv".format(file_name),
        remote_filepath="/hadoop/data/{0}.csv".format(file_name),
        operation="put",
        dag=dag
    )

    put_file_in_hdfs = SSHOperator(
        task_id='put_'+file_name+'_in_hdfs',
        ssh_conn_id="ssh_default",
        command=" cd /hadoop/bin && ./hdfs dfs -test -e /{0}.csv; if [ `echo $?` -gt 0 ]; then ./hdfs dfs -put /hadoop/data/{0}.csv /; fi".format(file_name),
        dag=dag
    )

    asd.append(put_file_in_hdfs)
    

    start >> sftp_file_to_container_hdfs >> put_file_in_hdfs 


spark_job = SparkSubmitOperator(
    task_id="spark_job",
    application="/usr/local/spark/app/hello-world.py", # Spark application path created in airflow and spark cluster
    name=spark_app_name,
    conn_id="spark_default",
    verbose=1,
    application_args=[file_path],
    dag=dag)

end = DummyOperator(task_id="end", dag=dag)

for i in asd:
    hito_files_hdfs.set_upstream(i)
spark_job.set_upstream(hito_files_hdfs)
end.set_upstream(spark_job)