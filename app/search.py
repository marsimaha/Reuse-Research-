import pandas as pd
import numpy as np
import nltk
from nltk.corpus import wordnet
nltk.download("wordnet")
import ast
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi

import streamlit as st
from sentence_transformers import SentenceTransformer


from neo4j import GraphDatabase
import search as sh
import json
from nltk.stem import WordNetLemmatizer


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




def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_query_matches_embed(model, search_query, list_embeddings):
    # Encode the search query
    query_embedding = model.encode(search_query, convert_to_numpy=True)

    # Calculate cosine similarities
    cos_similarities = np.array([cosine_similarity(query_embedding, emb) for emb in list_embeddings])

    # Get top matches
    top_matches_indices = np.argsort(-cos_similarities)[:5]  # Assuming you want top 5 matches
    top_cos_similarities = cos_similarities[top_matches_indices]

    return top_matches_indices, top_cos_similarities


def lemmatize_text(text):
    lemmatizer = WordNetLemmatizer()

    lemmatized_words = [lemmatizer.lemmatize(word) for word in text.split()]
    return ' '.join(lemmatized_words)


def outputs(model, list, list_code, search_query, list_embeddings):
    results, cos = get_query_matches_embed(model, search_query, list_embeddings)
    cos = np.sort(cos)[[-1, -2, -3, -4, -5]]            
    similar_texts = list[results] 
    similar_codes = list_code[results]
    df_similar_texts = pd.DataFrame({
        'Name': similar_texts,
        'Relevance': cos[0:len(similar_texts)],
        "Code": similar_codes
    }) 
    df_similar_texts = df_similar_texts.drop_duplicates(subset='Code', keep='first')
    df_similar_texts = df_similar_texts.loc[df_similar_texts['Relevance'] != 0]
    df_similar_texts.reset_index()

    return df_similar_texts

def search():
    st.title("My Streamlit App")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    if 'checkbox_state' not in st.session_state:
        st.session_state.checkbox_state = [False, False, False, False]
    
    search_query = st.text_input("Enter your search query:")

    def checkbox_callback(index):
        st.session_state.checkbox_state = [False, False, False, False]
        st.session_state.checkbox_state[index] = not st.session_state.checkbox_state[index]

    checkbox1 = st.checkbox('eBKP', value=st.session_state.checkbox_state[0], on_change=checkbox_callback, args=(0,))
    checkbox2 = st.checkbox('IFC', value=st.session_state.checkbox_state[1], on_change=checkbox_callback, args=(1,))
    checkbox3 = st.checkbox('MF', value=st.session_state.checkbox_state[2], on_change=checkbox_callback, args=(2,))
    checkbox4 = st.checkbox('UNICLASS', value=st.session_state.checkbox_state[3], on_change=checkbox_callback, args=(3,))


    if search_query:
        pass

    IFC = pd.read_csv("IFC_processed.csv") 
    IFC.IFC = IFC.IFC.apply(lemmatize_text)
    IFC_embeddings = np.load('embeddings_ifc.npy')

    eBKP = pd.read_csv("eBKP_processed1.csv") 
    eBKP['Element designation_EN'] = eBKP['Element designation_EN'].apply(lemmatize_text)
    eBKP_embeddings = np.load('embeddings_ebkp.npy')

    MF = pd.read_csv("MF_processed.csv") 
    MF['label'] = MF['label'].apply(lemmatize_text)
    MF_embeddings = np.load('embeddings_mf.npy')


    UNI = pd.read_excel("Uniclass2015_Pr.xlsx", header=2) 
    UNI['Title'] = UNI['Title'].apply(lemmatize_text)
    UNI_embeddings = np.load('embeddings_uni.npy')


    # You can use buttons to trigger actions
    if st.button("Search"):
        # Perform action on click (similar to form submission in Flask)
        if checkbox1:
            st.write("eBKP")
            df_similar_texts = outputs(model, eBKP['Element designation_EN'], eBKP['Code'], search_query, eBKP_embeddings)
            eBKPCode = eBKP[eBKP["Code"].isin(df_similar_texts["Code"])]

            df_similar_texts['Type'] = eBKPCode["IfcBuiltSystem.ObjectType"]
            st.table(df_similar_texts)

        if checkbox2:
            st.write("IFC")
            df_similar_texts = outputs(model, IFC['IFC'], IFC['raw'], search_query, IFC_embeddings)
            st.table(df_similar_texts)

        if checkbox3:
            st.write("MF")
            df_similar_texts = outputs(model, MF['label'], MF['code'], search_query, MF_embeddings)
            st.table(df_similar_texts)
        
        if checkbox4:
            st.write("UNICLASS")
            df_similar_texts = outputs(model, UNI['Title'], UNI['Code'], search_query, UNI_embeddings)
            st.table(df_similar_texts)


        if not checkbox3 and not checkbox2 and not checkbox1 and not checkbox4:
            st.write("eBKP")
            df_similar_texts = outputs(model, eBKP['Element designation_EN'], eBKP['Code'], search_query, eBKP_embeddings) 
            eBKPCode = eBKP[eBKP["Code"].isin(df_similar_texts["Code"])]

            df_similar_texts['Type'] = eBKPCode["IfcBuiltSystem.ObjectType"]
            st.table(df_similar_texts)

            st.write("IFC")
            df_similar_texts = outputs(model, IFC['IFC'], IFC['raw'], search_query, IFC_embeddings)
            st.table(df_similar_texts)

            st.write("MF")
            df_similar_texts = outputs(model,MF['label'], MF['code'], search_query, MF_embeddings)
            st.table(df_similar_texts)

            st.write("UNICLASS")
            df_similar_texts = outputs(model,UNI['Title'], UNI['Code'], search_query, UNI_embeddings)
            st.table(df_similar_texts)

