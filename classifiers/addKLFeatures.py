
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
def process(text_list):
	stripped_text = []
	for text in text_list:
		stripped_text.append(re.sub(ur'[!\?\.\,-_()\[\]\"\'\%0123456789]', '', text))
	return stripped_text

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
	#Pre-process text:
	comments = process(commentText)
	#Extract proper nouns:
	comment_tagged = pos_tag(comments[0].split())

	#comment_nnps = [word for word,pos in comment_tagged if pos == 'NN' or pos =='NP']
	#article_nnps = [word for word,pos in article_tagged if pos == 'NN' or pos =='NP']

	comment_nnps = u""
	for word, pos in comment_tagged:
		if pos == 'NN' or pos =='NP':
			comment_nnps += u" " + word

	article_nnps = u""
	if articleURL in article_metas:
		article_nnps = article_metas[articleURL]
	else:
		articles = process(articleText)
		article_tagged = pos_tag(articles[0].split())
		for word, pos in article_tagged:
			if pos == 'NN' or pos =='NP':
				article_nnps += u" " + word
		article_metas[articleURL] = article_nnps

	#Vectorize and return proper nouns:
	vectorizer = fe.text.CountVectorizer()
	vectorizer.fit([comment_nnps] + [article_nnps])
	c_dict = vectorizer.transform([comment_nnps])
	a_dict = vectorizer.transform([article_nnps])

	return (probabilities(c_dict), probabilities(a_dict))


#Subroutine to find Kullback-Leibler distance
def KL_score(c_probs, a_probs):
    distance = 0.0
    for i in range(0, c_probs.shape[1]):
        if c_probs[0,i] > 0 and a_probs[0,i] > 0:
            distance += c_probs[0,i] * np.log(c_probs[0,i]/a_probs[0,i])
    return distance


#Calculate KL divergence based on given probability distributions
def KL_divergence(comment_text, article_text, a_url):
	#Raw score:
	c_probs, a_probs = raw_count_vectorizer(comment_text, article_text)
	raw_score = KL_score(c_probs, a_probs)
	
	#raw_score = scipy.stats.entropy(c_probs.data, qk=a_probs.data)
	#Noun-only score
	c_probs, a_probs = proper_noun_vectorizer(comment_text, article_text, a_url)
	noun_score = KL_score(c_probs, a_probs)
	return raw_score, noun_score

############################# Main run method: ###########################


##DB setup:
db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/may31_day.db")
loop_cursor = db.cursor()
setter_cursor = db.cursor()
count = 0
article_metas = {}

#get_fulltext_no_repeats_query = "SELECT c.CommentID, CommentText, FullText, KLDistance FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.KLDistance IS NULL "
get_fulltext_norepeats_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c, Features f WHERE c.ArticleURL=a.URL AND c.CommentID = f.CommentID AND f.KLDistance IS NULL"
#get_fulltexts_query = "SELECT c.CommentID, c.CommentText, a.FullText, a.URL FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
for c_id, c_text, a_text, a_url in loop_cursor.execute(get_fulltext_norepeats_query):
#for c_id, c_text, a_text, a_url, klD in loop_cursor.execute(get_fulltext_no_repeats_query):
	if len(c_text) > 0 and len(a_text) > 0: #Check haven't already added kl distance
		raw_kl, noun_kl = KL_divergence([c_text], [a_text], a_url)
#		print "Raw: %f; Nouns: %f: commentID = %d" % (raw_kl, noun_kl, c_id)
		setter_cursor.execute("UPDATE Features SET KLDistance = ?, KLDistance_Nouns = ? WHERE CommentID = ?", (raw_kl, noun_kl, c_id))
		count += 1
		if count % 100 == 0:
			print "+100"
		if count % 1000 == 0:
			print "Added %d; still chugging" % count 
			db.commit()

#DB takedown:
db.commit()
setter_cursor.close()
loop_cursor.close()
db.close()








