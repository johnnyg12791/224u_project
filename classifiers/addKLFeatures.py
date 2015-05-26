
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
	return sparse_vec/sparse_vec.sum()

#Strip punctuation from text to improve vectorizing
#in next step.
def process(text_list):
	stripped_text = []
	for text in text_list:
		stripped_text.append(re.sub('[!\?\.\,-_()\[\]\"\']', '', text))
	return text_list

#Vectorize inputs to raw counts; return the probabilities
def raw_count_vectorizer(commentText, articleText):
	#Raw counts:
	vectorizer = fe.text.CountVectorizer(stop_words='english')
	vectorizer.fit(commentText + articleText)
	c_dict = vectorizer.transform(commentText)
	a_dict = vectorizer.transform(articleText)
	return (probabilities(c_dict), probabilities(a_dict))

#Vectorize and score based only on overlap of proper nouns.
def proper_noun_vectorizer(commentText, articleText):
	#Pre-process text:
	comments = process(commentText)
	articles = process(articleText)
	#Extract proper nouns:
	comment_tagged = pos_tag(commentText[0].split())
	article_tagged = pos_tag(articleText[0].split())
	comment_nnps = [word for word,pos in comment_tagged if pos == 'NNP']
	article_nnps = [word for word,pos in article_tagged if pos == 'NNP']
	print comment_nnps
	print article_nnps
	#Vectorize and return proper nouns:
	vectorizer = fe.text.CountVectorizer(stop_words='english')
	vectorizer.fit(comment_nnps + article_nnps)
	c_dict = vectorizer.transform(comment_nnps)
	a_dict = vectorizer.transform(article_nnps)
	return (probabilities(c_dict), probabilities(a_dict))

#Subroutine to find Kullback-Leibler distance
def KL_score(c_probs, a_probs):
    distance = 0.0
    for i in range(0, c_probs.shape[1]):
        if c_probs[0,i] > 0 and a_probs[0,i] > 0:
            distance += c_probs[0,i] * np.log(c_probs[0,i]/a_probs[0,i])
    return distance


#Calculate KL divergence based on given probability distributions
def KL_divergence(comment_text, article_text):
	#Raw score:
	c_probs, a_probs = raw_count_vectorizer(comment_text, article_text)
	raw_score = KL_score(c_probs, a_probs)
	#Noun-only score
	c_probs, a_probs = proper_noun_vectorizer(comment_text, article_text)
	noun_score = KL_score(c_probs, a_probs)
	return raw_score, noun_score

############################# Main run method: ###########################


##DB setup:
db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/all_comments_backup.db")
loop_cursor = db.cursor()
setter_cursor = db.cursor()
count = 0

get_fulltexts_query = "SELECT CommentID, CommentText, FullText FROM ArticleText a, Comments c WHERE c.ArticleURL=a.URL"
for c_id, c_text, a_text in loop_cursor.execute(get_fulltexts_query):
	if len(c_text) > 0 and len(a_text) > 0:
		raw_kl, noun_kl = KL_divergence([c_text], [a_text])
		print "Raw: %f; Nouns: %f" % (raw_kl, noun_kl)
		count += 1
		if count > 1: break #TODO: remove @ debug

#DB takedown:
db.commit()
setter_cursor.close()
loop_cursor.close()
db.close()








