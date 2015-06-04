import sqlite3
import os
import sys
import time
import string
from collections import Counter
from nltk.tag import pos_tag
from nltk.stem.porter import *

############### Copied from addSingleFeature.py #############################

#Method: make_sure_feature_in_db
#Modified for length; to use caching; to add multiple features in 1 update
def make_sure_feature_in_db(cursor, feature_name):
    cursor.execute("SELECT * FROM Features LIMIT 1")
    list_of_features = {description[0] for description in cursor.description}
    if(feature_name not in list_of_features):
        cursor.execute("ALTER TABLE Features ADD COLUMN %s REAL" % feature_name)


############## Select feature adding model: ###############################

#Method: updated_add_similarity_metric
#Updated method of add_similarity_metric that iterates through DB with a single cursor loop.
#Includes support for using a cutoff number of reviews (defined immediately above main)
def add_multiple_similarity_metrics(database):
    #loop cursor
    cursor = database.cursor()
    #insertion cursor
    set_cursor = database.cursor()
    make_sure_feature_in_db(cursor, "skipgrams_2")
    make_sure_feature_in_db(cursor, "skipgrams_3")

    #auxillary info
    counter = 0
    metadata = {}

    #Loop through all reviews
    #get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
    #for c_id, c_text, a_text, a_url in cursor.execute(get_fulltexts_query):
    fulltext_no_repeats_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.skipgrams_3 IS NULL"
    fulltext_no_repeats_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.skipgrams_3 IS NULL"
    for c_id, c_text, a_text, a_url in cursor.execute(fulltext_no_repeats_query):

        c_vec = word_vec(c_text)
        a_vec = word_vec(a_text)
        
        #Add 2-skipgrams
        skip2_similarity = jaccard_similarity_skipgrams(c_vec, a_vec, a_url, 2, skipgram2_metadata)
        #Add 3-skipgrams
        skip3_similarity = jaccard_similarity_skipgrams(c_vec, a_vec, a_url, 3, skipgram3_metadata)

        insert_statement = ("UPDATE Features SET skipgrams_2 = %f, skipgrams_3 = %f WHERE CommentID = %d" % (skip2_similarity, skip3_similarity, c_id))
        set_cursor.execute(insert_statement)

        counter += 1
        if counter % 1000 == 0:
            database.commit()
            print "Have added %d scores" % counter
        #if counter > cutoffNum: break

    set_cursor.close()
    cursor.close()
    database.commit()


#Method: add_similarity_metric
#Updated method of add_similarity_metric that iterates through DB with a single cursor loop.
#Includes support for using a cutoff number of reviews (defined immediately above main)
def add_similarity_metric(database, feat_name, feat_fxn):
    #loop cursor
    cursor = database.cursor()
    #insertion cursor
    set_cursor = database.cursor()
    make_sure_feature_in_db(cursor, feat_name)

    #auxillary info
    counter = 0
    metadata = {}

    #Loop through all reviews
    #get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
    #for c_id, c_text, a_text, a_url in cursor.execute(get_fulltexts_query):
    count = cursor.execute("SELECT COUNT(*) FROM Features WHERE stem_jaccard IS NULL").fetchone()

    fulltext_no_repeats_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.stem_jaccard IS NULL"
    for c_id, c_text, a_text, a_url in cursor.execute(fulltext_no_repeats_query):

        c_vec = word_vec(c_text)
        a_vec = word_vec(a_text)
        
        #Compute feature:
        feat = feat_fxn(c_vec, a_vec, a_url, metadata)

        insert_statement = ("UPDATE Features SET %s = %f WHERE CommentID = %d" % (feat_name, feat, c_id))
        set_cursor.execute(insert_statement)

        counter += 1
        if counter % 100 == 0:
            print " . "
            if counter % 1000 == 0:
                database.commit()
                print "Have added %d/%d scores" % (counter, count[0])
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


######### Main: ####################################################

def main():
    database = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/jun3.db")

    add_similarity_metric(database, "stem_jaccard", stem_jaccard_sim)

    database.close()

verbose = True 
cutoffNum = float("inf")
if __name__ == "__main__":
    main()


