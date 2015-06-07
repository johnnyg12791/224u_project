
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe
import sklearn.metrics as me
from sklearn import svm
from sklearn import linear_model
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA 
import csv
import scipy.sparse as sps 
from matplotlib.mlab import PCA as mlabPCA
import heapq
import sklearn
import string
import time
from sklearn.feature_selection import RFE 
import distributedwordreps
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
#TODO: alphabetize imports


class CommentFeatures():

#########Initialization/termination: ###############################
	def __init__(self, DB_PATH="nyt"):
		if DB_PATH == "nyt" :
			self.db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
		else:
			self.db = sqlite3.connect(DB_PATH)
		self.c = self.db.cursor()
		self.gold_cursor = self.db.cursor()

		#Queries to return all of training or dev data, respectively. Customize if you need other columns
		self.selectStatement = "SELECT CommentID, CommentText, EditorSelection FROM Comments c WHERE CommentText IS NOT NULL "
		self.trainCutoffNum = float("inf")
		self.devCutoffNum = float("inf")

		self.zeroBlanks = False #A parameter to set all null cells in table to 0
		self.preprocessText = False

		#User should provide a featureSelectQuery 
		self.featureSelectionQuery = None
		self.goldQuery = "SELECT EditorSelection FROM Comments WHERE CommentID = (?)"       

		#Number of reviews to terminate at; useful for debugging
		self.num_comments = float("inf")
		self.numInTrain = 0
		self.numInDev = 0
		self.proportionEditorPicksTrain = .5 #Artificially grab more editor pick reviews
		self.proportionEditorPicksDev = .5
		#Feature vectors x and "editor results" y for train and dev:
		#(not even going to touch test-- let's leave it clean!)
		#Train:
		self.t_x = []
		self.t_y = []
		#Dev:
		self.d_x = []
		self.d_y = []

		#Vectors to store CommentIDs (for use in misclassification analysis, etc)
		self.t_IDs = []
		self.d_IDs = []

		self.BOWvectorizer = None #A standin for "using bag of words"
		self.save_file="afs"
		self.save_file="results.csv"

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

	#Method: limitNumComments
	#Limit number of reviews for debugging/classification purposes
	def limitNumComments(self, upperLimit, devUpperLimit):
		self.trainCutoffNum = upperLimit
		self.devCutoffNum = devUpperLimit

	#Method: setVerbose
	#Set verbosity to "on"; note that right now this is 80% debugging output
	def setVerbose(self, verbose=True):
		self.verbose = verbose 

	#Method: zeroBlankColumns
	#When encountering a null value in a loop, treat it as if it is a zero.
	#(the alternative is for NaNs to be returned)
	def zeroBlankColumns(self):
		self.zeroBlanks = True

	#Method: preprocessText
	#A method that will first strip punctuation and lowecase a string before
	#vectorization step.
	def preprocessText(self):
		self.preprocessText = True 

	#Method: setEditorPicksProportion
	#Set the artificial number of editor picks to be "proportion"
	def setEditorPicksProportion(self, train_proportion, dev_proportion = -1):
		self.proportionEditorPicksTrain = train_proportion
		if dev_proportion == -1:
			self.proportionEditorPicksDev = train_proportion
		else:
			self.proportionEditorPicksDev = dev_proportion 

	def setResultsFile(self, filename):
		self.save_file = filename

