from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.*, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, c.CommentText, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
KLD_query = "SELECT KLDistance, KLDistance_Nouns FROM Features f, Comments c WHERE KLDistance IS NOT NULL AND c.CommentID = f.CommentID "
subj_query = "SELECT subjectivity, polarity, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
jaccard_query = "SELECT Jaccard, EditorSelection FROM Features c WHERE CommentID > 1 "
nltk_query = "SELECT f.*, c.TrainTest, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
<<<<<<< HEAD
basic_af = "SELECT * FROM Comments c WHERE CommentID > 1"
n_chars = "SELECT Jaccard, n_sentences, avg_word_len, n_questions, EditorSelection FROM Features c "
=======
n_chars = "SELECT Agree, PhD, Jaccard, n_chars, EditorSelection FROM Features c "
>>>>>>> f8471c89672ab33345a6c74e9cf13ee0cbcf7b48
basic_af = "SELECT * FROM Features "
overlap_features = "SELECT skipgrams_2, skipgrams_3, Jaccard, Cosine, n_chars, n_words, n_upper, subjectivity, EditorSelection FROM Features "
everything_for_bow = "SELECT f.*, c.CommentText FROM Comments c, Features f, Articles a WHERE c.CommentID = f.CommentID AND c.ArticleURL = a.URL AND a.Section = 'World' "
nn_features = "SELECT num_1_letter_words, skipgrams_3, n_sentences, EditorSelection FROM Features"

##############Initialize features model:
cf = CommentFeatures()

<<<<<<< HEAD
#Set cutoff on review count, verbosity, features query:
cf.limitNumComments(100000) #50,000 samples will be our default "small" size
=======
##############Set cutoff on review count, verbosity, features query:
cf.limitNumComments(50000) #50,000 samples will be our default "small" size
>>>>>>> f8471c89672ab33345a6c74e9cf13ee0cbcf7b48
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(overlap_features)
cf.zeroBlankColumns()
#cf.preprocessText()
#cf.setResultsFile("results.csv") ##JOHN-- pulled this out of "classify"

<<<<<<< HEAD
#Choose classifier: (Choose ONE)
#cf.setLinearSVM()
#cf.setSGD()
#cf.setKernelSVM("rbf")
cf.setRandomForest()

#Query the database to make feature vectors/clean data:
=======
##############Query the database to make feature vectors/clean data:
>>>>>>> f8471c89672ab33345a6c74e9cf13ee0cbcf7b48
cf.featureModel()
#cf.featuresAndCommentWordsModel(maxNgram=2)
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()

<<<<<<< HEAD
#Perform the classification step, show metrics:
cf.classify("results.csv", cv_search=False)
=======
##############Choose classifier: (Choose ONE)
#<<<<<<< HEAD
#cf.setSGD()
cf.setLinearSVM(C_val=.5)
#cf.setKernelSVM("poly")
#cf.useCVSearch()
#>>>>>>> f951cfc8eebf6453ec71f914019c60cdbcc71c8a
#cf.setRandomForest()
#cf.useNeuralNetwork() #Recommend: low # features


##############Perform the classification step, show metrics:
cf.classify()
#cf.visualize_tsne()
>>>>>>> f8471c89672ab33345a6c74e9cf13ee0cbcf7b48
#Can only use this with a Linear Kernel
cf.topNCoefficients(30) #Check to see which coefficients are assigned highest classification weight
cf.viewMisclassifiedReviews()

##############Close up the database, cursors, etc
cf.close()

