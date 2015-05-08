
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe
import sklearn.metrics as me
from sklearn import svm


class CommentFeatures():

#########Initialization/termination: ###############################
	def __init__(self):
		self.db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
		self.c = self.db.cursor()
		#Queries to return all of training or dev data, respectively. Customize if you need other columns
		self.trainSelectQueryEditorPick = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =1 AND c.EditorSelection = 1"
		self.trainSelectQueryNonEditorPick = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =1 AND c.EditorSelection = 0"

		self.devSelectQueryEditorPick = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =2 AND c.EditorSelection = 1"
		self.devSelectQueryNonEditorPick = "SELECT CommentText, FullText, EditorSelection FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =2 AND c.EditorSelection = 0"

		#Number of reviews to terminate at; useful for debugging
		self.trainCutoffNum = 2000 #float("inf")
		self.proportionEditorPicks = .25 #Artificially grab more editor pick reviews
		#Feature vectors x and "editor results" y for train and dev:
		#(not even going to touch test-- let's leave it clean!)
		#Train:
		self.t_x = []
		self.t_y = []
		#Dev:
		self.d_x = []
		self.d_y = []

	def close(self):
		self.c.close()
		self.db.close()

#########Feature vector creation: ######################################

	def getReviews(self):
		#Grab train examples, add text and "golds:"
		num_grabbed = 0
		for cText, aText, gold in self.c.execute (self.trainSelectQueryEditorPick):
			self.t_x.append(cText)
			self.t_y.append(gold)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
		print "editor picks in"
		for cText, aText, gold in self.c.execute (self.trainSelectQueryNonEditorPick):
			self.t_x.append(cText)
			self.t_y.append(gold)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum: break
		#Grab dev examples, add text and "golds:"
		num_grabbed = 0
		for cText, aText, gold in self.c.execute (self.devSelectQueryEditorPick):
			self.d_x.append(cText)
			self.d_y.append(gold)
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
		for cText, aText, gold in self.c.execute (self.devSelectQueryNonEditorPick):
			self.d_x.append(cText)
			self.d_y.append(gold)
			if num_grabbed > self.trainCutoffNum: break

	#Method: bagOfWords
	#Classification using bag of words model
	#Note that this does not take into account the article text
	def bagOfWords(self, tfidf=True):
		self.getReviews()
		#Choose which vectorizing schematic to use:
		if tfidf:
			#Vectorize BOW, append to train/dev x:
			tfidf_vectorizer = fe.text.TfidfVectorizer() #Set binary to true for rough estim
			tfidf_fit = tfidf_vectorizer.fit(self.t_x + self.d_x)
			self.t_x = tfidf_vectorizer.transform(self.t_x)
			self.d_x = tfidf_vectorizer.transform(self.d_x)
			#self.t_x = tfidf_vectorizer.fit_transform(self.t_x)
			#self.d_x = tfidf_vectorizer.fit_transform(self.d_x)
		else:
			#Use a standard count-vectorizer model
			count_vectorizer = fe.text.CountVectorizer()
			self.t_x = count_vectorizer.fit_transform(self.t_x)
			self.d_x = count_vectorizer.fit_transform(self.d_x)
		print "Done setting up BOW model"

###########Set classifier type + parameters: ############################

	def setLinearSVM(self, C_val=1):
		self.classifier = svm.LinearSVC(C=C_val)
		print "Using linear SVM with C=%.f" % C_val


###########Classification step: ##########################################


	def classify(self):
		print "Starting classifier..."
		self.classifier.fit(self.t_x, self.t_y)
		predict_train = self.classifier.predict(self.t_x)
		predict_dev = self.classifier.predict(self.d_x)

		print "Classified %d samples, using %d feature" % self.t_x.shape
		print "Training accuracy:"
		self.f1_accuracy(predict_train, self.t_y)
		print "Dev accuracy:"
		self.f1_accuracy(predict_dev, self.d_y)

##########Accuracy and Results: ##########################################

	def f1_accuracy(self, predicted_vals, real_vals):
		accuracy = me.f1_score(real_vals, predicted_vals)
		print "F1 accuracy is %.3f" % accuracy
















