from pyspark.sql.types import *
from pyspark.sql import SparkSession

appName = "Python Example - PySpark Read CSV"
master = 'local'

# Create Spark session
spark = SparkSession.builder \
    .master(master) \
    .appName(appName) \
    .getOrCreate()

# Convert list to data frame
df = spark.read.format('csv') \
                .option('header',True) \
                .load('hdfs://hdfs:9000/sample_submission.csv')
df.show()

# structure of the training data set
#train_schema = StructType([
#  StructField('date', DateType()),
#  StructField('store', IntegerType()),
#  StructField('item', IntegerType()),
#  StructField('sales', IntegerType())
#  ])

# read the training file into a dataframe
#train = spark.read.csv(
#  '/FileStore/tables/demand_forecast/train/train.csv', 
#  header=True, 
#  schema=train_schema
#  )

# make the dataframe queriable as a temporary view
#train.createOrReplaceTempView('train')