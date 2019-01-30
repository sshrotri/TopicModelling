from collections import defaultdict
from pyspark.ml.linalg import Vectors, SparseVector
from pyspark.ml.clustering import LDA
from pyspark.sql import SQLContext
import re
import pickle
from nltk.corpus import stopwords
from pyspark import SparkContext
from pyspark.sql.functions import col
sc = SparkContext.getOrCreate()
# check if spark context is defined
print(sc.version)
import time

data = sc.wholeTextFiles("path_to_txt_files/*.txt").map(lambda x: x[1])

fileNames = sc.wholeTextFiles("path_to_txt_files/*.txt").map(lambda x: x[0].split('/')[-1])

allFileNames = fileNames.collect()

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
    
# Get an inverted vocabulary, so that we can look up the word by its ndex value
inverse_vocab = {value: key for(key,value) in vocabulary.items()}

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

dfs = df.randomSplit([0.60, 0.40])
dfTrain = dfs[1]

fileNames = dfTrain.select('doc_id').collect()
indices = [int(i.doc_id) for i in fileNames]

myFileNames = [allFileNames[i] for i in indices]

K = 25
alpha = [50/K for _ in range(K)]
beta = 0.5

lda_model = LDA(optimizer='online', maxIter=15, k=K, docConcentration=alpha, topicConcentration=beta)
df_fit = lda_model.fit(dfTrain)

# Open an output file
num_words = 15
with open('newtopicsGenerated.txt', 'w') as f:
    topic_indices = df_fit.describeTopics(maxTermsPerTopic = num_words)
    termIndyLst = topic_indices.select('termIndices').collect()
    
    # Print topics, showing the top-weighted 10 terms for each topic
    for i in range(topic_indices.count()):
        f.write("\n\n")
        f.write("Topic #{0}\n".format(i + 1))
        wordsHere = termIndyLst[i].termIndices
        
        for j in range(num_words):
            f.write("{0}\n".format(inverse_vocab[wordsHere[j]]))
                
    f.write("{0} topics distributed over {1} documents and {2} unique words\n"  \
        .format(K, documents.count(), len(vocabulary)))
        
transformed = df_fit.transform(dfTrain)
transformed.take(10)

print('Collecting document proportions...')
td = transformed.select('topicDistribution').collect()

print('Building dictionary to save...')
docDict = {}
doc_id = 0
for f in myFileNames:
    docDict[f] = list(td[doc_id].topicDistribution)
    doc_id += 1
    
print('Saving to pickle...')
f = open('newAllDocTopicProps.pckl', 'wb')
pickle.dump(docDict, f)
f.close()
print('Done!')