#########Raw feature vector creation: ######################################

	#Method: createSelectStatments
	#A method which will create custom select statements from the user-entered version for
	#editor pick and non-editor pick train and dev data.
	#The postCondition paremeter refers to whether the passed query already has a "WHERE"
	#condition included (such as SELECT * WHERE c.ID = f.ID). In this case, must append "ANDS"
	def createSelectStatements(self, statement):
		#Check if statement was created using a postcondition (in which case, don't use AND)
		postCondition = string.find(statement, "WHERE")
		if postCondition > -1:
			self.trainSelectQueryEditorPick =  statement + " AND f.TrainTest =1 AND f.EditorSelection = 1"
			self.trainSelectQueryNonEditorPick = statement + " AND f.TrainTest =1 AND f.EditorSelection = 0"
			self.devSelectQueryEditorPick = statement + " AND f.TrainTest =2 AND f.EditorSelection = 1"
			self.devSelectQueryNonEditorPick = statement + " AND f.TrainTest =2 AND f.EditorSelection = 0"
		else:
			self.trainSelectQueryEditorPick =  statement + " WHERE TrainTest =1 AND EditorSelection = 1"
			self.trainSelectQueryNonEditorPick = statement + " WHERE TrainTest =1 AND EditorSelection = 0"
			self.devSelectQueryEditorPick = statement + " WHERE TrainTest =2 AND EditorSelection = 1"
			self.devSelectQueryNonEditorPick = statement + " WHERE TrainTest =2 AND EditorSelection = 0"

	#Method: createCommentIDSelectStatement
	#Create individual select statement that will pull the features associated with
	#a given comment ID.
	def createCommentIDSelectStatement(self, statement, c_id):
		return statement + " AND c.CommentID = " + str(c_id)

	#Method: getReviews
	#A method to return review fulltext as self.t_x and self.d_x, as well as a dict
	#representing the additional features grabbed for each comment/article pair
	#The t_x and d_x parameters are in case you are going to run another features set
	#after bag of words; in which case, you will want to vectorize these vectors separately.
	def getCommentsBagOfWords(self, t_x, d_x, returnCommentIDs=False):
		self.createSelectStatements(self.selectStatement)
		#Create list of comment IDs for feature extraction: 
		t_commentIDs = [] 
		d_commentIDs = []
		#Grab train examples, add text and "golds:"
		num_grabbed = 0	
		#Artificially add 25% editor picks
		for cID, cText, gold in self.c.execute (self.trainSelectQueryEditorPick):
			t_x.append(cText)
			self.t_y.append(gold)
			if returnCommentIDs: t_commentIDs.append(cID)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicksTrain: break
		#Add 75% non-editor picks
		for cID, cText, gold in self.c.execute (self.trainSelectQueryNonEditorPick):
			t_x.append(cText)
			self.t_y.append(gold)
			if returnCommentIDs: t_commentIDs.append(cID)
			num_grabbed += 1
			if num_grabbed > self.trainCutoffNum: break
		#Grab dev examples, add text and "golds:"
		num_grabbed = 0
		#Artificially add 25% editor picks
		for cID, cText, gold in self.c.execute (self.devSelectQueryEditorPick):
			d_x.append(cText)
			self.d_y.append(gold)
			if returnCommentIDs: d_commentIDs.append(cID)
			if num_grabbed > self.devCutoffNum * self.proportionEditorPicksDev: break
		#Add 75% non-editor picks
		for cID, cText, gold in self.c.execute (self.devSelectQueryNonEditorPick):
			d_x.append(cText)
			self.d_y.append(gold)
			if returnCommentIDs: d_commentIDs.append(cID)
			num_grabbed +=1
			if num_grabbed > self.devCutoffNum: break

		#Return comment IDs; useful when we want to vectorize this dict separately
		return t_commentIDs, d_commentIDs


	#Method: commentGold
	#Returns the gold label for a given comment ID
	def commentGold(self, commentID):
		gold_cursor = self.db.cursor()
		gold_cursor.execute(self.goldQuery, [commentID])
		gold = gold_cursor.fetchone()[0]
		return gold 

	#Method: singleCommentFeatureDict
	#This method will create a single feature dict corresponding to a single row.
	def singleCommentFeatureDict(self, row):
		feature_dict = {}
		gold = 0
		#for i, col in enumerate(row):
		for i, col in enumerate(self.c.description):
			val = row[i]
			if val == None: ##TODO: Remove once no longer adding null features
				val = 0
			#Make sure we don't add the editor selection to the feature dict!
			if col[0] == "EditorSelection":
				gold = row[i]
			else:
				feature_dict[col[0]] = val
		return feature_dict, gold 

	def getFeatureRow(self, featureQuery, commentID):
		query = self.createCommentIDSelectStatement(featureQuery, commentID)
		self.c.execute(query)
		row = self.c.fetchone()
		return self.singleCommentFeatureDict(row)[0]

	#Method: makeFeatureDict
	#This method will return a list of dictionaries containing the desired features. 
	#VectorizeBOW will perform a separate vectorization step on the dict entry titled
	#CommentText.
	def makeFeatureDict(self, query, cutoff, vectorizeBOW=False):
		X = []
		bow_X = []
		Y = []
		ID_vec = []
		num_comments = 0
		for row in self.c.execute(query):
			feature_dict = {}
			#blanks_flag = 0
			for i, col in enumerate(self.c.description):
				val = row[i]
				if val == None and self.zeroBlanks:
					val = 0
					#blanks_flag = 1 #Hackey way to screen out "incompletely featured" comments
				#Append EditorSelection to golds:
				if col[0] == "EditorSelection":
					gold = row[i]
				elif col[0] == "CommentText":
					bow_X.append(val)
				elif col[0] == "CommentID":
					ID_vec.append(val)
				elif col[0] == "TrainTest":
					continue
				#Add columns to features:
				else:
					feature_dict[col[0]] = val

			if vectorizeBOW:
				#Precondition: must have selected CommentText
				commentText = feature_dict["CommentText"]

			#if blanks_flag == 0:
			X.append(feature_dict)
			Y.append(gold)
			#Check cutoff:
			num_comments += 1
			if num_comments > cutoff: break 
		return (X, Y, bow_X, ID_vec)


	#Method: getCommentFeatures
	#This method will set self.t_x and self.d_x to be vectors of comment features, and
	#t_y and d_y to be the gold labels. Note that this relies on passing the model a
	#feature selection query, and must have first thing you request be comment ID.
	#The split parameter is for splitting our input based on some feature.
	def getCommentFeatures(self):
		self.createSelectStatements(self.featureSelectionQuery)

		#Train and dev bag of words representations
		t_bow_X = []
		d_bow_X = []

		#Train, editor
		train_editorX, Y, bX, ids = self.makeFeatureDict(
			self.trainSelectQueryEditorPick, self.trainCutoffNum * self.proportionEditorPicksTrain)
		self.t_x.extend(train_editorX)
		self.t_y.extend(Y)
		t_bow_X.extend(bX)
		self.t_IDs.extend(ids)

		if self.verbose:
			print "Created training/editor pick vectors"

		#Train, non-editor
		train_noneditorX, Y, bX, ids = self.makeFeatureDict(
			self.trainSelectQueryNonEditorPick, self.trainCutoffNum * (1-self.proportionEditorPicksTrain))
		self.t_x.extend(train_noneditorX)
		self.t_y.extend(Y)
		t_bow_X.extend(bX)
		self.t_IDs.extend(ids)

		if self.verbose:
			print "Created training/non-editor pick vectors"

		#Dev, editor
		dev_editorX, Y, bX, ids = self.makeFeatureDict(
			self.devSelectQueryEditorPick, self.devCutoffNum * self.proportionEditorPicksDev)
		self.d_x.extend(dev_editorX)
		self.d_y.extend(Y)
		d_bow_X.extend(bX)
		self.d_IDs.extend(ids)


		if self.verbose:
			print "Created dev/editor pick vectors"

		#Dev, non-editor
		dev_noneditorX, Y, bX, ids = self.makeFeatureDict(
			self.devSelectQueryNonEditorPick, self.devCutoffNum * (1-self.proportionEditorPicksDev))
		self.d_x.extend(dev_noneditorX)
		self.d_y.extend(Y)
		d_bow_X.extend(bX)
		self.d_IDs.extend(ids)

		if self.verbose:
			print "Created dev/non-editor pick vectors"

		#Return train and dev bag of words representations
		return t_bow_X, d_bow_X

	def featureDictSplitClassifier(self, query, cutoff, vectorizeBOW=False, splitOn=20):
		short_X = []
		short_bow = []
		long_X = []
		long_bow = []
		short_Y = []
		long_Y = []
		short_IDS = []
		long_IDS = []

		num_comments = 0
		for row in self.c.execute(query):
			feature_dict = {}
			for i, col in enumerate(self.c.description):
				val = row[i]
				if val == None and self.zeroBlanks:
					val = 0
				feature_dict[col[0]] = val

			commentText = feature_dict.pop("CommentText")
			length_comment = len(commentText.split())
			if length_comment > splitOn:
				long_Y.append(feature_dict.pop("EditorSelection"))
				long_IDS.append(feature_dict.pop("CommentID"))
				long_bow.append(commentText)
				long_X.append(feature_dict)
			else:
				short_Y.append(feature_dict.pop("EditorSelection"))
				short_IDS.append(feature_dict.pop("CommentID"))
				short_bow.append(commentText)
				short_X.append(feature_dict)

			#Check cutoff:
			num_comments += 1
			if num_comments > cutoff: break 
		return (short_X, short_bow, short_Y, short_IDS, long_X, long_bow, long_Y, long_IDS)

	#Method: getCommentsSplitClassifier
	#This method will set self.t_x and self.d_x to be vectors of comment features, and
	#t_y and d_y to be the gold labels. Note that this relies on passing the model a
	#feature selection query, and must have first thing you request be comment ID.
	#The split parameter is for splitting our input based on some feature.
	def getCommentsSplitClassifier(self, splitOn):

		self.s_t_x = []
		self.l_t_x = []
		self.s_d_x = []
		self.l_d_x = []
		self.s_t_y = []
		self.l_t_y = []
		self.s_d_y = []
		self.l_d_y = []
		self.s_t_ID = []
		self.l_t_ID = []
		self.s_d_ID = []
		self.l_d_ID = []

		self.createSelectStatements(self.featureSelectionQuery)

		#Train and dev bag of words representations
		s_t_bow_X = []
		l_t_bow_X = []
		s_d_bow_X = []
		l_d_bow_X = []

		#Train, editor
		short_X, short_bow, short_Y, short_IDS, long_X, long_bow, long_Y, long_IDS = self.featureDictSplitClassifier(
			self.trainSelectQueryEditorPick, self.trainCutoffNum * self.proportionEditorPicksTrain, splitOn)

		self.s_t_x.extend(short_X)
		self.l_t_x.extend(long_X)
		self.s_t_y.extend(short_Y)
		self.l_t_y.extend(long_Y)
		s_t_bow_X.extend(short_bow)
		l_t_bow_X.extend(long_bow)
		self.s_t_ID.extend(short_bow)
		self.l_t_ID.extend(long_bow)

		if self.verbose:
			print "Created training/editor pick vectors"

		#Train, non-editor
		short_X, short_bow, short_Y, short_IDS, long_X, long_bow, long_Y, long_IDS = self.featureDictSplitClassifier(
			self.trainSelectQueryNonEditorPick, self.trainCutoffNum * (1-self.proportionEditorPicksTrain), splitOn)
		self.s_t_x.extend(short_X)
		self.l_t_x.extend(long_X)
		self.s_t_y.extend(short_Y)
		self.l_t_y.extend(long_Y)
		s_t_bow_X.extend(short_bow)
		l_t_bow_X.extend(long_bow)
		self.s_t_ID.extend(short_bow)
		self.l_t_ID.extend(long_bow)

		if self.verbose:
			print "Created training/non-editor pick vectors"

		#Dev, editor
		short_X, short_bow, short_Y, short_IDS, long_X, long_bow, long_Y, long_IDS = self.featureDictSplitClassifier(
			self.devSelectQueryEditorPick, self.trainCutoffNum * self.proportionEditorPicksDev, splitOn)
		self.s_d_x.extend(short_X)
		self.l_d_x.extend(long_X)
		self.s_d_y.extend(short_Y)
		self.l_d_y.extend(long_Y)
		s_d_bow_X.extend(short_bow)
		l_d_bow_X.extend(long_bow)
		self.s_d_ID.extend(short_bow)
		self.l_d_ID.extend(long_bow)


		if self.verbose:
			print "Created dev/editor pick vectors"

		#Dev, non-editor
		short_X, short_bow, short_Y, short_IDS, long_X, long_bow, long_Y, long_IDS = self.featureDictSplitClassifier(
			self.devSelectQueryNonEditorPick, self.trainCutoffNum * (1-self.proportionEditorPicksDev), splitOn)
		self.s_d_x.extend(short_X)
		self.l_d_x.extend(long_X)
		self.s_d_y.extend(short_Y)
		self.l_d_y.extend(long_Y)
		s_d_bow_X.extend(short_bow)
		l_d_bow_X.extend(long_bow)
		self.s_d_ID.extend(short_bow)
		self.l_d_ID.extend(long_bow)

		if self.verbose:
			print "Created dev/non-editor pick vectors"

		#Return train and dev bag of words representations
		return s_t_bow_X, l_t_bow_X, s_d_bow_X, l_d_bow_X

