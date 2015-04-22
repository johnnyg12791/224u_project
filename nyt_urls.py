#nyt_urls.py
import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import pprint
import numpy as np
import math
from bs4 import BeautifulSoup #also: pip install beautifulsoup4
import pickle
import sqlite3

#This returns a list of urls to different NYT articles
#We will keep track of the URL, Author, Section, Date


def main():
    #Use api to get json objects
    #Most popular api keys: (eventually, cycle through each API key for each call)
    API_KEYS = ["e548999ea9b04cf78d32d9359d1f03a5:15:15145567"]
    #this number 30 can be changed to 1 in order to 
    URL = "http://api.nytimes.com/svc/mostpopular/v2/mostemailed/all-sections/1?api-key=e548999ea9b04cf78d32d9359d1f03a5:15:15145567"
    response = requests.get(URL)    

    #Create Article objects from that
    data = json.loads(response.text)
    articles_processed = 0
    new_articles_added = 0
    for item in data[u'results']:
        new_articles_added += process_article(Article(item))
        articles_processed += 1

    num_results = data[u'num_results']
    #Cycle through all pages, getting the 
    num_pages = int(math.ceil(num_results/20.0))
    for i in range(num_pages):
        offset = str(20*(i+1))
        response = requests.get(URL + "&offset=" + offset)
        data = json.loads(response.text)
        for item in data[u'results']:
            new_articles_added +=  process_article(Article(item))
            articles_processed += 1
        print "Processed %d articles out of %d" % (articles_processed, num_results)
        print "%d New Articles Added" % (new_articles_added)

#Function: process_article
#This function first checks to see if the article is in the
#database. Iff the article is not in the database, it adds the
#article into the database, marking its comments as yet-to-be scraped
def process_article(article):
    #Avoid adding repeated articles to DB:
    if not database_contains_article(article.url):
        put_article_database(article)
        return 1
    return 0


# Function: database_contains_article
# Boolean-returning function that returns true iff the database contains
# the specified article URL (in "Articles" table)
def database_contains_article(url):
    command = "SELECT * FROM Articles WHERE URL = (?)"
    db_cursor.execute(command, (url,))
    if db_cursor.fetchone() == None:
        return False
    return True 

#Function: put_article_database
#Adds the selected article to the Articles table in the database
def put_article_database(article):
    command = "INSERT into Articles (URL, Author, Title, Section, CommentsAdded) VALUES (?, ?, ?, ?, ?)"
    db_cursor.execute(command, (article.url, article.author, article.title, article.section, False))

#Class: Article
#Provides wrapper for fields present in articles returned by NYtimes "popular" api
class Article:
    author = ""
    url = ""
    section = ""
    date = ""
    title = ""

    def __init__(self, data):
        #Takes the json data for a given article
        #Sets the author, url, section, and date fields    
        self.author = data[u'byline'][3:]#Remove the "By " from byline
        self.url = data[u'url']
        self.section = data[u'section']
        self.date = data[u'published_date']
        self.title = data[u'title']


    def displayArticle(self):
        print self.title, " by ", self.author
        print "Appeared on ", self.date, "in the ", self.section, " section"
        print "URL = ", self.url

#This prints a list of all NYT sections, if you ever want that
def print_all_sections():
    response = requests.get("http://api.nytimes.com/svc/mostpopular/v2/mostemailed/sections-list?api-key=e548999ea9b04cf78d32d9359d1f03a5:15:15145567")
    data = json.loads(response.text)
    for result in data[u'results']:
        print str(result[u'name'])


#Open database and access cursor:
comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
db_cursor = comments_db.cursor()

if __name__ == "__main__":
    #Run main method:
    main()

#Close database and cursor:
comments_db.commit()
db_cursor.close()
comments_db.close()





