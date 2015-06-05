import sqlite3
import os
import sys
import re
import time
import string
from collections import Counter
from nltk.tag import pos_tag
from nltk.stem.porter import *
from textblob import TextBlob
import math

############### Copied from addSingleFeature.py #############################

#Method: make_sure_feature_in_db
#Modified for length; to use caching; to add multiple features in 1 update
def make_sure_feature_in_db(cursor, feature_name):
    cursor.execute("SELECT * FROM Features LIMIT 1")
    list_of_features = {description[0] for description in cursor.description}
    if(feature_name not in list_of_features):
        cursor.execute("ALTER TABLE Features ADD COLUMN %s REAL" % feature_name)


#Method: add_similarity_metric
#Updated method of add_similarity_metric that iterates through DB with a single cursor loop.
#Includes support for using a cutoff number of reviews (defined immediately above main)
def add_similarity_metric(database):
    #loop cursor
    cursor = database.cursor()
    #insertion cursor
    set_cursor = database.cursor()
    make_sure_feature_in_db(cursor, "author_in_text")
    make_sure_feature_in_db(cursor, "first_sentence_jaccard")
    make_sure_feature_in_db(cursor, "first_sentence_cosine")
    make_sure_feature_in_db(cursor, "polarity_dif")
    make_sure_feature_in_db(cursor, "subjectivity_dif")



    #auxillary info
    counter = 0
    metadata = {}

    #Loop through all reviews
    #get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
    #for c_id, c_text, a_text, a_url in cursor.execute(get_fulltexts_query):

    initial_togo = cursor.execute("SELECT COUNT(*) FROM Features WHERE first_sentence_jaccard IS NULL").fetchone()[0]
    #text_name_query = "SELECT c.CommentText, a.Author FROM Comments c, Articles a WHERE c.ArticleURL = a.URL "
    fulltext_no_repeats_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL, u.Author FROM ArticleText a, Comments c, Features f, Articles u WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND a.URL = u.URL"
    for c_id, c_text, a_text, a_url, a_name in cursor.execute(fulltext_no_repeats_query):
        c_vec = word_vec(c_text)
        a_vec = word_vec(a_text)
        
        #Compute feature:
        num_name = author_name_in_comment(c_vec, a_name)
        s = get_first_sentence_features(c_text, a_text, a_url)

        insert_statement = ("UPDATE Features SET author_in_text = %f, first_sentence_jaccard = %f, first_sentence_cosine = %f, polarity_dif = %f, subjectivity_dif = %f WHERE CommentID = %d" % (num_name, s[0], s[1], s[2], s[3], c_id))
        set_cursor.execute(insert_statement)

        counter += 1
        if counter % 100 == 0:
            sys.stdout.write("*")
            sys.stdout.flush()
            if counter % 1000 == 0:
                database.commit()
                print "\n Have added %d/%d scores" % (counter, initial_togo)
        if counter > cutoffNum: break

    set_cursor.close()
    cursor.close()
    database.commit()


############ Convenience functions for calculation: ####################

#Method: word_vec
#Converts a string (comment or article) into a list of all words, minus punctuation
def word_vec(text):
    return [word.strip(string.punctuation).lower() for word in text.replace("<br/>", " ").split()]

#Method: jaccard_sim
#Computes the Jaccard similarity between two vectors x and y
def jaccard_sim(x, y):
    union = float(len(set(x).union(set(y))))
    intersection = len(set(x).intersection(set(y)))
    return intersection/union

#Method: cosine_sim
def cosine_sim(x, y):
    dot_product = 0
    x_dict = Counter(x)
    y_dict = Counter(y)
    for key, value in x_dict.items():
        dot_product += value * y_dict.get(key, 0)

    return dot_product / float(len(x_dict) * len(y_dict) + 1)

########### Feature functions: ########################################

#Method: jaccard_similarity_skipgrams
#Adds "skipgrams"-- like a bigram, but with up to k words separating them--
#to the database, under the jaccard similarity metric.
def jaccard_similarity_skipgrams(c_text, a_text, a_url, kVal, metadict):
    k = kVal # Number of spaces to skip
    c_dict = {}
    a_dict = {}

    #Get skipgrams from comment text:
    for i in range(len(c_text)):
        for j in range(i+1, min(len(c_text), i + k + 2)):
            skipgram = (c_text[i], c_text[j])
            c_dict[skipgram] = 1
    #Get skipgrams from article text:
    if a_url in metadict:
        a_dict = metadict[a_url]
    else:
        for i in range(len(a_text)):
            for j in range(i+1, min(len(a_text), i + k + 2)):
                skipgram = (a_text[i], a_text[j])
                a_dict[skipgram] = 1
        metadict[a_url] = a_dict

    #Compute Jaccard similarity of this skipgram:
    union = float(len(set(c_dict.keys()).union(set(a_dict.keys()))))
    intersect = len(set(c_dict.keys()).intersection(set(a_dict.keys())))
    if union == 0:
        return 0
    dist = intersect / union
    return dist 

#Method: stem_jaccard_sim
#Stem the words using NLTK's PorterStemmer, then calculate the jaccard distance
#between a comment and its article text.
def stem_jaccard_sim(x, y, a_url, metaD):
    stemmy = PorterStemmer()
    stemmed_x = [stemmy.stem(word) for word in x]
    stemmed_y = []
    if a_url in metaD:
        stemmed_y = metaD[a_url]
    else:
        stemmed_y = [stemmy.stem(word) for word in y]
        metaD[a_url] = stemmed_y

    return jaccard_sim(stemmed_x, stemmed_y)

#Method: author_name_in_comment
#Returns the number of occurrences of the authors (first or last) name in the comment
#text.
def author_name_in_comment(c_vec, a_name):
    if len(a_name) < 1: return 0
    a_name = a_name.lower()
    occurrs = Counter(c_vec)
    return occurrs[a_name.split()[0]] + occurrs[a_name.split()[-1]]

def grab_first_sentence(text):
    return re.split(u'[.?!]', text)[0]

#Method: get_first_sentence_features
def get_first_sentence_features(c_text, a_text, a_url):
    first_sentence = grab_first_sentence(c_text)
    first_sentence_vec = word_vec(first_sentence)
    article = word_vec(a_text)
    
    first_sentence_jaccard = jaccard_sim(first_sentence_vec, article)
    first_sentence_cosine = cosine_sim(first_sentence_vec, article)

    #Note: sentiment analysis on first sentence was fairly useless; comparing
    #with the whole comment text instead
    comment_blob = TextBlob(c_text)
    article_blob = None
    if a_url in blob_cache:
        article_blob = blob_cache[a_url]
    else:
        article_blob = TextBlob(a_text)
        blob_cache[a_url] = article_blob

    polarity_dif = abs(comment_blob.sentiment.polarity - article_blob.sentiment.polarity)
    subjectivity_dif = abs(comment_blob.sentiment.subjectivity - article_blob.sentiment.subjectivity)
    
    return first_sentence_jaccard, first_sentence_cosine, polarity_dif, subjectivity_dif



######### Main: ####################################################

def main():
    database = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/jun5.db")

    add_similarity_metric(database)

    database.commit()
    database.close()

verbose = True 
blob_cache = {}
cutoffNum = float("inf")
if __name__ == "__main__":
    main()