################ Cleaning up feature vectors: ###############


	#Method: calcPCA
	#Perform PCA feature selection on train and dev x data
	def calcPCA(self):
		#Normalize data vectors:
		self.t_x = (self.t_x - np.mean(self.t_x, 0)) / np.std(self.t_x, 0)
		self.d_x = (self.d_x - np.mean(self.d_x, 0)) / np.std(self.d_x, 0)

		#Fit on train
		
	def recursiveFeatureElimination(self):
		print "Starting RFE..."
		eliminator = RFE(self.classifier, 10, verbose=True)
		eliminator.fit(self.t_x, self.t_y)
		
		self.t_x = eliminator.transform(self.t_x)
		self.d_x = eliminator.transform(self.d_x)


################ Model Selection: ###########################

	#Method: bagOfWords
	#Classification using bag of words model
	#Note that this does not take into account the article text
	def bagOfWordsModel(self, tfidf=True):
		self.getCommentsBagOfWords(self.t_x, self.d_x)
		#Choose which vectorizing schematic to use:
		if tfidf:
			print "Creating features using tf-idf..."
			#Vectorize using TF-IDF scheme:
			self.vectorizer = fe.text.TfidfVectorizer(stop_words='english') #Set binary to true for rough estim
		else:
			print "Creating features using non-normalized bag of words..."
			#Use a standard count-vectorizer model
			self.vectorizer = fe.text.CountVectorizer()

		self.vectorizer.fit(self.t_x + self.d_x)
		self.t_x = self.vectorizer.transform(self.t_x)
		self.d_x = self.vectorizer.transform(self.d_x)

		if self.verbose:
			print "Vectorized bag of words."


	#Method: extractCommentFeatures
	#Populates self.t_x and self.d_x with features from database, without pullijg
	#any of the text associated with the comment.
	def featureModel(self):
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


	#Method: featuresAndCommentWordsModel
	#A model based on extracted features, running bag of words on the comments.
	def featuresAndCommentWordsModel(self, tfidf=True, maxNgram=1):

		bow_t_x, bow_d_x = self.getCommentFeatures()

		ngram_size = (1, maxNgram)

		#Vectorize and transform BOW features:
		if tfidf:
			self.BOWvectorizer = fe.text.TfidfVectorizer(stop_words='english', strip_accents='unicode', ngram_range=ngram_size)
		else:
			self.BOWvectorizer = fe.text.DictVectorizer()
		self.BOWvectorizer.fit(bow_t_x + bow_d_x)
		bow_t_x = self.BOWvectorizer.transform(bow_t_x)
		bow_d_x = self.BOWvectorizer.transform(bow_d_x)

		#Vectorize and transform extracted features:
		self.vectorizer = fe.DictVectorizer()
		self.vectorizer.fit(self.t_x + self.d_x)
		self.t_x = self.vectorizer.transform(self.t_x)
		self.d_x = self.vectorizer.transform(self.d_x)

		#Concatenate BOW and extracted features:
		self.t_x = sps.hstack([self.t_x, bow_t_x])
		self.d_x = sps.hstack([self.d_x, bow_d_x])

	#Method: splitClassifierModel
	#Model which runs two classifiers
	def splitClassifierModel(self, tfidf=True, maxNgram=1, splitOn=20):
		s_t_bow_X, l_t_bow_X, s_d_bow_X, l_d_bow_X = self.getCommentsSplitClassifier(splitOn)
		ngram_size = (1, maxNgram)

		if tfidf:
			self.BOWvectorizer = fe.text.TfidfVectorizer(stop_words='english', strip_accents='unicode', ngram_range=ngram_size)
		else:
			self.BOWvectorizer = fe.text.DictVectorizer()
		self.BOWvectorizer.fit(s_t_bow_X + l_t_bow_X + s_d_bow_X + l_d_bow_X)
		s_t_bow_X = self.BOWvectorizer.transform(s_t_bow_X)
		l_t_bow_X = self.BOWvectorizer.transform(l_t_bow_X)
		s_d_bow_X = self.BOWvectorizer.transform(s_d_bow_X)
		l_d_bow_X = self.BOWvectorizer.transform(l_d_bow_X)

		self.vectorizer = fe.DictVectorizer()
		self.vectorizer.fit(self.s_t_x + self.l_t_x + self.s_d_x + self.l_d_x)
		self.s_t_x = self.vectorizer.transform(self.s_t_x)
		self.l_t_x = self.vectorizer.transform(self.l_t_x)
		self.s_d_x = self.vectorizer.transform(self.s_d_x)
		self.l_d_x = self.vectorizer.transform(self.l_d_x)

		self.s_t_x = sps.hstack([self.s_t_x, s_t_bow_X])
		self.l_t_x = sps.hstack([self.l_t_x, l_t_bow_X])
		self.s_d_x = sps.hstack([self.s_d_x, s_d_bow_X])
		self.l_d_x = sps.hstack([self.l_d_x, l_d_bow_X])


