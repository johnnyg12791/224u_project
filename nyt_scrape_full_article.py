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
import lxml.html as lh
import time




#TODO: make num_to_scrape something you can call
NUM_TO_SCRAPE = 10 #How many articles you wish to scrape at this time
SCRAPE_PAUSE = 1 #pause between requests to NYT.com

#Add fulltext of NYT articles to "Articles" table in DB
def main():
	#Find articles which need their fulltext added:
	numGrabbed = 0
	command = "SELECT URL FROM Articles WHERE HaveFullText = 0"

	for url in loop_cursor.execute(command):
		#Upload full text
		save_full_article(url)
		#Update number, break if at max
		numGrabbed += 1
		print "Processed %d/%d articles" % (numGrabbed, NUM_TO_SCRAPE)
		if numGrabbed == NUM_TO_SCRAPE:
			break
		time.sleep(SCRAPE_PAUSE)

#Note: borrowed heavily from:
# http://nbviewer.ipython.org/gist/johnb30/4743272
def save_full_article(url):
	page = requests.get(url)
	doc = lh.fromstring(page.content)
	text = doc.xpath('//p[@itemprop="articleBody"]')
	finalText = str()
	for par in text:
	    finalText += par.text_content()

	print finalText #DEBUG
	exec_cursor.execute("UPDATE Articles SET HaveFullText=1 WHERE URL = ?", (url,))
	exec_cursor.execute("UPDATE Articles SET FullText= ? WHERE URL = ?", (finalText, url))

#Open database and access cursors:
comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
loop_cursor = comments_db.cursor() #Cursor to do update of comments table
exec_cursor = comments_db.cursor()
#Run main method:
if __name__ == "__main__":
    main()
#Close database and cursors:
comments_db.commit()
loop_cursor.close()
comments_db.close()
exec_cursor.close()




