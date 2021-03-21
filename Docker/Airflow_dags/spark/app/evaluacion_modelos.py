from pyspark.sql.types import *
from pyspark.sql import SparkSession
from fbprophet import Prophet
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.functions import current_date
from pyspark.sql.types import *
from pyspark import SparkContext


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
  StructField('yhat_lower',FloatType())
  ])

print("Se lee el fichero de las predicciones, guardado en hdfs")
new_forecasts = spark.read.csv(
  'hdfs://hdfs:9000/new_forecasts.csv', 
  header=True, 
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
  
  # get store & item in incoming data set
  training_date = evaluation_pd['training_date'].iloc[0]
  store = evaluation_pd['store'].iloc[0]
  item = evaluation_pd['item'].iloc[0]
  
  # calulate evaluation metrics
  mae = mean_absolute_error( evaluation_pd['y'], evaluation_pd['yhat'] )
  mse = mean_squared_error( evaluation_pd['y'], evaluation_pd['yhat'] )
  rmse = sqrt( mse )
  
  # assemble result set
  results = {'training_date':[training_date], 'store':[store], 'item':[item], 'mae':[mae], 'mse':[mse], 'rmse':[rmse]}
  return pd.DataFrame.from_dict( results )


# calculate metrics
results = (
  spark
    .table('new_forecasts')
    .filter('ds < \'2018-01-01\'') # limit evaluation to periods where we have historical data
    .select('training_date', 'store', 'item', 'y', 'yhat')
    .groupBy('training_date', 'store', 'item')
    .apply(evaluate_forecast)
    )

print("RESULTADOS")
results.show()
results.write.csv("hdfs://hdfs:9000/evaluacion_modelos.csv")


