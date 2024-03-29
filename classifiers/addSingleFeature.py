import sqlite3
import os
import sys
import time
import string
from collections import Counter
from nltk.stem.porter import *


def make_sure_feature_in_db(cursor, feature_nam=e):
    cursor.execute("SELECT * FROM Features LIMIT 1")
    list_of_features = {description[0] for description in cursor.description}
    if(feature_name not in list_of_features):
        cursor.execute("ALTER TABLE Features ADD COLUMN %s REAL" % feature_name)



def add_feature_to_database(database, feature_name, search_terms=[]):
    cursor = database.cursor()
    make_sure_feature_in_db(cursor, feature_name)

    if search_terms == [] :
        search_terms = [feature_name.lower()]

    #Then cycle through all comments
    comments_data = [(c_id, c_text) for (c_id, c_text) in cursor.execute("SELECT CommentID, CommentText FROM Comments")]
    counter = 0
    start = time.time()
    for comment_id, comment_text in comments_data:    
        feature_value = 1.0 if any(term.lower() in comment_text.lower() for term in search_terms) else 0.0
        #Insert into SQLite
        insert_statement = ("UPDATE Features SET %s= %f WHERE CommentID = %d" % (feature_name, feature_value, comment_id))
        cursor.execute(insert_statement)
        #Timing and Commiting
        if(counter % 1000 == 0):
            print counter, " took ", time.time() - start
            database.commit()
        counter += 1
    cursor.close() 
    database.commit()   


def add_similarity_metric(database, feature_name, feature_fct):
    cursor = database.cursor()
    make_sure_feature_in_db(cursor, feature_name)

    #Then cycle through all comments
    comments_data = []
    for c_id, c_text in cursor.execute("SELECT CommentID, CommentText FROM Comments"):
        comments_data.append((c_id, c_text))
        if len(comments_data) > cutoffNum:
            break ##TODO: remove @ debug
    #comments_data = [(c_id, c_text) for (c_id, c_text) in cursor.execute("SELECT CommentID, CommentText FROM Comments")]
    counter = 0
    start = time.time()
    #Two dictionaries to facilitate getting article text for given comment id
    id_to_url, url_to_article = get_article_text_dictionary(cursor)

    for comment_id, comment_text in comments_data:    
        #article_text = get_article_text_from_comment(cursor, comment_id)
        article_text = url_to_article[str(id_to_url[comment_id])]
        similarity = feature_fct(word_vec(comment_text), word_vec(article_text))

        insert_statement = ("UPDATE Features SET %s = %f WHERE CommentID = %d" % (feature_name, similarity, comment_id))
        cursor.execute(insert_statement)

        if counter % 1000 == 0 :
            print counter, " took ", time.time() - start
            database.commit()
        counter += 1

    cursor.close() 
    database.commit()   

#Method: add_multiple_similarity_metrics
#Alternate method to add_similarity_metric that iterates through DB with a single cursor loop.
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

    get_fulltexts_query = "SELECT CommentID, CommentText, FullText FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
    comments_data = [(c_id, c_text, a_text) for (c_id, c_text, a_text) in cursor.execute(get_fulltexts_query)]

    for c_id, c_text, a_text in comments_data:
        feature_value = feature_fct(word_vec(c_text), word_vec(a_text))

        insert_statement = ("UPDATE Features SET %s = %f WHERE CommentID = %d" % (feature_name, feature_value, c_id))
        cursor.execute(insert_statement)

    skipgram2_metadata = {}
    skipgram3_metadata = {}

    #Loop through all reviews
    get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
    for c_id, c_text, a_text, a_url in cursor.execute(get_fulltexts_query):
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

