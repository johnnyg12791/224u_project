
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe


class CommentFeatures():

#########Initialization/termination: ###############################
	def __init__(self):
		self.db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
		self.c = self.db.cursor()
		#Queries to return all of training or dev data, respectively. Customize if you need other columns
		self.trainSelectQuery = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =1"
		self.devSelectQuery = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =2"
		#Number of reviews to terminate at; useful for debugging
		self.trainCutoffNum = 20 #float("inf")
		#Feature vectors x and "editor results" y for train and dev:
		#(not even going to touch test-- let's leave it clean!)
		self.t_x = []
		self.t_y = []
		self.d_x = []
		self.d_y = []

	def close(self):
		self.c.close()
		self.db.close()

#########Feature vector creation: ###############################

	#Method: bagOfWords
	#Classification using bag of words model
	def bagOfWords(self):
		num_grabbed = 0
		for cText, aText, gold in self.c.execute (self.trainSelectQuery):
			print "in query"
			self.t_x.append((cText, aText))
			self.t_y.append(gold)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum: break
		print "before:"
		print self.t_x
		tfidf_vectorizer = fe.text.TfidfVectorizer(stop_words='english', binary=True) #Set binary to true for rough estim
		self.t_x = tfidf_vectorizer.fit_transform(self.t_x)
		print self.t_x

