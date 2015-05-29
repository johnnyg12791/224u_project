
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe
import sklearn.metrics as me
from sklearn import svm
from sklearn import linear_model
from sklearn.decomposition import PCA 
import csv
import scipy.sparse as sps 
from matplotlib.mlab import PCA as mlabPCA
import heapq



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

		#User should provide a featureSelectQuery 
		self.featureSelectionQuery = None
		self.goldQuery = "SELECT EditorSelection FROM Comments WHERE CommentID = (?)"       

		#Number of reviews to terminate at; useful for debugging
		self.num_comments = float("inf")
		self.numInTrain = 0
		self.numInDev = 0
		self.proportionEditorPicks = .5 #Artificially grab more editor pick reviews
		#Feature vectors x and "editor results" y for train and dev:
		#(not even going to touch test-- let's leave it clean!)
		#Train:
		self.t_x = []
		self.t_y = []
		#Dev:
		self.d_x = []
		self.d_y = []

		self.BOWvectorizer = None #A standin for "using bag of words"

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
		self.trainCutoffNum = upperLimit

	#Set verbose; note that right now this is 80% debugging output
	def setVerbose(self, verbose=True):
		self.verbose = verbose 

	#Set the artificial number of editor picks to be "proportion"
	def setEditorPicksProportion(self, proportion):
		self.proportionEditorPicks = proportion

#########Raw feature vector creation: ######################################

	#Method: createSelectStatments
	#A method which will create custom select statements from the user-entered version for
	#editor pick and non-editor pick train and dev data.
	def createSelectStatements(self, statement):
		self.trainSelectQueryEditorPick =  statement + " AND c.TrainTest =1 AND c.EditorSelection = 1"
		self.trainSelectQueryNonEditorPick = statement + " AND c.TrainTest =1 AND c.EditorSelection = 0"
		self.devSelectQueryEditorPick = statement + " AND c.TrainTest =2 AND c.EditorSelection = 1"
		self.devSelectQueryNonEditorPick = statement + " AND c.TrainTest =2 AND c.EditorSelection = 0"

	#Method: createSelectStatments
	#A method which will create custom select statements from the user-entered version for
	#editor pick and non-editor pick train and dev data.
	def createSelectStatementsNew(self, statement):
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
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
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
			if num_grabbed > self.trainCutoffNum * self.proportionEditorPicks: break
		#Add 75% non-editor picks
		for cID, cText, gold in self.c.execute (self.devSelectQueryNonEditorPick):
			d_x.append(cText)
			self.d_y.append(gold)
			if returnCommentIDs: d_commentIDs.append(cID)
			num_grabbed +=1
			if num_grabbed > self.trainCutoffNum: break

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
		num_comments = 0
		for row in self.c.execute(query):
			feature_dict = {}
			blanks_flag = 0
			for i, col in enumerate(self.c.description):
				val = row[i]
				if val == None: ##TODO: Remove once no longer adding null features
					val = 0
					#blanks_flag = 1 #Hackey way to screen out "incompletely featured" comments
				#Append EditorSelection to golds:
				if col[0] == "EditorSelection":
					gold = row[i]
				elif col[0] == "CommentText":
					bow_X.append(val)
				elif col[0] == "CommentID" or col[0] == "TrainTest":
					continue
				#Add columns to features:
				else:
					feature_dict[col[0]] = val

			if vectorizeBOW:
				#Precondition: must have selected CommentText
				commentText = feature_dict["CommentText"]

			if blanks_flag == 0:
				X.append(feature_dict)
				Y.append(gold)
			#Check cutoff:
			num_comments += 1
			if num_comments > cutoff: break 
		return (X, Y, bow_X)


	#Method: getCommentFeatures
	#This method will set self.t_x and self.d_x to be vectors of comment features, and
	#t_y and d_y to be the gold labels. Note that this relies on passing the model a
	#feature selection query, and must have first thing you request be comment ID.
	def getCommentFeatures(self):
		self.createSelectStatements(self.featureSelectionQuery)

		#Train and dev bag of words representations
		t_bow_X = []
		d_bow_X = []

		#Train, editor
		train_editorX, Y, bX = self.makeFeatureDict(
			self.trainSelectQueryEditorPick, self.trainCutoffNum * self.proportionEditorPicks)
		self.t_x.extend(train_editorX)
		self.t_y.extend(Y)
		t_bow_X.extend(bX)

		if self.verbose:
			print "Created training/editor pick vectors"

		#Train, non-editor
		train_noneditorX, Y, bX = self.makeFeatureDict(
			self.trainSelectQueryNonEditorPick, self.trainCutoffNum * (1-self.proportionEditorPicks))
		self.t_x.extend(train_noneditorX)
		self.t_y.extend(Y)
		t_bow_X.extend(bX)


		if self.verbose:
			print "Created training/non-editor pick vectors"

		#Dev, editor
		dev_editorX, Y, bX = self.makeFeatureDict(
			self.devSelectQueryEditorPick, self.trainCutoffNum * self.proportionEditorPicks)
		self.d_x.extend(dev_editorX)
		self.d_y.extend(Y)
		d_bow_X.extend(bX)


		if self.verbose:
			print "Created dev/editor pick vectors"

		#Dev, non-editor
		dev_noneditorX, Y, bX = self.makeFeatureDict(
			self.devSelectQueryNonEditorPick, self.trainCutoffNum * (1-self.proportionEditorPicks))
		self.d_x.extend(dev_noneditorX)
		self.d_y.extend(Y)
		d_bow_X.extend(bX)

		if self.verbose:
			print "Created dev/non-editor pick vectors"

		#Return train and dev bag of words representations
		return t_bow_X, d_bow_X