###########Set classifier type + parameters: ############################


	#Method: setLinearSVM
	#Sets classifier to be very basic linear SVM
	def setLinearSVM(self, C_val=.1, penalty='l2', dual=True):
		self.classifier = svm.LinearSVC(C=C_val, penalty=penalty, dual=dual)
		print "Using linear SVM with C=%.3f" % C_val

	#Method: setSGD
	#Set classifier to be SGD, with default settings
	def setSGD(self):
		self.classifier = linear_model.SGDClassifier(loss="log")
		print "Using SGD classifier"

	#Method: setKernalSVM
	#Set self.classifier to be SVM with kernel as specified
	def setKernelSVM(self, kernel='rbf'):
		#Check defaults: http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
		self.classifier = svm.SVC(kernel = kernel) 
		print "Using ", kernel, " Kernel for SVM"

	#Method: setRandomForest
	#NOTE: this has not been debugged yet; it wants dense data representation,
	#not our CSR sparse matrices
	def setRandomForest(self):
		self.classifier = RandomForestClassifier()
		print "Using random forest classifier"

	#Method: useCVSearch
	#Leverage sklearn's GridSearch platform to customize parameters for
	#an SVC. Note that a consequence of calling this method is setting self.classifier
	#to be the SVC with found parameters.
	def useCVSearch(self):
		print "Starting CV Grid Search"
		#This many params takes a long time
		param_grid = [ {'C': [.01, .1, 1, 10], 'kernel': ['poly', 'linear', 'rbf'], 'gamma': [1e-4, 1e-3, 1e-2, 0.1]} ]
		#See scoring : http://scikit-learn.org/stable/modules/model_evaluation.html
		clf = sklearn.grid_search.GridSearchCV(self.classifier, param_grid, scoring='f1')
		clf.fit(self.t_x, self.t_y)
		params = clf.best_params_
		#self.classifier = self.classifier(C=params['C'], kernel=params['kernel'], gamma=params['gamma'])
		#Definitely works as below, not sure if above is correct syntax ^^
		self.classifier = svm.SVC(C=params['C'], kernel=params['kernel'], gamma=params['gamma'])

	#Method: useNeuralNetwork
	#This method will train and run a shallow neural network.
	#NOTE: Pipeline syntax copied directly from:
	#http://scikit-learn.org/stable/auto_examples/neural_networks/plot_rbm_logistic_classification.html#example-neural-networks-plot-rbm-logistic-classification-py
	def useNeuralNetwork(self):
		#Set up logistic regression unit:
		logistic = linear_model.LogisticRegression()
		#Set up neural net unit; tune its parameters ##TODO: grid search for params
		rbm = BernoulliRBM(random_state=0, verbose=True)
		rbm.learning_rate = 0.06
		rbm.n_iter = 20
		rbm.n_components = 50
		#Make classifier a pipeline
		self.classifier = Pipeline(steps=[('rbm', rbm), ('logistic', logistic)])

	#Method: useTwoClassifiers
	#Use 2 classifiers splitting on review length. Note that in order to use this classification
	#scheme you must have called "splitClassifierModel"
	def useTwoClassifiers(self):
		self.classifier1 = svm.LinearSVC(C=.5)
		self.classifier2 = svm.LinearSVC(C=.5)


