import sqlite3
import os
import sys
import time
import string
from collections import Counter
from nltk.tag import pos_tag

############### Copied from addSingleFeature.py #############################
#Modified for length; to use caching; to add multiple features in 1 update

def make_sure_feature_in_db(cursor, feature_name):
    cursor.execute("SELECT * FROM Features LIMIT 1")
    list_of_features = {description[0] for description in cursor.description}
    if(feature_name not in list_of_features):
        cursor.execute("ALTER TABLE Features ADD COLUMN %s REAL" % feature_name)



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


#Converts a string (comment or article) into a list of all words, minus punctuation
def word_vec(text):
    return [word.strip(string.punctuation).lower() for word in text.replace("<br/>", " ").split()]

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

def KL_divergence_POS(c_text, a_text, a_url, metadict):

    comment_tagged = pos_tag(c_text)
    article_tagged = []
    if a_url in metadict:
        article_tagged = metadict[a_url]
    else:
        article_tagged = pos_tag(a_text)
        metadict[a_url] = article_tagged


def main():
    database = sqlite3.connect(sys.argv[1])

    add_multiple_similarity_metrics(database)

    database.close()

verbose = True 
cutoffNum = float("inf")
if __name__ == "__main__":
    main()