################ Cleaning up feature vectors: ###############


	#Method: calcPCA
	#Perform PCA feature selection on train and dev x data
	def calcPCA(self):
		#Normalize data vectors:
		self.t_x = (self.t_x - np.mean(self.t_x, 0)) / np.std(self.t_x, 0)
		self.d_x = (self.d_x - np.mean(self.d_x, 0)) / np.std(self.d_x, 0)

		#Fit on train
		


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
	def featuresAndCommentWordsModel(self, tfidf=True):

		bow_t_x, bow_d_x = self.getCommentFeatures()

		#Vectorize and transform BOW features:
		self.BOWvectorizer = fe.text.TfidfVectorizer(stop_words='english')
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

		if self.verbose:
			print "Training vector looks like:"
			print self.t_x 

	#Method: featuresAndCommentWordsModel
	#A feature model based on extracted features + BOW on the comments.
	def featuresAndCommentWordsModel_slow(self, tfidf=True):
		#Get bag of words from comments:
		bow_t_x = []
		bow_d_x = []
		t_IDs, d_IDs = self.getCommentsBagOfWords(t_x=bow_t_x, d_x=bow_d_x, returnCommentIDs=True)

		#Vectorize and transform BOW features:
		self.BOWvectorizer = fe.text.TfidfVectorizer(stop_words='english')
		self.BOWvectorizer.fit(bow_t_x + bow_d_x)
		bow_t_x = self.BOWvectorizer.transform(bow_t_x)
		bow_d_x = self.BOWvectorizer.transform(bow_d_x)

		if self.verbose:
			print "Extracted and vectorized BOW features..."

		#Get extra features, using list found in BOW task:
		feat_t_x = []
		feat_d_x = []
		for c_id in t_IDs:
			feat_t_x.append(self.getFeatureRow(self.featureSelectionQuery, c_id))
		for c_id in d_IDs:
			feat_d_x.append(self.getFeatureRow(self.featureSelectionQuery, c_id))


		#Vectorize the extra features; store in self.t_x and self.d_x
		self.vectorizer = fe.DictVectorizer()
		self.vectorizer.fit(feat_t_x + feat_d_x)
		self.t_x = self.vectorizer.transform(feat_t_x)
		self.d_x = self.vectorizer.transform(feat_d_x)

		if self.verbose:
			print "Extracted and vectorized extra features..."

		#Stack them together:
		self.t_x = sps.hstack([self_t_x, bow_t_x])
		self.d_x = sps.hstack([self.d_x, bow_d_x])


###########Set classifier type + parameters: ############################

	#Method: setLinearSVM
	#Sets classifier to be very basic linear SVM
	def setLinearSVM(self, C_val=1):
		self.classifier = svm.LinearSVC(C=C_val)
		print "Using linear SVM with C=%.f" % C_val

	def setSGD(self):
		self.classifier = linear_model.SGDClassifier()
		print "Using SGD classifier"


###########Classification step: ##########################################

	#Method: classify
	#Run the classifier specified under self.classifier on the train and
	#dev data. Report the analysis.
	def classify(self, save_file="afs"):
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
		self.save_results(t_acc, d_acc, save_file)

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


	def save_results(self, train, dev, save_file):
		if save_file == "afs":
			save_file = "/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/results.csv"
		with open(save_file, 'a') as results_file:
			fields = ['f1_train', 'f1_dev', 'num_samples', 'num_features', 'classifier_type']
			writer = csv.DictWriter(results_file, fieldnames=fields)
			n_samples, n_features = self.t_x.shape
			writer.writerow({'f1_train': train, 'f1_dev': dev, 
    			'num_samples': n_samples, 'num_features': n_features, 'classifier_type': self.classifier})