###########Classification step: ##########################################

	def useEnsemble(self):
		print "Starting Ensemble"

		print "Classifying with LinearSVM"
		self.classifier = svm.LinearSVC(C=.5, dual=False)#, class_weight="auto")
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_1 = self.classifier.predict(self.t_x)
		predict_dev_1 = self.classifier.predict(self.d_x)

		print "Classifying with a Random Forest"
		#self.classifier = svm.SVC(C=.5)
		self.classifier = RandomForestClassifier()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_2 = self.classifier.predict(self.t_x)
		predict_dev_2 = self.classifier.predict(self.d_x)

		print "Classifying with SGD"
		self.classifier = linear_model.SGDClassifier(loss="log")
		#self.classifier = RandomForestClassifier()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_3 = self.classifier.predict(self.t_x)
		predict_dev_3 = self.classifier.predict(self.d_x)

		print "Creating Ensemble"
		#Dividing by 2 has the effect of selecting the majority
		train_sum_predict = predict_train_1 + predict_train_2 + predict_train_3
		dev_sum_predict = predict_dev_1 + predict_dev_2 + predict_dev_3

		print "number of positives predicted when dividing by 2 = ", np.sum(dev_sum_predict / 2)
		print "number of positives predicted when dividing by 3 = ", np.sum(dev_sum_predict / 3)

		predict_train = train_sum_predict / 2
		predict_dev = dev_sum_predict / 2


		print "Classified %d samples, using %d features" % self.t_x.shape
		print "Training accuracy:"
		t_acc = self.f1_accuracy(predict_train, self.t_y)
		self.p_r_f_s(self.t_y, predict_train)
		
		print "Classification report:"
		self.classification_report(predict_train, self.t_y)
		print "Dev accuracy:"
		d_acc = self.f1_accuracy(predict_dev, self.d_y)
		self.p_r_f_s(self.d_y, predict_dev)
		
		print "Classification report:"
		self.classification_report(predict_dev, self.d_y)

		#Save results to CSV
		self.save_results(t_acc, d_acc, ensemble=True)

	#Method: classify
	#Run the classifier specified under self.classifier on the train and
	#dev data. Report the analysis.
	def classify(self):
		#Fit classifier, then classify train and dev examples
		print "Starting classifier..."
		if self.verbose:
			print "Classifying based on features:"
			print self.vectorizer.get_feature_names()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train = self.classifier.predict(self.t_x)
		predict_dev = self.classifier.predict(self.d_x)

		#Report F1 statistics
		print "Classified %d samples, using %d features" % self.t_x.shape
		print "Training accuracy:"
		t_acc = self.f1_accuracy(predict_train, self.t_y)
		self.p_r_f_s(self.t_y, predict_train)

		print "Classification report:"
		self.classification_report(predict_train, self.t_y)
		print "Dev accuracy:"
		d_acc = self.f1_accuracy(predict_dev, self.d_y)
		self.p_r_f_s(self.d_y, predict_dev)
		
		print "Classification report:"
		self.classification_report(predict_dev, self.d_y)

		#Save results to CSV
		self.save_results(t_acc, d_acc)

	def useEnsemble(self):
		print "Starting Ensemble"
		print "Classifying with LinearSVM"
		self.classifier = svm.LinearSVC(C=.5, dual=False)#, class_weight="auto")
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_1 = self.classifier.predict(self.t_x)
		predict_dev_1 = self.classifier.predict(self.d_x)

		print "Classifying with SVM + PolyKernel"
		self.classifier = svm.SVC(C=.5)
		#self.classifier = RandomForestClassifier()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_2 = self.classifier.predict(self.t_x)
		predict_dev_2 = self.classifier.predict(self.d_x)

		print "Classifying with SGD"
		self.classifier = linear_model.SGDClassifier()
		#self.classifier = RandomForestClassifier()
		self.classifier.fit(self.t_x, self.t_y)
		predict_train_3 = self.classifier.predict(self.t_x)
		predict_dev_3 = self.classifier.predict(self.d_x)

		print "Creating Ensemble"
		#Dividing by 2 has the effect of selecting the majority
		predict_train = (predict_train_1 + predict_train_2 + predict_train_3) / 2
		predict_dev = (predict_dev_1 + predict_dev_2 + predict_dev_3) / 2
		print "Classified %d samples, using %d features" % self.t_x.shape
		print "Training accuracy:"
		t_acc = self.f1_accuracy(predict_train, self.t_y)
		self.p_r_f_s(self.t_y, predict_train)
		
		print "Classification report:"
		self.classification_report(predict_train, self.t_y)
		print "Dev accuracy:"
		d_acc = self.f1_accuracy(predict_dev, self.d_y)
		self.p_r_f_s(self.d_y, predict_dev)
		
		print "Classification report:"
		self.classification_report(predict_dev, self.d_y)
		#Save results to CSV
		self.save_results(t_acc, d_acc, ensemble=True)

	def classifyOnSplit(self):
		print "Starting dual classifiers..."
		self.classifier1.fit(self.s_t_x, self.s_t_y)
		self.classifier2.fit(self.l_t_x, self.l_t_y)

		short_predict_train = self.classifier1.predict(self.s_t_x)
		long_predict_train = self.classifier2.predict(self.l_t_x)
		short_predict_dev = self.classifier1.predict(self.s_d_x)
		long_predict_dev = self.classifier2.predict(self.l_d_x)

		print "Short train:"
		self.classification_report(self.s_t_y, short_predict_train)
		print "Short dev:"
		self.classification_report(self.s_d_y, short_predict_dev)
		print "Long train:"
		self.classification_report(self.l_t_y, long_predict_train)
		print "Long dev:"
		self.classification_report(self.l_d_y, long_predict_dev)

	#Method: makeNamesList
	#Returns the names associated with features at given index in the
	#classifier's attributes matrix.
	def makeNamesList(self):
		feature_names = []
		feature_names.extend(self.vectorizer.get_feature_names())
		if self.BOWvectorizer != None:
			feature_names.extend(self.BOWvectorizer.get_feature_names())
		return feature_names

	#Method: topNCoefficients
	#This method will record the top N coefficients used during the classifier
	#step.
	def topNCoefficients(self, numToPrint):
		weights = self.classifier.coef_.tolist()
		numTop = numToPrint
		names = self.makeNamesList()
		if len(names) < numTop:
		    numTop = len(names)
		tops = heapq.nlargest(numTop, enumerate(weights[0]), key=lambda x: abs(x[1])) #Use absolute magnitude of weight as key
		for item in tops:
		    print "Item " + names[item[0]].encode('utf-8') + " has weight " + str(item[1])

    #Method: classifyKValidation
    #Run a given classifier k times, returns an average of its outputs for 6 categories:
    #train & dev precision, recall, and f1. Prints these quantities out, as well as variance.
	def classifyKValidation(self, k=3, verbose=False):
		accuracies = np.zeros((k, 6))
		for i in range(k):
			self.classifier.fit(self.t_x, self.t_y)
			predict_train = self.classifier.predict(self.t_x)
			predict_dev = self.classifier.predict(self.d_x)

			if verbose:
				print "Train:"
				print me.classification_report(self.t_y, predict_train)
				print "Dev:"
				print me.classification_report(self.d_y, predict_dev)

			p, r, f, s = me.precision_recall_fscore_support(self.t_y, predict_train, average='micro')
			accuracies[i][0] = p
			accuracies[i][1] = r
			accuracies[i][2] = f
			p, r, f, s = me.precision_recall_fscore_support(self.d_y, predict_dev, average='micro')
			accuracies[i][3] = p
			accuracies[i][4] = r
			accuracies[i][5] = f

		avg_accuracies = np.mean(accuracies, axis=0)
		print "Average train precision=%.3f, recall=%.3f, F1=%.3f \n Average dev precision=%.3f, recall=%.3f, F1=%.3f" % (avg_accuracies[0], avg_accuracies[1], avg_accuracies[2], avg_accuracies[3], avg_accuracies[4], avg_accuracies[5])
		std_variance = np.std(accuracies, axis=0)
		print "Variance looked like:"
		print std_variance
		    

