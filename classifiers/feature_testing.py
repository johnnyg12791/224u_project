from CommentFeatures import CommentFeatures
 
all_query = "SELECT f.*, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, c.CommentText, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
KLD_query = "SELECT KLDistance, KLDistance_Nouns FROM Features f, Comments c WHERE KLDistance IS NOT NULL AND c.CommentID = f.CommentID "
subj_query = "SELECT subjectivity, polarity, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
jaccard_query = "SELECT Jaccard, EditorSelection FROM Features c WHERE CommentID > 1 "
nltk_query = "SELECT f.*, c.TrainTest, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
basic_af = "SELECT * FROM Comments c WHERE CommentID > 1"
n_chars = "SELECT Jaccard, n_sentences, avg_word_len, n_questions, EditorSelection FROM Features c "
n_chars = "SELECT Agree, PhD, Jaccard, n_chars, c.EditorSelection, c.CommentID, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
basic_af = "SELECT * FROM Features "
overlap_features = "SELECT CommentText, skipgrams_2, skipgrams_3, Jaccard, Cosine, n_chars, n_words, n_upper, subjectivity, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
everything_for_bow = "SELECT f.*, c.CommentText FROM Comments c, Features f, Articles a WHERE c.CommentID = f.CommentID AND c.ArticleURL = a.URL AND a.Section = 'World' "
nn_features = "SELECT num_1_letter_words, skipgrams_3, n_sentences, EditorSelection FROM Features"

#'SELECT f.n_sentences, nltk.POS, FROM Features f, nltk_features nltk JOIN '
#Initialize features model:
poly_features = "SELECT KLDistance, KLDistance_Nouns, Jaccard, stem_jaccard, polarity, n_exclamations, Cosine, n_questions, n_words, perc_1_char_words, perc_2_5_letter_words, perc_6_9_letter_words, perc_10_14_letter_words, perc_15plus_letter_words, JJR, RP, UH, VBD, POS, EX, RBS, PDT, NNPS, FW, LS, skipgrams_3, skipgrams_2, CommentID, EditorSelection FROM Features "
poly_features_bow = "SELECT KLDistance, KLDistance_Nouns, Jaccard, polarity, n_exclamations, Cosine, n_questions, n_words, perc_1_char_words, perc_2_5_letter_words, perc_6_9_letter_words, perc_10_14_letter_words, perc_15plus_letter_words, JJR, RP, UH, VBD, POS, EX, RBS, PDT, NNPS, FW, LS, skipgrams_3, skipgrams_2, c.CommentID, c.EditorSelection, CommentText FROM Features f, Comments c, Articles a WHERE f.CommentID = c.CommentID AND a.Section = 'World' AND a.URL = c.ArticleURL "
nltk_feats = "SELECT WRB, JJR, RP, UH, VBD, POS, EX, RBS, PDT, NNPS, FW, LS, EditorSelection FROM Features "
one_feat = "SELECT Jaccard, c.CommentID, c.EditorSelection, c.CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
stem_jac_feat = "SELECT stem_jaccard, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
##############Initialize features model:
cf = CommentFeatures()


##############Set cutoff on review count, verbosity, features query:
cf.limitNumComments(50000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(basic_af)
cf.zeroBlankColumns()
#cf.preprocessText()
#cf.setResultsFile("results.csv") ##JOHN-- pulled this out of "classify"


##############Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.featuresAndCommentWordsModel(maxNgram=2)
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()
#cf.splitClassifierModel(splitOn=200)

##############Choose classifier: (Choose ONE)
#cf.setSGD()
cf.setLinearSVM(C_val=.5, penalty='l1', dual=False)
#cf.setKernelSVM("poly")
#cf.useCVSearch()
#cf.setRandomForest()
#cf.useNeuralNetwork() #Recommend: low # features
#cf.useTwoClassifiers()


##############Perform the classification step, show metrics:
#cf.classify()
cf.useEnsemble()
#cf.classifyOnSplit()

##############Visualization of results:
#cf.visualize_tsne()
#Can only use this with a Linear Kernel
#Note: to see topNCoefficients, must include CommentText and CommentID in select query
#cf.topNCoefficients(30) #Check to see which coefficients are assigned highest classification weight
#cf.viewMisclassifiedReviews()

##############Close up the database, cursors, etc
cf.close()

