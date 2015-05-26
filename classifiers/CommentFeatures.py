
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe
import sklearn.metrics as me
from sklearn import svm
import csv


class CommentFeatures():

#########Initialization/termination: ###############################
	def __init__(self):
		self.db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
		self.c = self.db.cursor()
		self.gold_cursor = self.db.cursor()

		#Queries to return all of training or dev data, respectively. Customize if you need other columns
		self.selectStatement = "SELECT CommentID, CommentText FROM Comments"

		#User should provide a featureSelectQuery 
		self.featureSelectionQuery = None
		self.goldQuery = "SELECT EditorSelection FROM Comments WHERE CommentID = (?)"       

		#Number of reviews to terminate at; useful for debugging
		self.num_comments = float("inf")
		self.numInTrain = 0
		self.numInDev = 0
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
		self.gold_cursor.close()
		self.db.close()

#########Initialize and custom settings: ###############################

	#Modify the default statement which is used to grab all reviews
	def setSelectStatement(self, statement):
		self.selectStatement = statement

	#Add additional features to be used in the classification.
	def setFeaturesQuery(self, featuresStatement):
		self.featureSelectionQuery = featuresStatement

	#Limit number of reviews for debugging/classification purposes
	def limitNumComments(self, upperLimit):
		self.num_comments = upperLimit

	def setVerbose(self, verbose=True):
		self.verbose = verbose 

#########Feature vector creation: ######################################

	#Method: createSelectStatments
	#A method which will create custom select statements from the user-entered version for
	#editor pick and non-editor pick train and dev data.
	def createSelectStatements(self, statement):
		self.trainSelectQueryEditorPick =  statement + " AND c.TrainTest =1 AND c.EditorSelection = 1"
		self.trainSelectQueryNonEditorPick = statement + " AND c.TrainTest =1 AND c.EditorSelection = 0"
		self.devSelectQueryEditorPick = statement + " AND c.TrainTest =2 AND c.EditorSelection = 1"
		self.devSelectQueryNonEditorPick = statement + " AND c.TrainTest =2 AND c.EditorSelection = 0"

	#Method: getReviews
	#A method to return review fulltext as self.t_x and self.d_x, as well as a dict
	#representing the additional features grabbed for each comment/article pair
	def getCommentsBagOfWords(self):
		#Grab train examples, add text and "golds:"
		num_grabbed = 0	
		#Artificially add 25% editor picks
		for cID, cText, gold in self.c.execute (self.trainSelectQueryEditorPick):
			self.t_x.append(cText)
			self.t_y.append(gold)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
		#Add 75% non-editor picks
		for cID, cText, gold in self.c.execute (self.trainSelectQueryNonEditorPick):
			self.t_x.append(cText)
			self.t_y.append(gold)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum: break
		#Grab dev examples, add text and "golds:"
		num_grabbed = 0
		#Artificially add 25% editor picks
		for cID, cText, gold in self.c.execute (self.devSelectQueryEditorPick):
			self.d_x.append(cText)
			self.d_y.append(gold)
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
		#Add 75% non-editor picks
		for cID, cText, gold in self.c.execute (self.devSelectQueryNonEditorPick):
			self.d_x.append(cText)
			self.d_y.append(gold)
			if num_grabbed > self.trainCutoffNum: break

	#Method: commentGold
	#Returns the gold label for a given comment ID
	def commentGold(self, commentID):
		gold_cursor = self.db.cursor()
		gold_cursor.execute(self.goldQuery, [commentID])
		gold = gold_cursor.fetchone()[0]
		return gold 

	#Method: makeFeatureDict
	#This method will return a list of dictionaries containing the desired features. 
	def makeFeatureDict(self, query, cutoff):
		X = []
		Y = []
		num_comments = 0
		for row in self.c.execute(query):
			feature_dict = {}
			for i, col in enumerate(self.c.description):
				val = row[i]
				if val == None: ##TODO: Remove once no longer adding null features
					val = 0
				feature_dict[col[0]] = val
			commentID = feature_dict["CommentID"]
			#gold = self.commentGold(commentID)
			print feature_dict
			gold = feature_dict["EditorSelection"] #Second thing passed has to be editor pick
			X.append(feature_dict)
			Y.append(gold)
			#Check cutoff:
			num_comments += 1
			if num_comments > cutoff: break 
		return (X, Y)


	#Method: getCommentFeatures
	#This method will set self.t_x and self.d_x to be vectors of comment features, and
	#t_y and d_y to be the gold labels. Note that this relies on passing the model a
	#feature selection query, and must have first thing you request be comment ID.
	def getCommentFeatures(self):
		self.createSelectStatements(self.featureSelectionQuery)
		#Train, editor
		train_editorX, Y = self.makeFeatureDict(
			self.trainSelectQueryEditorPick, self.num_comments * self.proportionEditorPicks)
		self.t_x.extend(train_editorX)
		self.t_y.extend(Y)

		if self.verbose:
			print "Created training/editor pick vectors"

		#Train, non-editor
		train_noneditorX, Y = self.makeFeatureDict(
			self.trainSelectQueryNonEditorPick, self.num_comments * (1-self.proportionEditorPicks))
		self.t_x.extend(train_noneditorX)
		self.t_y.extend(Y)

		if self.verbose:
			print "Created training/non-editor pick vectors"

		#Dev, editor
		dev_editorX, Y = self.makeFeatureDict(
			self.devSelectQueryEditorPick, self.num_comments * self.proportionEditorPicks)
		self.d_x.extend(dev_editorX)
		self.d_y.extend(Y)

		if self.verbose:
			print "Created dev/editor pick vectors"

		#Dev, non-editor
		dev_noneditorX, Y = self.makeFeatureDict(
			self.devSelectQueryNonEditorPick, self.num_comments * (1-self.proportionEditorPicks))
		self.d_x.extend(dev_noneditorX)
		self.d_y.extend(Y)


		if self.verbose:
			print "Created comment feature vectors"

