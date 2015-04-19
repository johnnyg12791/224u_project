#nyt_scraper.py

#http://www.pythoncentral.io/introduction-to-sqlite-in-python/
#I like the idea of these sqllite tables to store data

import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import pprint
import numpy as np
import math
from bs4 import BeautifulSoup #also: pip install beautifulsoup4


#For the community API
#API_KEY = 3abe3be579e0b85dac546964182f1dd7:17:15145567
PRE_URL = "http://api.nytimes.com/svc/community/v3/user-content/url.json?api-key=3abe3be579e0b85dac546964182f1dd7:17:15145567&url="

#

def main():
    #We will need to do some work to compile a list of these
    #Another scraping tool/function?
    #We could sort them into editorials/authors/sections of the paper

    urls = ["http://www.nytimes.com/2015/04/17/opinion/help-for-victims-of-crooked-schools.html", "http://www.nytimes.com/2015/04/17/opinion/david-brooks-when-cultures-shift.html"]
    #instead I want to load pickle file
    #and get all URLS


    #{url : {[comment1, comment2, comment3...], url: [comment1, comment2, comment3...], 3 : [...], ....}
    article_comments_dict = {}
    for url in urls:
        #Get a list of all json object comments
        comments = get_comments_from_json(url)
        article_comments_dict[url] = comments
        #Add Data to Datastructure/SQL Table/Whatever..
        #add_data(comments, url)


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



#Add the data to a dict/sql database or whatever
def add_data(data):
    #Sql lite stuff
    pass



if __name__ == "__main__":
    main()