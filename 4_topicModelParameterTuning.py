from collections import defaultdict
from pyspark.ml.linalg import Vectors, SparseVector
from pyspark.ml.clustering import LDA
from pyspark.sql import SQLContext
import re
from nltk.corpus import stopwords
from pyspark import SparkContext

sc = SparkContext.getOrCreate()
# check if spark context is defined
print(sc.version)
import time


data = sc.wholeTextFiles("path_to_text_file/*.txt").map(lambda x: x[1])

# Tokenize the data
tokens = data.map(lambda document: document.strip().lower()) \
    .map(lambda x: x.split()) \
    .map(lambda word: [x for x in word if x.isalpha()]) \
    .map(lambda word: [x for x in word if len(x) > 2])
    

stop = stopwords.words('english')
# Get vocabulary 
# Flat map to put words into one giant list
# Remove stopwords
# Map and then reduce by key
# Sort by word count
termCounts = tokens.flatMap(lambda document: document) \
    .filter(lambda x: x not in stop) \
    .map(lambda word: (word,1)) \
    .reduceByKey(lambda x,y: x+y) \
    .map(lambda tuple: (tuple[1],tuple[0])) \
    .sortByKey(False)   
    
# Dictionary
vocabulary = termCounts.map(lambda x: x[1]) \
    .zipWithIndex() \
    .collectAsMap()   
    
# Convert a given document into a vector of word counts
def document_vector(document):
    id = document[1]
    counts = defaultdict(int)
    for token in document[0]:
        if token in vocabulary:
            token_id = vocabulary[token]
            counts[token_id] += 1
    counts = sorted(counts.items())
    keys = [x[0] for x in counts]
    values = [x[1] for x in counts]
    return (id, SparseVector(len(vocabulary), keys, values))

# Process all the documents into word vector using above function
documents = tokens.zipWithIndex().map(document_vector).map(list)

df = documents.toDF(['doc_id', 'features'])

# create spark dataframe
#df = spark.createDataFrame(documents, ["doc_id", "features"])
# split into training and testing data
dfs = df.randomSplit([0.85, 0.15])
dfTrain = dfs[0]
dfTest = dfs[1]

# choose different values of topics
Ks = [k for k in range(2, 21)]
# topic prior, determines how sparse or non-sparse the topics are 
betas = [0.05, 0.1, 2., 5.]
# initialize LDA model 
lda_model = LDA(seed=10, optimizer='online', maxIter=2000)
# number of documents
D = dfTrain.count()

output = []

for K in Ks:
    for beta in betas:
        t=time.time()
        # per document proportion prior, based on Griffiths et. al, 2004
        alpha = [50/K for _ in range(K)]
        # set parameters in model accordingly
        lda_model.setParams(k=K, docConcentration=alpha, topicConcentration=beta)
        # fit model
        df_fit = lda_model.fit(dfTrain)
        # get fit perplexity
        df_perp = df_fit.logPerplexity(dfTest)
        
        print('Perplexity={} for K={}, alpha={}, beta={}'.format(df_perp, K, 50/K, beta))
        output.append(['Perplexity={} for K={}, alpha={}, beta={}'.format(df_perp, K, 50/K, beta)])
        print(time.time()-t)
        
 with open('modelTuningResults', 'w') as f:
    for item in output:
        f.write("%s\n" % item)
