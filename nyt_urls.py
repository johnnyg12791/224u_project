#nyt_urls.py
import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import pprint
import numpy as np
import math
from bs4 import BeautifulSoup #also: pip install beautifulsoup4
import pickle

#This returns a list of urls to different NYT articles
#We will keep track of the URL, Author, Section, Date


#Most popular api key
#API_KEY = e548999ea9b04cf78d32d9359d1f03a5:15:15145567

def main():
    #Use api to get json objects
    article_list = []
    URL = "http://api.nytimes.com/svc/mostpopular/v2/mostemailed/all-sections/30?api-key=e548999ea9b04cf78d32d9359d1f03a5:15:15145567"
    response = requests.get(URL)

    #Create Article objects from that
    data = json.loads(response.text)
    for item in data[u'results']:
        article_list.append(Article(item))

    num_results = data[u'num_results']
    #Cycle through all pages, getting the 
    num_pages = int(math.ceil(num_results/20.0))
    for i in range(num_pages):
        offset = str(20*(i+1))
        response = requests.get(URL + "&offset=" + offset)
        data = json.loads(response.text)
        for item in data[u'results']:
            article_list.append(Article(item))       
        print len(article_list), " out of ", num_results
    #Add them all to a list, then pickle
    pickle.dump(article_list, open( "articles.p", "wb" ) )


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


if __name__ == "__main__":
    main()


#This prints a list of all NYT sections, if you ever want that
def print_all_sections():
    response = requests.get("http://api.nytimes.com/svc/mostpopular/v2/mostemailed/sections-list?api-key=e548999ea9b04cf78d32d9359d1f03a5:15:15145567")
    data = json.loads(response.text)
    for result in data[u'results']:
        print str(result[u'name'])