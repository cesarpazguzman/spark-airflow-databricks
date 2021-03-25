from pyspark.sql.types import *
from pyspark.sql import SparkSession
from fbprophet import Prophet
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.functions import current_date
from pyspark.sql.types import *
from pyspark import SparkContext

import pickle


# Create Spark session
spark = SparkSession.builder.getOrCreate()

print("Se declara el esquema")

# structure of the training data set
train_schema = StructType([
  StructField('date', DateType()),
  StructField('store', IntegerType()),
  StructField('item', IntegerType()),
  StructField('sales', IntegerType())
  ])

print(train_schema)
print("Se lee el archivo train.csv pasandole el esquema")

# read the training file into a dataframe
train = spark.read.csv(
  'hdfs://hdfs:9000/train.csv', 
  header=True, 
  schema=train_schema
)

train.show()

print("Se crea la vista temporal train para poder consultarla desde sql")
train.createOrReplaceTempView('train')

sql_statement = '''
  SELECT
    store,
    item,
    CAST(date as date) as ds,
    SUM(sales) as y
  FROM train
  GROUP BY store, item, ds
  ORDER BY store, item, ds
  '''

print(sql_statement)

store_item_history = (
  spark
    .sql( sql_statement )
    .repartition(spark.sparkContext.defaultParallelism, ['store', 'item'])
  ).cache()


print("Se define el esquema que nos devolvera la UDF, con las predicciones hechas")
result_schema =StructType([
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


@pandas_udf( result_schema, PandasUDFType.GROUPED_MAP )
def forecast_store_item( history_pd ):
  
  # TRAIN MODEL AS BEFORE
  # --------------------------------------
  # remove missing values (more likely at day-store-item level)
  history_pd = history_pd.dropna()
  
  # configure the model
  model = Prophet(
    interval_width=0.95,
    growth='linear',
    daily_seasonality=False,
    weekly_seasonality=True,
    yearly_seasonality=True,
    seasonality_mode='multiplicative'
    )
  
  # train the model
  model.fit( history_pd )
  # --------------------------------------
  
  # BUILD FORECAST AS BEFORE
  # --------------------------------------
  # make predictions
  future_pd = model.make_future_dataframe(
    periods=90, 
    freq='d', 
    include_history=True
    )
  forecast_pd = model.predict( future_pd )  

  print("hdfs://hdfs:9000/modelo_entrenado_{0}_{1}.pickle".format(history_pd['store'].iloc[0],history_pd['item'].iloc[0]))


  #with open("/usr/local/spark/resources/modelos/modelo_entrenado_{0}_{1}.pickle".format(history_pd['store'].iloc[0],history_pd['item'].iloc[0]), "wb") as f:
  #   pickle.dump(model, f)


  # --------------------------------------
  
  # ASSEMBLE EXPECTED RESULT SET
  # --------------------------------------
  # get relevant fields from forecast
  f_pd = forecast_pd[ ['ds','yhat', 'yhat_upper', 'yhat_lower'] ].set_index('ds')
  
  # get relevant fields from history
  h_pd = history_pd[['ds','store','item','y']].set_index('ds')
  
  # join history and forecast
  results_pd = f_pd.join( h_pd, how='left' )
  results_pd.reset_index(level=0, inplace=True)
  
  # get store & item from incoming data set
  results_pd['store'] = history_pd['store'].iloc[0]
  results_pd['item'] = history_pd['item'].iloc[0]
  # --------------------------------------

  results_pd['interval_width'] = 0.95
  results_pd['growth'] = 'linear'
  results_pd['daily_seasonality'] = False
  results_pd['weekly_seasonality'] = True
  results_pd['yearly_seasonality'] = True
  results_pd['seasonality_mode'] = 'multiplicative'

  # return expected dataset
  return results_pd[ ['ds', 'store', 'item', 'y', 'yhat', 'yhat_upper', 'yhat_lower', 'interval_width','growth',
    'daily_seasonality','weekly_seasonality','yearly_seasonality','seasonality_mode'] ]  


print("Se ejecuta la UDF por cada combinacion articulo-tienda")
results = (
  store_item_history
    .groupBy('store', 'item')
    .apply(forecast_store_item)
    .withColumn('training_date', current_date() )
    )

print("El resultado de las predicciones se almacenan en una vista temporal")
results.createOrReplaceTempView('new_forecasts')
results.show()
print("SE GUARDA EN HDFS EL NEW_FORECAST")

df = spark.sql("SELECT * FROM new_forecasts")
df.show()
df.coalesce(1).write.mode("overwrite").format("parquet").save("hdfs://hdfs:9000/new_forecasts")


