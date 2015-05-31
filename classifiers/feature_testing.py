from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.*, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, c.CommentText, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
KLD_query = "SELECT KLDistance, KLDistance_Nouns FROM Features f, Comments c WHERE KLDistance IS NOT NULL AND c.CommentID = f.CommentID "
subj_query = "SELECT subjectivity, polarity, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
jaccard_query = "SELECT Jaccard, EditorSelection FROM Features c WHERE CommentID > 1 "
nltk_query = "SELECT f.*, c.TrainTest, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
n_chars = "SELECT Agree, PhD, Jaccard, n_chars, EditorSelection FROM Features c "
basic_af = "SELECT * FROM Features "
overlap_features = "SELECT skipgrams_2, skipgrams_3, Jaccard, Cosine, n_chars, n_words, n_upper, subjectivity, EditorSelection FROM Features "

#Initialize features model:
cf = CommentFeatures()

#Set cutoff on review count, verbosity, features query:
cf.limitNumComments(15000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(overlap_features)
cf.zeroBlankColumns()

#Choose classifier: (Choose ONE)
#<<<<<<< HEAD
#cf.setSGD()
#cf.setLinearSVM()
cf.setKernelSVM("poly")
#>>>>>>> f951cfc8eebf6453ec71f914019c60cdbcc71c8a
#cf.setRandomForest()

#Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.featuresAndCommentWordsModel()
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()

#Perform the classification step, show metrics:
cf.classify("results.csv", cv_search=False)
#Can only use this with a Linear Kernel
cf.topNCoefficients(10) #Check to see which coefficients are assigned highest classification weight

#Close up the database, cursors, etc
cf.close()