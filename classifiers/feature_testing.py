from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.*, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, c.CommentText, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
KLD_query = "SELECT KLDistance, KLDistance_Nouns FROM Features f, Comments c WHERE KLDistance IS NOT NULL AND c.CommentID = f.CommentID "
subj_query = "SELECT subjectivity, polarity, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
jaccard_query = "SELECT Jaccard, EditorSelection FROM Features c WHERE CommentID > 1 "
nltk_query = "SELECT f.*, c.TrainTest, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
basic_af = "SELECT * FROM Comments c WHERE CommentID > 1"
n_chars = "SELECT Jaccard, n_sentences, avg_word_len, n_questions, EditorSelection FROM Features c "
basic_af = "SELECT * FROM Features "
overlap_features = "SELECT skipgrams_2, skipgrams_3, Jaccard, Cosine, n_chars, n_words, n_upper, subjectivity, EditorSelection FROM Features "
everything_for_bow = "SELECT f.*, c.CommentText FROM Comments c, Features f, Articles a WHERE c.CommentID = f.CommentID AND c.ArticleURL = a.URL AND a.Section = 'World' "
nn_features = "SELECT num_1_letter_words, skipgrams_3, n_sentences, EditorSelection FROM Features"
baseline = "SELECT c.CommentText, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
baseline_orig = "SELECT n_chars, n_words, n_periods, n_questions, n_exclamations, n_upper, avg_word_len, n_sentences, avg_sentence_len, words_per_sentence, EditorSelection FROM Features "
just_jaccard = "SELECT Jaccard, n_chars, EditorSelection From Features"
##############Initialize features model:
cf = CommentFeatures("../john_test_5.db")


##############Set cutoff on review count, verbosity, features query:
cf.limitNumComments(60000, 16000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(baseline)
cf.zeroBlankColumns()
#cf.preprocessText()
#cf.setResultsFile("results.csv") ##JOHN-- pulled this out of "classify"


#Query the database to make feature vectors/clean data:
##############Query the database to make feature vectors/clean data:
#cf.featureModel()
cf.featuresAndCommentWordsModel(maxNgram=1)
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()


##############Choose classifier: (Choose ONE)
#cf.setSGD()
#cf.setLinearSVM(C_val=.5)
#cf.setKernelSVM("poly")
#cf.useCVSearch()
#cf.setRandomForest()
#cf.useNeuralNetwork() #Recommend: low # features


##############Perform the classification step, show metrics:
cf.useEnsemble()
#cf.classify()
#cf.visualize_tsne()
#Can only use this with a Linear Kernel
cf.topNCoefficients(1) #Check to see which coefficients are assigned highest classification weight

#cf.viewMisclassifiedReviews(article_url="http://www.nytimes.com/2013/04/18/us/politics/senate-obama-gun-control.html")
#cf.viewYesClassifiedReviews(article_url="http://www.nytimes.com/2013/04/18/us/politics/senate-obama-gun-control.html")

#cf.viewMisclassifiedReviews(article_url="http://www.nytimes.com/2015/04/08/us/south-carolina-officer-is-charged-with-murder-in-black-mans-death.html")
#cf.viewYesClassifiedReviews(article_url="http://www.nytimes.com/2015/04/08/us/south-carolina-officer-is-charged-with-murder-in-black-mans-death.html")

##############Close up the database, cursors, etc
cf.close()

