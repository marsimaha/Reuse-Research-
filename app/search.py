import pandas as pd
import numpy as np
import nltk
from nltk.corpus import wordnet
nltk.download("wordnet")
import ast
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi

def tokenize(text):
    return word_tokenize(text.lower())  # Tokenize and lowercase the text

class BM25Plus(BM25Okapi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delta = kwargs.get('delta', 1.0)  # BM25+ has an extra delta parameter

    def _score(self, doc_freq, total_docs, doc_len, avg_doc_len, freq, rel_freq, k1, b):
        # This is a conceptual method; actual implementation may differ
        idf = self._idf(doc_freq, total_docs)
        tf = self._tf(freq, doc_len, avg_doc_len, k1, b)
        tf_plus = tf + self.delta  # Modification for BM25+
        return idf * tf_plus

# Fetch synonyms for a word
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

# Enrich a text string with synonyms
def enrich_with_synonyms(text):
    words = text.split()
    enriched_text = []
    for word in words:
        enriched_text.append(word)
        enriched_text.extend(get_synonyms(word))
    return ' '.join(enriched_text)

def get_query_matches(query, text1):
    # Tokenize the query and each document in text1
    query_tokens = tokenize(query)
    text1_tokens = [tokenize(doc) for doc in text1]
    
    # Initialize BM25 with the tokenized documents
    bm25 = BM25Plus(text1_tokens)
    
    # Get BM25 scores for the query against each document in text1
    doc_scores = bm25.get_scores(query_tokens)
    
    # Get the top 5 indices from text1 most similar to the query
    top_text1_indices = np.argsort(doc_scores)[-5:][::-1]
    
    # Return the indices and their corresponding scores
    return top_text1_indices, doc_scores[top_text1_indices]

def correct_and_eval(input_str):
    corrected_str = input_str.replace(" ", ", ")
    # Handling consecutive commas by replacing them with a single comma
    corrected_str = corrected_str.replace(", ,", ",")
    corrected_str = corrected_str.replace("[,","[") 
    corrected_str = corrected_str.replace(",]", "]") 

    # If the corrected string starts or ends with a comma, remove it
    corrected_str = corrected_str.strip(",")
    return ast.literal_eval(corrected_str)


def get_eBKP(adapter, results):
    eBKP = pd.read_csv("eBKP_processed1.csv")
    adapBKP = adapter["eBPK indexes"]
    if len(results) == 0:
        return [["", ""]]
    elif len(results) == 1:
        most_similar_text3 = eBKP["code"][correct_and_eval(adapBKP[results[0]])[0]]
        most_similar_text31 = eBKP["Translated_Text"][correct_and_eval(adapBKP[results[0]])[0]]
        return [(most_similar_text3, most_similar_text31)]
    else:
        most_similar_text3 = eBKP["code"][correct_and_eval(adapBKP[results[0]])[0]]
        most_similar_text31 = eBKP["Translated_Text"][correct_and_eval(adapBKP[results[0]])[0]]
        most_similar_text32 = eBKP["code"][correct_and_eval(adapBKP[results[1]])[1]]
        most_similar_text321 = eBKP["Translated_Text"][correct_and_eval(adapBKP[results[1]])[1]]
        most_similar_text33 = eBKP["code"][correct_and_eval(adapBKP[results[2]])[2]]
        most_similar_text332 = eBKP["Translated_Text"][correct_and_eval(adapBKP[results[2]])[2]]
        return [(most_similar_text3, most_similar_text31), (most_similar_text32, most_similar_text321), (most_similar_text33, most_similar_text332)]

def get_MF(adapter, results):
    MF = pd.read_csv("MF_processed.csv")
    adapMF = adapter["Master Format indexes"]
    if len(results) == 0:
        return [["", ""]]
    elif len(results) == 1:
        most_similar_text2 = MF["code"][correct_and_eval(adapMF[results[0]])[0]]
        most_similar_text22 = MF["label"][correct_and_eval(adapMF[results[0]])[0]]
        return [[most_similar_text2, most_similar_text22]]
    else:
        most_similar_text2 = MF["code"][correct_and_eval(adapMF[results[0]])[0]]
        most_similar_text22 = MF["label"][correct_and_eval(adapMF[results[0]])[0]]
        most_similar_text21 = MF["code"][correct_and_eval(adapMF[results[1]])[1]]
        most_similar_text212 = MF["label"][correct_and_eval(adapMF[results[1]])[1]]
        most_similar_text23 = MF["code"][correct_and_eval(adapMF[results[2]])[2]]
        most_similar_text232 = MF["label"][correct_and_eval(adapMF[results[2]])[2]]

        return [[most_similar_text2, most_similar_text22], [most_similar_text21, most_similar_text212], [most_similar_text23, most_similar_text232]]