################ Model Selection: ###########################

	#Method: bagOfWords
	#Classification using bag of words model
	#Note that this does not take into account the article text
	def bagOfWordsModel(self, tfidf=True):
		self.getCommentsBagOfWords()
		#Choose which vectorizing schematic to use:
		if tfidf:
			print "Creating features using tf-idf..."
			#Vectorize using TF-IDF scheme:
			tfidf_vectorizer = fe.text.TfidfVectorizer() #Set binary to true for rough estim
			tfidf_vectorizer.fit(self.t_x + self.d_x)
			self.t_x = tfidf_vectorizer.transform(self.t_x)
			self.d_x = tfidf_vectorizer.transform(self.d_x)
		else:
			print "Creating features using non-normalized bag of words..."
			#Use a standard count-vectorizer model
			count_vectorizer = fe.text.CountVectorizer()
			count_vectorizer.fit(self.t_x + self.d_x)
			self.t_x = count_vectorizer.transform(self.t_x)
			self.d_x = count_vectorizer.transform(self.d_x)

		if self.verbose:
			print "Vectorized bag of words."


	#Method: extractCommentFeatures
	#Populates self.t_x and self.d_x with features from database, without pullijg
	#any of the text associated with the comment.
	def featureModel(self):

		if self.verbose:
			print "Slow af step"

		#Initialize t_x, d_x, t_y, and d_y using getCommentFeatures method
		self.getCommentFeatures()

		if self.verbose:
			print "Selected comment features"
 
		#Vectorize comments; this would be the place to apply feature functions as desired
		self.vectorizer = fe.DictVectorizer()
		self.vectorizer.fit(self.t_x + self.d_x)

		self.t_x = self.vectorizer.transform(self.t_x)
		self.d_x = self.vectorizer.transform(self.d_x)

		if self.verbose:
			print "Vectorized extracted features"




###########Set classifier type + parameters: ############################

	#Method: setLinearSVM
	#Sets classifier to be very basic linear SVM
	def setLinearSVM(self, C_val=1):
		self.classifier = svm.LinearSVC(C=C_val)
		print "Using linear SVM with C=%.f" % C_val


###########Classification step: ##########################################


	def classify(self):
		#Fit classifier, then classify train and dev examples
		print "Starting classifier..."
		print self.t_x 
		print self.vectorizer.get_feature_names()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train = self.classifier.predict(self.t_x)
		predict_dev = self.classifier.predict(self.d_x)

		#Report F1 statistics
		print "Classified %d samples, using %d features" % self.t_x.shape
		print "Training accuracy:"
		t_acc = self.f1_accuracy(predict_train, self.t_y)
		print "Dev accuracy:"
		d_acc = self.f1_accuracy(predict_dev, self.d_y)

		#Save results to CSV
		self.save_results(t_acc, d_acc)

##########Accuracy and Results: ##########################################

	def f1_accuracy(self, predicted_vals, real_vals):
		accuracy = me.f1_score(real_vals, predicted_vals)
		print "F1 accuracy is %.3f" % accuracy
		return accuracy


	def save_results(self, train, dev):
		with open("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/results.csv", 'a') as results_file:
			fields = ['f1_train', 'f1_dev', 'num_samples', 'num_features', 'classifier_type']
			writer = csv.DictWriter(results_file, fieldnames=fields)
			n_samples, n_features = self.t_x.shape
			writer.writerow({'f1_train': train, 'f1_dev': dev, 
    			'num_samples': n_samples, 'num_features': n_features, 'classifier_type': self.classifier})