#What I really want is two dictionaries
#comment_id --> url
#url --> article_text
def get_article_text_dictionary(cursor):
    id_to_url = {}
    url_to_article = {}
    comment_id_url = []
    comment_id_url = [(c_id, url) for (c_id, url) in cursor.execute("SELECT CommentID, ArticleURL FROM Comments")]
    for c_id, url in comment_id_url:
        id_to_url[c_id] = url

    article_text_url = [(text, url) for (text, url) in cursor.execute("SELECT FullText, URL FROM ArticleText")]
    for text, url in article_text_url:
        url_to_article[url] = text

    return (id_to_url, url_to_article)

#Converts a string (comment or article) into a list of all words, minus punctuation
def word_vec(text):
    return [word.strip(string.punctuation).lower() for word in text.replace("<br/>", " ").split()]


#Given a CommentID and Database cusor, 
#uses a sql query to get the article text from Article/ArticleText tables
def get_article_text_from_comment(cursor, comment_id):
    stmt = "SELECT FullText From ArticleText AS A JOIN Comments AS C ON A.URL=C.ArticleURL WHERE C.CommentID = " + str(comment_id)
    return [text for text in cursor.execute(stmt)][0][0]

#Method: cosine_sim
def cosine_sim(x, y):
    dot_product = 0
    x_dict = Counter(x)
    y_dict = Counter(y)
    for key, value in x_dict.items():
        dot_product += value * y_dict.get(key, 0)
    #How ever many are in common
    if(len(x_dict) == 0):
        print "comment: ", x #Somehwere in 56,000 we have an empty comment...

    return dot_product / float(len(x_dict) * len(y_dict) + 1)

#Jaccard = Intersection / Union 
#Add weighting scheme??
def jaccard_sim(x, y):
    union = float(len(set(x).union(set(y))))
    intersection = len(set(x).intersection(set(y)))
    return intersection/union

#Method: stem_jaccard_sim
#Stem the words using NLTK's PorterStemmer, then calculate the jaccard distance
#between a comment and its article text.
def stem_jaccard_sim(x, y):
    stemmy = PorterStemmer()
    stemmed_x = [stemmy.stem(word) for word in x]
    stemmed_y = [stemmy.stem(word) for word in y]
    print x
    print stemmed_x
    return jaccard_sim(stemmed_x, stemmed_y)


def n_char_word_range(c_text, a_text):
    low = 16
    high = 20
    n_words_in_range = 0
    for word in c_text:
        if(len(word) >= low and len(word) <= high):
            n_words_in_range += 1
    
    #print n_words_in_range
    return n_words_in_range


#This compares the size of the comment to the size of the article (roughly: word count)
def size_compared_to_article(c_text, a_text):
    return float(len(c_text)+1)/float(len(a_text)+1)



#Method: jaccard_similarity_skipgrams
#Adds "skipgrams"-- like a bigram, but with up to k words separating them--
#to the database, under the jaccard similarity metric.
#The "metadict" is a cached copy of article text dictionaries (Thanks John!)
#This way you don't have to compute the same skipgrams hundreds of times.
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
    dist = intersect / union
    return dist 


def ends_with_question(a_text, c_text):
    if c_text[-1] == "?" :
        return 1.0
    else :
        return 0.0


def main():
    database = sqlite3.connect(sys.argv[1])
    #add_feature_to_database(database, "IAmA", ["I'm a", "I am a", "I am an", "I'm an"])
    #add_feature_to_database(database, "Europe")

    #updated_add_similarity_metric(database, "size_compared_to_article", n_char_word_range)

    #updated_add_similarity_metric(database, "skipgrams_2", jaccard_similarity_skipgrams)
    #add_multiple_similarity_metrics(database)

    add_similarity_metric(database, "stem_jaccard", stem_jaccard_sim)
    #add_similarity_metric(database, "Cosine", cosine_sim)
    #add_similarity_metric(database, "Jaccard", jaccard_sim)
    #add_similarity_metric(database, "Euclidean", euclidean_sim)

    database.close()

verbose = True 
cutoffNum = 10 #float("inf")

if __name__ == "__main__":
    main()


