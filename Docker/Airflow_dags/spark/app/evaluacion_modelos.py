from pyspark.sql.types import *
from pyspark.sql import SparkSession
from fbprophet import Prophet
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.functions import current_date
from pyspark.sql.types import *
from pyspark import SparkContext
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt
from datetime import date
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri('http://mlflow_server:5000')

master = 'local'

# Create Spark session
spark = SparkSession.builder \
    .master(master) \
    .getOrCreate()

print("Se declara el esquema")

new_forecasts_schema = StructType([
  StructField('ds',DateType()),
  StructField('store',IntegerType()),
  StructField('item',IntegerType()),
  StructField('y',FloatType()),
  StructField('yhat',FloatType()),
  StructField('yhat_upper',FloatType()),
  StructField('yhat_lower',FloatType()),
  StructField('interval_width',FloatType()),
  StructField('growth',StringType()),
  StructField('daily_seasonality',BooleanType()),
  StructField('weekly_seasonality',BooleanType()),
  StructField('seasonality_mode',StringType()),
  StructField('yearly_seasonality',BooleanType()),
  ])

print("Se lee el fichero de las predicciones, guardado en hdfs")
new_forecasts = spark.read.parquet(
  'hdfs://hdfs:9000//new_forecasts/', 
  schema=new_forecasts_schema
)

new_forecasts.show()

print("Se crea la vista temporal new_forecasts para poder consultarla desde sql")
new_forecasts.createOrReplaceTempView('new_forecasts')

print("Se crea el esquema para el resultado de la evaluacion")
eval_schema =StructType([
  StructField('training_date', DateType()),
  StructField('store', IntegerType()),
  StructField('item', IntegerType()),
  StructField('mae', FloatType()),
  StructField('mse', FloatType()),
  StructField('rmse', FloatType())
  ])


@pandas_udf( eval_schema, PandasUDFType.GROUPED_MAP )
def evaluate_forecast( evaluation_pd ):
  mlflow.set_tracking_uri('http://mlflow_server:5000')
  try:
    experiment_id = mlflow.create_experiment(name="ev_modelosv4", artifact_location='http://mlflow_server:5000/mlflow/')
  except:
    experiment_id = mlflow.get_experiment_by_name(name="ev_modelosv4").experiment_id  
  with mlflow.start_run(experiment_id=experiment_id, run_name="store={0}_item{1}".format(evaluation_pd['store'].iloc[0],
            evaluation_pd['item'].iloc[0])):
      # get store & item in incoming data set
      training_date = evaluation_pd['training_date'].iloc[0]
      store = evaluation_pd['store'].iloc[0]
      item = evaluation_pd['item'].iloc[0]
      
      print("Evaluacion_modelo_{0}_{1}".format(store,item))
      # calulate evaluation metrics
      mae = mean_absolute_error( evaluation_pd['y'], evaluation_pd['yhat'] )
      mse = mean_squared_error( evaluation_pd['y'], evaluation_pd['yhat'] )
      rmse = sqrt( mse )
      
      mlflow.log_metric('mae', mae)
      mlflow.log_metric('mse', mse)
      mlflow.log_metric('rmse', rmse)

      mlflow.log_param('store', store)
      mlflow.log_param('item', item)
      mlflow.log_param('interval_width', evaluation_pd['interval_width'].iloc[0])
      mlflow.log_param('growth', evaluation_pd['growth'].iloc[0])
      mlflow.log_param('daily_seasonality', evaluation_pd['daily_seasonality'].iloc[0])
      mlflow.log_param('weekly_seasonality', evaluation_pd['weekly_seasonality'].iloc[0])
      mlflow.log_param('yearly_seasonality', evaluation_pd['yearly_seasonality'].iloc[0])
      mlflow.log_param('seasonality_mode', evaluation_pd['seasonality_mode'].iloc[0])

      # assemble result set
      results = {'training_date':[training_date], 'store':[store], 'item':[item], 'mae':[mae], 'mse':[mse], 'rmse':[rmse]}
  
  mlflow.end_run()
  return pd.DataFrame.from_dict( results )


# calculate metrics
results = (
  spark
    .table('new_forecasts')
    .filter('ds < \'2018-01-01\'') # limit evaluation to periods where we have historical data
    .select('training_date', 'store', 'item', 'y', 'yhat','interval_width','growth',
      'daily_seasonality','weekly_seasonality','yearly_seasonality','seasonality_mode')
    .groupBy('training_date', 'store', 'item')
    .apply(evaluate_forecast)
    )


print("RESULTADOS")
results.show()
results.coalesce(1).write.mode("overwrite").parquet("hdfs://hdfs:9000/evaluacion_modelos")


