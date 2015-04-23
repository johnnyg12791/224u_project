#create_url_list.py
import sys
import json
import yaml #same: pip install pyyaml
import requests #if this doesnt work, try: pip install requests
import time

#This basically gets all articles from Jan 1, 2013 until now.
#when search term is obama, we get 18,000 articles
def main():
    term = sys.argv[1]
    begin = "http://api.nytimes.com/svc/search/v2/articlesearch.json?q=" + term + "&fq=source:(\"The%20New%20York%20Times\")&begin_date="
    end = "&sort=oldest&api-key=eb94970b5aef4d0e8664c8c8c26da4fe:4:15145567"
    page = 0
    num_pages = 0
    date = 20130101
    all_urls = []
    while(date < 20150401):#Go until april 1st
        while(page < 101):
            query = begin + str(date) + "&page=" + str(page) + end
            response = requests.get(query)
            data = json.loads(response.text)
            if(num_pages == 0):
                num_pages = data[u'response'][u'meta'][u'hits']/10
            for item in data[u'response'][u'docs']:
                url = item[u'web_url']
                if(url not in all_urls):
                    all_urls.append(url)
            page += 1
            #For rate limiting
            time.sleep(.1)
            print "Added %d of %d total urls" % (len(all_urls), num_pages*10)
        date += 100
        page = 0
        if(date > 20131300 and date < 20140000):
            date = 20140101
        elif(date > 20141300 and date < 20150000):
            date = 20150101
        print date
    

    output_file = open("url_list_" + term + ".txt", 'wb')
    for url in all_urls:
        output_file.write(url)
        output_file.write('\n')
    output_file.close()


if __name__ == "__main__":
    main()
