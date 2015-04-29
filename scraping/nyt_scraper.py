#nyt_scraper.py

#http://www.pythoncentral.io/introduction-to-sqlite-in-python/
#I like the idea of these sqllite tables to store data
'''
import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import pprint
import numpy as np
import math
from bs4 import BeautifulSoup #also: pip install beautifulsoup4
'''
import time
import sqlite3
import random 
from nyt_urls import *


#For the community API=
#Johns API_KEY=3abe3be579e0b85dac546964182f1dd7:17:15145567
#Marks API KEY=e7c94a47f04362f395038e2126907219:12:71919922
#TODO: modify so cycle through API keys
PRE_URL = "http://api.nytimes.com/svc/community/v3/user-content/url.json?api-key=e7c94a47f04362f395038e2126907219:12:71919922&url="
num_to_scrape = 10000
num_scraped_sofar = 0
#

def main():
    ##Pull unprocessed articles from DB:
    num_articles = db_article_cursor.execute("SELECT COUNT(*) FROM Articles WHERE CommentsAdded = 0").fetchone()[0]
    unprocessedArticlesCommand = "SELECT URL FROM Articles WHERE CommentsAdded = 0"
    all_urls = db_article_cursor.execute(unprocessedArticlesCommand)
    urls_used = []
    for index, url in enumerate(all_urls):
        #print "next article:"
        article_url = url[0] #So that it isn't treated as a tuple
        #Process article:
        if(article_url not in urls_used):
            process_article_comments(article_url)
            #Mark article as processed:
            mark_article_processed(article_url)
            urls_used.append(article_url)
            print "Done processing url %d of %d" % (index, num_to_scrape)
            if index > num_to_scrape: 
                print "Done scraping"
                break


#Function: process_article_comments
#Method to scrape all of the comments from the community API associated
#with the given article URL.
def process_article_comments(article_url):
    #Get a list of all json object comments for this URL:
    comments = get_comments_from_json(article_url)
    #print "Url %s has %d comments" %(article_url, len(comments))
    if len(comments) > 0:
        #If article has comments, add them to DB
        add_comments_to_db(comments, article_url)
        global num_scraped_sofar
        num_scraped_sofar += 1

#Function: mark_article_processsed
#SQL call with the inner (comments) cursor to mark the given articleURL (key)
#as being processed.
def mark_article_processed(article_url):
    db_comments_added.execute("UPDATE Articles SET CommentsAdded=1 WHERE URL = ?", (article_url,))
    comments_db.commit()

#create one giant json thing with all of that articles data?
#The issue is that there is only 25 comments per request, so we need multiple with changes of the offset
#or just get each json and store it immediately in our SQL table
def get_comments_from_json(url):
    response = requests.get(PRE_URL + url)
    try:
        data = json.loads(response.text)
    except:
        print "Could not load one json"
        return []
    num_pages = int(math.ceil(data[u'results'][u'totalParentCommentsFound']/25.0))
    #Total parent comments is what we want to cycle through pages/offset, but some comments are "replies"
    #So there is a nested/tree like structure for those, but I'm not sure if any are "top picks"
    all_comments = []
    all_comments.extend(data[u'results'][u'comments'])

    for i in range(num_pages):
	time.sleep(.1)#Slow down for rate limiting
	offset = str(25 * (i+1))
        response = requests.get(PRE_URL + url + "&offset=" + offset)
        data = json.loads(response.text)
        all_comments.extend(data[u'results'][u'comments'])
    return all_comments

#Splits dataset into 70/20/10 train/dev/test
#Where 1 = train, 2 = dev, 3 = test
def train_dev_test():
    classification = random.random()
    if classification < .7:
        return 1
    if classification < .9:
        return 2
    return 3

#Function: add_comments_to_db
#Add information about comment to database
def add_comments_to_db(comments, article_url):
    #print "Adding data associated with %s" %article_url
    for c in comments:
        #Setup of comment in DB:
        #(CommentID integer PRIMARY KEY, ArticleURL text, RecommendedFlag integer, 
        #NumReplies integer, Trusted integer, UserDisplayName text, CreateDate integer, 
        #UserID integer, CommentTitle text, Sharing integer, NumRecommendations integer, 
        #EditorSelection boolean, Timespeople integer, CommentText text)
        #print c["commentID"]
	tdt = train_dev_test()
	command = "INSERT OR IGNORE INTO Comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (c["commentID"], article_url, c["recommendedFlag"], c["replyCount"], c["trusted"],
            c["userDisplayName"], c["createDate"], c["userID"], c["commentTitle"],
            c["sharing"], c["recommendations"], c["editorsSelection"], c["timespeople"], c["commentBody"], tdt)
        db_cursor.execute(command, values)



#Open database and access cursor:
comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
db_article_cursor = comments_db.cursor() #Cursor to keep track of article query results
db_cursor = comments_db.cursor() #Cursor to do update of comments table
db_comments_added = comments_db.cursor()
#Run main method:
if __name__ == "__main__":
    main()
#Close database and cursor:
comments_db.commit()
db_comments_added.close()
db_cursor.close()
db_article_cursor.close()
comments_db.close()