##########Accuracy and Results: ##########################################

	def classification_report(self, predicted, real):
		print 'Number of 1s in gold is {} out of {}'.format(np.sum(real), len(real))

		print 'Number of 1s predicted is {} out of {}'.format(np.sum(predicted), len(predicted))
		print me.classification_report(real, predicted)

	def f1_accuracy(self, predicted_vals, real_vals):
		accuracy = me.f1_score(real_vals, predicted_vals)
		print "F1 accuracy is %.3f" % accuracy
		return accuracy

	def p_r_f_s(self, real_vals, predicted_vals):
		p, r, f, s = me.precision_recall_fscore_support(real_vals, predicted_vals)
		print "Precision = %.3f, recall = %.3f, f1 = %.3f, support = %.3f" %(p[0], r[0], f[0], s[0])
		return p, r, f, s 

	def visualize_tsne(self):
		print "Preparing TSNE visualization..."
		#X_array = self.t_x.toarray()
		tsne_model = TSNE()
		tsne_x = tsne_model.fit_transform(self.t_x)
		print "Tsne shape:"
		print tsne_x.shape
		colors = []
		for y in self.t_y:
			if y == 1:
				colors.append('r')
			else: colors.append('g')
		plt.scatter(tsne_x[:, 0], tsne_x[:, 1], c=colors)
		plt.show()


	def visualize_2_features(self, feature1, feature2):
		pass

	def save_results(self, train, dev):
		if self.save_file == "afs":
			self.save_file = "/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/results.csv"
		with open(self.save_file, 'a') as results_file:
			num_total = self.trainCutoffNum
			num_1s = num_total * self.proportionEditorPicksTrain

			if ensemble :
				results_file.write("**Results from Ensemble Model**\n")
			results_file.write(time.strftime("%Y-%m-%d %H:%M") + "\n")
			results_file.write("Number of 1s : " + str(num_1s) + " out of " + str(num_total) + "\n")
			results_file.write("---------------------\n")
			results_file.write("| f1_train | f1_dev  |\n")
			results_file.write("| " + str(round(train, 5)) + "  | " + str(round(dev, 5)) + " |\n")
			results_file.write("---------------------\n")

			results_file.write("Features = " + (',').join(self.vectorizer.get_feature_names()) + "\n")
			results_file.write("Classifier = ")
			results_file.write(str(self.classifier) + '\n\n')

	#Method: viewMisclassifiedReviews
	#A method that will print out reviews that were misclassified.
	def viewMisclassifiedReviews(self, numToShow=10, allFromDev=True, showFalseNegs=True, showFalsePos=True, article_url=None):
		#View mislcassified reviews:
		predictions_dev = self.classifier.predict(self.d_x)
		false_pos = 0
		false_neg = 0
		if article_url != None :
			print "The Article URL is: ", article_url
			ids_by_article = self.c.execute("SELECT CommentID FROM Comments WHERE ArticleURL = ?", (article_url,)).fetchall()
			ids_by_article = [ids[0] for ids in ids_by_article]
		else :
			ids_by_article = [x for x in range(5e7, 1e8)]
		for i in range(len(predictions_dev)):
			prediction = predictions_dev[i]
			gold = self.d_y[i]
			c_id = self.d_IDs[i]
			if showFalseNegs and false_neg < numToShow and c_id in ids_by_article:
				if prediction == 1 and gold == 0 :
					print "Comment %d misclassified. False Positive" % (c_id)
					text = self.c.execute("SELECT CommentText FROM Comments WHERE CommentID = ?", (c_id,)).fetchone()
					print text
					print "\n"
					false_neg += 1
			if showFalsePos and false_pos < numToShow  and c_id in ids_by_article:
				if prediction == 0 and gold == 1:
					print "Comment %d misclassified . False Negative" % (c_id)
					text = self.c.execute("SELECT CommentText FROM Comments WHERE CommentID = ?", (c_id,)).fetchone()
					print text
					print "\n"
					false_pos += 1
			if false_neg + false_pos > 2 * numToShow: break
		print "Number of False Positives: ", false_pos
		print "Number of False Negatives: ", false_neg



	def viewYesClassifiedReviews(self, numToShow=10, allFromDev=True, showTrueNegs=True, showTruePos=True, article_url=None):
		#View mislcassified reviews:
		predictions_dev = self.classifier.predict(self.d_x)
		true_pos = 0
		true_neg = 0
		if article_url != None :
			print "The Article URL is: ", article_url
			ids_by_article = self.c.execute("SELECT CommentID FROM Comments WHERE ArticleURL = ?", (article_url,)).fetchall()
			ids_by_article = [ids[0] for ids in ids_by_article]
		else :
			ids_by_article = [x for x in range(5e7, 1e8)]
		for i in range(len(predictions_dev)):
			prediction = predictions_dev[i]
			gold = self.d_y[i]
			c_id = self.d_IDs[i]
			if showTrueNegs and true_neg < numToShow and c_id in ids_by_article:
				if prediction == 0 and prediction == 0:
					print "Comment %d classified correctly: True Negative" % (c_id)
					text = self.c.execute("SELECT CommentText FROM Comments WHERE CommentID = ?", (c_id,)).fetchone()
					print text
					print "\n"
					true_neg += 1
			if showTruePos and true_pos < numToShow and c_id in ids_by_article:
				if prediction == 1 and prediction == 1:
					c_id = self.d_IDs[i]
					print "Comment %d classified correctly: True Positive" % (c_id)
					text = self.c.execute("SELECT CommentText FROM Comments WHERE CommentID = ?", (c_id,)).fetchone()
					print text
					print "\n"
					true_pos += 1
			if true_neg + true_pos > 2 * numToShow: break
		print "Number of True Positives: ", true_pos
		print "Number of True Negatives: ", true_neg












