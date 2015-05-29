import sqlite3
import os
import sys
import time
import string
from collections import Counter

def make_sure_feature_in_db(cursor, feature_name):
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
    comments_data = [(c_id, c_text) for (c_id, c_text) in cursor.execute("SELECT CommentID, CommentText FROM Comments")]
    counter = 0
    start = time.time()

    #Maybe I should store all article text in a dictionary, comment_id --> text
    id_to_url, url_to_article = get_article_text_dictionary(cursor)
    #Could be faster than all the DB joins..
    for comment_id, comment_text in comments_data:    
        #article_text = get_article_text_from_comment(cursor, comment_id)
        article_text = url_to_article[str(id_to_url[comment_id])]
        similarity = feature_fct(word_vec(comment_text), word_vec(article_text))
        #print similarity
        #print jaccard_sim(word_vec(comment_text), word_vec(article_text))
        #raw_input("")
        insert_statement = ("UPDATE Features SET %s= %f WHERE CommentID = %d" % (feature_name, similarity, comment_id))
        cursor.execute(insert_statement)
        
        if counter % 1000 == 0 :
            print counter, " took ", time.time() - start
            database.commit()
        counter += 1

    cursor.close() 
    database.commit()   


#What I really want is two dictionaries
#comment_id --> url
#url --> article_text
def get_article_text_dictionary(cursor):
    id_to_url = {}
    url_to_article = {}

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
    stmt = "SELECT FullText From ArticleText AS A JOIN Comments AS C ON A.URL=C.ArticleURL WHERE C.CommentID = "
    stmt += str(comment_id)
    text = [text for text in cursor.execute(stmt)][0][0]
    text = text.replace(u"\xc3", "")
    return text


#remove stop words?
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


def euclidean_sim(x, y):
    pass


def main():
    database = sqlite3.connect(sys.argv[1])
    #add_feature_to_database(database, "IAmA", ["I'm a", "I am a", "I am an", "I'm an"])
    #add_feature_to_database(database, "Europe")

    add_similarity_metric(database, "Cosine", cosine_sim)
    #add_similarity_metric(database, "Jaccard", jaccard_sim)
    #add_similarity_metric(database, "Euclidean", euclidean_sim)

    database.close()


if __name__ == "__main__":
    main()