import sys
from pyspark import SparkConf, SparkContext

# Create spark context
sc = SparkContext()

print("Hello World!")


# Get the second argument passed to spark-submit (the first is the python app)
logFile = "/usr/local/spark/resources/1.log"

# Read file
logData = sc.textFile(logFile).cache()

# Get lines with A
numAs = logData.filter(lambda s: 'a' in s).count()

# Get lines with B 
numBs = logData.filter(lambda s: 'b' in s).count()

# Print result
print("Lines with a: {}, lines with b: {}".format(numAs, numBs))