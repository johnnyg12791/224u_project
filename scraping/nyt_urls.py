#nyt_urls.py
import sys
import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import pprint
import numpy as np
import math
import datetime
from bs4 import BeautifulSoup #also: pip install beautifulsoup4
import pickle
import sqlite3

#This returns a list of urls to different NYT articles
#We will keep track of the URL, Author, Section, Date
db = 0
def main():
    db = int(sys.argv[1]) #1 if you want to use the DB, 0 for testing purposes

    if(db):
        #Open database and access cursor:
        comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
        db_cursor = comments_db.cursor()
    
    #If you just pass in the DB flag, runs most viewed article script
    if(len(sys.argv) == 2):
        add_most_viewed_articles()
    
    #You can also pass in a search term, to run the article search script
    else:
        term = sys.argv[2]
        add_articles_by_term(term)


    if(db):
        #Close database and cursor:
        comments_db.commit()
        db_cursor.close()
        comments_db.close()


#This takes a search term (ie, "obama", "economics", "sports")
#And uses a very similar process as add_most_viewed articles to adding to database
def add_articles_by_term(term):
    begin = "http://api.nytimes.com/svc/search/v2/articlesearch.json?q=" + term + "&fq=source:(\"The%20New%20York%20Times\")&begin_date="
    end = "&sort=oldest&api-key=eb94970b5aef4d0e8664c8c8c26da4fe:4:15145567"

    new_articles_added = 0
    #Can change this start date
    search_date = datetime.date(2013, 1, 1)
    all_urls = []
    while(search_date < datetime.date.today()):#Go until april 1st
        for page in range(3): #Assume at most 3 pages (30 articles) a day for a given search term..?
            #This is to reformat 2013-01-01 as 20130101
            date = str(search_date)[:4] + str(search_date)[5:7] + str(search_date)[8:10]
            #Then we put together the query and get the json data
            query = begin + date + "&page=" + str(page) + end
            response = requests.get(query)
            data = json.loads(response.text)
            #go through the data, setting up our article information
            for item in data[u'response'][u'docs']:
                if(db):
                    new_articles_added += process_article(Article(item, most_viewed=False))
                else:
                    #Article(item, most_viewed=False).displayArticle()
                    url = item[u'web_url']
                    if(url not in all_urls):
                        all_urls.append(url)
            page += 1
        search_date += datetime.timedelta(days=1)
        print "You are at day ", search_date
        if(db):
            print "%d new articles added to database" % (new_articles_added)
        else:
            print "You've found %d new urls" % (len(all_urls))


#This was the foundation of what we had earlier
#Gets a list of urls (not including offsets) to start from
#Then cycles through all pages of that response
#Adding each article, first by processing to an object, the into sqlite
#Basic tracking progress is included as well
def add_most_viewed_articles():
    articles_per_page = 20
    urls = create_different_urls()
    for url in urls:
        print url
        data = json.loads((requests.get(url)).text)
        new_articles_added = 0
        num_pages = int(math.ceil(data[u'num_results']/float(articles_per_page)))
        for page in range(num_pages):
            offset = str(articles_per_page*(page))
            response = requests.get(url + "&offset=" + offset)
            data = json.loads(response.text)
            for item in data[u'results']:
                if(db):
                    new_articles_added += process_article(Article(item))
                else:
                    Article(item).displayArticle()
            print "Processed %d articles out of %d" % (page*articles_per_page, num_pages*articles_per_page)
            print "%d New Articles Added To Database" % (new_articles_added)



#This creates all the different sharetype-date-section combinations for the base URL
#Can rotate here between 3 different API KEYS
def create_different_urls():
    to_start_urls = []
    beg = "http://api.nytimes.com/svc/mostpopular/v2/"
    middle = "/all-sections/"
    end = "?api-key=e548999ea9b04cf78d32d9359d1f03a5:15:15145567"

    share_types = ["mostemailed", "mostviewed", "mostpopular"]
    time_periods = [1, 7, 30]
    for most_what in share_types:
        for num_days in time_periods:
            url = beg + most_what + middle + str(num_days) + end
            to_start_urls.append(url)
    #print to_start_urls
    return to_start_urls


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

    def __init__(self, data, most_viewed=True):
        #Takes the json data for a given article
        #Sets the author, url, section, and date fields    
        if(most_viewed):
            self.author = data[u'byline'][3:]#Remove the "By " from byline
            self.url = data[u'url']
            self.section = data[u'section']
            self.date = data[u'published_date']
            self.title = data[u'title']
        else: #We are getting this from the article search API
            print data
            if(data[u'byline'] != [] and data[u'byline'] != None):
                self.author = data[u'byline'][u'original'][3:]
            self.url = data[u'web_url']
            self.section = data[u'section_name']
            self.date = data[u'pub_date']
            self.title = data[u'headline'][u'main']#[u'print_headline']
            #raw_input("")

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




if __name__ == "__main__":
    #Run main method:
    main()





