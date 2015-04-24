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
import sqlite3
from nyt_urls import *


#For the community API=
#API_KEY = 3abe3be579e0b85dac546964182f1dd7:17:15145567
#Marks API Key e7c94a47f04362f395038e2126907219:12:71919922
#TODO: modify so cycle through API keys
PRE_URL = "http://api.nytimes.com/svc/community/v3/user-content/url.json?api-key=e7c94a47f04362f395038e2126907219:12:71919922&url="
#

def main():
    ##Pull unprocessed articles from DB:
    unprocessedArticlesCommand = "SELECT URL FROM Articles WHERE CommentsAdded = 0"
    for url in db_article_cursor.execute(unprocessedArticlesCommand):
        print "next article:"
        article_url = url[0] #So that it isn't treated as a tuple
        #Process article:
        process_article_comments(article_url)
        #Mark article as processed:
        mark_article_processed(article_url)
        print "Done processing url %s" % article_url

#Function: process_article_comments
#Method to scrape all of the comments from the community API associated
#with the given article URL.
def process_article_comments(article_url):
    #Get a list of all json object comments for this URL:
    comments = get_comments_from_json(article_url)
    print "Url %s has %d comments" %(article_url, len(comments))
    if len(comments) > 0:
        #If article has comments, add them to DB
        add_comments_to_db(comments, article_url)

#Function: mark_article_processsed
#SQL call with the inner (comments) cursor to mark the given articleURL (key)
#as being processed.
def mark_article_processed(article_url):
    db_cursor.execute("UPDATE Articles SET CommentsAdded=1 WHERE URL = ?", (article_url,))


#create one giant json thing with all of that articles data?
#The issue is that there is only 25 comments per request, so we need multiple with changes of the offset
#or just get each json and store it immediately in our SQL table
def get_comments_from_json(url):
    response = requests.get(PRE_URL + url)
    data = json.loads(response.text)
    num_pages = int(math.ceil(data[u'results'][u'totalParentCommentsFound']/25.0))
    #Total parent comments is what we want to cycle through pages/offset, but some comments are "replies"
    #So there is a nested/tree like structure for those, but I'm not sure if any are "top picks"

    all_comments = []
    all_comments.extend(data[u'results'][u'comments'])

    for i in range(num_pages):
        offset = str(25 * (i+1))
        response = requests.get(PRE_URL + url + "&offset=" + offset)
        data = json.loads(response.text)
        #pprint.pprint(data)
        all_comments.extend(data[u'results'][u'comments'])
    print "url: ", url, " has ", str(len(all_comments)), " comments"
    return all_comments



#Function: add_comments_to_db
#Add information about comment to database
def add_comments_to_db(comments, article_url):
    print "Adding data associated with %s" %article_url
    for c in comments:
        #Setup of comment in DB:
        #(CommentID integer PRIMARY KEY, ArticleURL text, RecommendedFlag integer, 
        #NumReplies integer, Trusted integer, UserDisplayName text, CreateDate integer, 
        #UserID integer, CommentTitle text, Sharing integer, NumRecommendations integer, 
        #EditorSelection boolean, Timespeople integer, CommentText text)
        command = "INSERT INTO Comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (c["commentID"], article_url, c["recommendedFlag"], c["replyCount"], c["trusted"],
            c["userDisplayName"], c["createDate"], c["userID"], c["commentTitle"],
            c["sharing"], c["recommendations"], c["editorsSelection"], c["timespeople"], c["commentBody"])
        db_cursor.execute(command, values)





#Open database and access cursor:
comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
db_article_cursor = comments_db.cursor() #Cursor to keep track of article query results
db_cursor = comments_db.cursor() #Cursor to do update of comments table
#Run main method:
if __name__ == "__main__":
    main()
#Close database and cursor:
comments_db.commit()
db_cursor.close()
db_article_cursor.close()
comments_db.close()





