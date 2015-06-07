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
baseline_orig = "SELECT n_chars, n_words, n_periods, n_questions, n_exclamations, n_upper, avg_word_len, n_sentences, avg_sentence_len, words_per_sentence, EditorSelection FROM Features "
just_jaccard = "SELECT Jaccard, n_chars, EditorSelection From Features"
baseline_features = "SELECT Jaccard, skipgrams_2, skipgrams_3, Cosine, avg_sentence_len, n_chars, c.CommentID, c.EditorSelection, CommentText FROM Features f, Comments c WHERE c.CommentID = f.CommentID "

#Feature set John used for his high af accuracy
baseline = "SELECT c.CommentText, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.89      0.89      0.89     60002
#avg / total       0.76      0.76      0.76     16002

##All .58
baseline_sub_stemming = "SELECT c.CommentText, c.CommentID, f.stem_jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.89      0.89      0.89     60002
#avg / total       0.76      0.76      0.76     16002

##.59 ->
##.58 ->
baseline_plus_wordbuckets = "SELECT c.CommentText, num_1_letter_words, num_2_5_letter_words, num_6_9_letter_words, num_10_14_letter_words, num_15plus_letter_words, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#  0.89      0.89      0.89     60002
#  0.76      0.76      0.76 
baseline_plus_author = "SELECT c.CommentText, author_in_text, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#   0.81      0.74      0.72     60002
# 0.74      0.67      0.65     16002
baseline_plus_lengths = "SELECT c.CommentText, c.CommentID, f.Jaccard, avg_sentence_len, avg_word_len, n_chars, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.78      0.74      0.73     60002
#avg / total       0.72      0.69      0.67     16002

#avg / total       0.60      0.59      0.59     60002
#avg / total       0.60      0.59      0.59     16002

baseline_plus_sent = "SELECT c.CommentText, polarity, subjectivity, polarity_dif, subjectivity_dif, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.89      0.89      0.89     60002
#avg / total       0.76      0.76      0.76     16002

##All .59
baseline_plus_sent_dif = "SELECT c.CommentText, polarity_dif, subjectivity_dif, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.89      0.89      0.89     60002
#avg / total       0.76      0.76      0.76     16002

##avg / total       0.59      0.59      0.59     60002
##avg / total       0.58      0.58      0.58     16002

baseline_plus_KLD = "SELECT c.CommentText, KLDistance, KLDistance_Nouns, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
##All .58

baseline_plus_KLD_less_jacc = "SELECT c.CommentText, KLDistance, KLDistance_Nouns, c.CommentID, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
#avg / total       0.53      0.53      0.52     60002
#avg / total       0.53      0.53      0.52     16002


baseline_plus_punct = "SELECT c.CommentText, n_exclamations, n_periods, starts_with_I, n_upper, n_words, n_questions, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
##0.25      0.50      0.33     60002
##0.25      0.50      0.33     16002

nltk = "SELECT * FROM Features " ##Note: mark's db
#avg / total       0.62      0.53      0.42     60002
#avg / total       0.59      0.52      0.41     16002

baseline_plus_sent_sentences = "SELECT c.CommentText, polarity, subjectivity, polarity_dif, subjectivity_dif, first_sentence_jaccard, first_sentence_cosine, author_in_text, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
##All 59's

baseline_perc_words = "SELECT c.CommentText, perc_1_letter_words, perc_2_5_letter_words, perc_6_9_letter_words, perc_10_14_letter_words, perc_15plus_letter_words, c.CommentID, f.Jaccard, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "
##59-->
##58 -->

top_each_cl = "SELECT c.CommentText, perc_6_9_letter_words, subjectivity, KLDistance, avg_sentence_len, n_words, stem_jaccard, author_in_text, c.CommentID, f.EditorSelection FROM Features f, Comments c WHERE c.CommentID = f.CommentID "




##############Initialize features model:
cf = CommentFeatures()


##############Set cutoff on review count, verbosity, features query:
cf.limitNumComments(60000, 16000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(top_each_cl)
cf.zeroBlankColumns()
#cf.preprocessText()
#cf.setResultsFile("results.csv") ##JOHN-- pulled this out of "classify"

##############Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.featuresAndCommentWordsModel(maxNgram=1)
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()
#cf.splitClassifierModel(splitOn=200)

##############Choose classifier: (Choose ONE)
cf.setSGD()
#cf.setLinearSVM(C_val=.5)
#cf.setKernelSVM("poly")
#cf.useCVSearch()
#cf.setRandomForest()
#cf.useNeuralNetwork() #Recommend: low # features
#cf.useTwoClassifiers()


##############Perform the classification step, show metrics:
cf.useEnsemble()
#cf.classify()
#cf.visualize_tsne()
cf.topNCoefficients(10) #Check to see which coefficients are assigned highest classification weight

#cf.viewMisclassifiedReviews(article_url="http://www.nytimes.com/2013/04/18/us/politics/senate-obama-gun-control.html")

#cf.classifyOnSplit()
#cf.classifyKValidation(k=3, verbose=True)

##############Close up the database, cursors, etc
cf.close()

