#!/bin/python3.6
import nltk
import math
import numpy as np
import sys
from tqdm import tqdm
import pickle
import time
from nltk import word_tokenize
from nltk.util import ngrams
from collections import Counter
import argparse
from joblib import Parallel, delayed
import multiprocessing
num_cores = multiprocessing.cpu_count()

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-n", "--ngrams", help="ngram parameter", type=int)
parser.add_argument("--tokens", help="tokens pickle file address")
args = parser.parse_args()

if args.verbose:
    print("verbosity turned on")

tokens = []

if (args.tokens):
    with open(args.tokens, 'rb') as f:
        tokens = pickle.load(f)
else:
    print('tokens are missing, use the provided tokenizer.')

print('loaded', len(tokens), 'tokens')

print('calculating', args.ngrams, 'grams')
gramed = ngrams(tokens,args.ngrams)

# TODO IMP add starting and ending WORDs ?
# NOTE alan intori tahe jomle ghabli chasbide be badi
gramStats = Counter(gramed)
blockStats = Counter(tokens)
print(gramStats.most_common(50))

# memoize helper
def memoize(f):
    memo = {}
    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]
    return helper

# helper count grams
def countGramsStartingWith(sequence):
    windowSize = len(sequence)
    if windowSize >= args.ngrams : raise Exception('bad sequence length')
    totalCount = 0
    for gram, count in gramStats.items():
        if (list(gram[0:windowSize]) == sequence[0:windowSize]):
            totalCount += count
    return totalCount

# helper looksup ngram count of a seq + last block
def ngramCount(seq, block):
    # create the ngram tuple to lookup it's count
    if (len(seq) == args.ngrams):
        seq[windowSize] = seq
    else:
        seq.append(seq)
    return gramStats[tuple(sequence)]


# TODO add kney and add-1 smoothing
# idea sequence is ngramSize-1
# returns a dictionary of probabilities
def simpleProbabilities(sequence):
    windowSize = args.ngrams-1
    if len(sequence) !=  windowSize: raise Exception('short sequence') #TODO backoff to lower grams? 
    probabilities = {}
    totalCount = countGramsStartingWith(sequence)
    for candidateBlock in list(blockStats):
        probab = round(ngramCount(sequence, candidateBlock)/totalCount, 10)
        probabilities[candidateBlock] = probab
    # or return a sorted list of (block, prob) pairs  
    return probabilities

# calculates the perplexity for a sequence of blocks
def perplexity(blockSequence):
    windowSize = args.ngrams -1
    numWords = len(blockSequence)
    sequenceProbabilityInv = 1;
    # calculate sequence prob inv
    for idx, val in enumerate(blockSequence):
        if idx < windowSize: continue # skip the first n blocks. change if you added starting padding
        probs = simpleProbabilities(blockSequence[idx-windowSize:idx])
        invProb = 1.0/probs[val]
        sequenceProbabilityInv = sequenceProbabilityInv * invProb
    perplexity = (sequenceProbabilityInv)**(1.0/ numWords)
    return perplexity

def evaluate(testSet):
    # tokenize each sentence of test set
    with open(testSet, 'r') as f:
        sentenceTokens = Parallel(n_jobs=num_cores)(delayed(nltk.word_tokenize)(line) for line in tqdm(f.readlines()))
    # calculate perplexity for each sent
    print('calculating perplexities')
    perps = Parallel(n_jobs=num_cores)(delayed(perplexity)(sent) for sent in tqdm(sentenceTokens))
    avg = sum(perps) / float(len(perps))
    print(avg)
    return avg

def interactiveInspection():
    while True:
        # calculate probabilities given a sequence of words
        seq = input('pass a sequence: ')
        seq = seq.split(' ')
        # simpleProbabilities(seq, gramStats)
        perplexity(seq)

evaluate('data/sample.txt')
