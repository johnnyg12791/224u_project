
import sqlite3
import sklearn.feature_extraction as fe
import scipy.stats
from nltk.tag import pos_tag
import numpy as np
import scipy.sparse as ss
import string
import re 
##TODO: alphabetize imports

#Return the probabilities of each word in the vector
def probabilities(sparse_vec):
	if sparse_vec.sum() == 0:
		return sparse_vec
	return sparse_vec/sparse_vec.sum()

#Strip punctuation from text to improve vectorizing
#in next step.
def process(text):
	return re.sub(ur'[!\?\.\,-_()\[\]\"\'\%0123456789]', '', text)

#Vectorize inputs to raw counts; return the probabilities
def raw_count_vectorizer(commentText, articleText):
	#Raw counts:
	vectorizer = fe.text.CountVectorizer(stop_words='english')
	vectorizer.fit(commentText + articleText)
	c_dict = vectorizer.transform(commentText)
	a_dict = vectorizer.transform(articleText)
	return (probabilities(c_dict), probabilities(a_dict))

#Vectorize and score based only on overlap of proper nouns.
def proper_noun_vectorizer(commentText, articleText, articleURL):
	#Pre-process, extract proper nouns from comment:
	comments = process(commentText[0])
	comment_tagged = pos_tag(comments.split())

	comment_nnps = []
	comment_adj = []
	for word, pos in comment_tagged:
		if pos == 'NN' or pos =='NP':
			comment_nnps.append(word)
		if pos == 'ADJ':
			comment_adj.append(word)

	#Do the same for article text; if already done, grab from cache:
	article_nnps = []
	article_adj = []
	article_tagged = "" #REMOVE debug
	if articleURL in a_cache_processed:
		article_nnps = a_cache_processed[articleURL]
		article_adj = a_cache_adj[articleURL]
	else:
		articles = process(articleText[0])
		article_tagged = pos_tag(articles.split())
		for word, pos in article_tagged:
			if pos == 'NN' or pos =='NP':
				article_nnps.append(word)
			if pos == 'ADJ':
				article_adj.append(word)
		a_cache_processed[articleURL] = article_nnps
		a_cache_adj[articleURL] = article_adj

	#Vectorize and return proper nouns:
	vectorizer = fe.text.CountVectorizer()
	c_dict = None
	a_dict = None
	if len(comment_nnps) > 0 or len(article_nnps) > 0:
		vectorizer.fit(comment_nnps + article_nnps)
		c_dict = vectorizer.transform(comment_nnps)
		a_dict = vectorizer.transform(article_nnps)
		c_dict = probabilities(c_dict)
		a_dict = probabilities(a_dict)


	print comment_tagged
	print article_tagged

	print comment_adj
	print article_adj

	#Vectorize and return adjectives:
	adj_vectorizer = fe.text.CountVectorizer()
	c_aj = None
	a_aj = None
	if len(comment_adj) > 0 or len(article_adj) > 0:
		adj_vectorizer.fit(comment_adj + article_adj)
		c_aj = adj_vectorizer.transform(comment_adj)
		a_aj = adj_vectorizer.transform(article_adj)
		c_aj = probabilities(c_aj)
		a_aj = probabilities(a_aj)
	else:
		print "using nones"

	return (c_dict, a_dict, c_aj, a_aj)


#Subroutine to find Kullback-Leibler distance
def KL_score(c_probs, a_probs):
    distance = 0.0
    for i in range(0, c_probs.shape[1]):
        if c_probs[0,i] > 0 and a_probs[0,i] > 0:
            distance += c_probs[0,i] * np.log(c_probs[0,i]/a_probs[0,i])
    return distance


#Calculate KL divergence based on given probability distributions
def KL_divergence(comment_text, article_text, article_url):
	#Raw score:
	c_probs, a_probs = raw_count_vectorizer(comment_text, article_text)
	raw_score = KL_score(c_probs, a_probs)
	
	#Noun-only score + adjective-only score:
	c_probs, a_probs, c_adj_probs, a_adj_probs = proper_noun_vectorizer(comment_text, article_text, article_url)
	noun_score = 0
	if c_probs != None and a_probs != None:
		noun_score = KL_score(c_probs, a_probs)

	adj_score = 0
	if c_adj_probs != None and a_adj_probs != None:
		adj_score = KL_score(c_adj_probs, a_adj_probs)

	return raw_score, noun_score, adj_score

############################# Main run method: ###########################


##DB setup:
db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/may29.db")
loop_cursor = db.cursor()
setter_cursor = db.cursor()
count = 0

#Cache results from articles
a_cache_raw = {}
a_cache_processed = {}
a_cache_adj = {}

get_fulltext_no_repeats_query = "SELECT c.CommentID, CommentText, FullText, KLDistance FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.KLDistance IS NULL "
get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
for c_id, c_text, a_text, a_url in loop_cursor.execute(get_fulltexts_query):
#for c_id, c_text, a_text, klD in loop_cursor.execute(get_fulltext_no_repeats_query):
	if len(c_text) > 0 and len(a_text) > 0: #Check haven't already added kl distance
		raw_kl, noun_kl, adj_kl = KL_divergence([c_text], [a_text], a_url)
		print "Raw: %f; Nouns: %f, Adj: %f - commentID = %d" % (raw_kl, noun_kl, adj_kl, c_id)
		#setter_cursor.execute("UPDATE Features SET KLDistance = ?, KLDistance_Nouns = ?, KLDistance_Adj =? WHERE CommentID = ?", (raw_kl, noun_kl, adj_kl, c_id))
		count += 1
		if count > 10: break
		if count % 1000 == 0:
			print "Have added %d scores" % counter 
			db.commit()

#DB takedown:
db.commit()
setter_cursor.close()
loop_cursor.close()
db.close()








