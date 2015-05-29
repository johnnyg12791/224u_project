from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.*, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, c.CommentText, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
KLD_query = "SELECT KLDistance, KLDistance_Nouns FROM Features f, Comments c WHERE KLDistance IS NOT NULL AND c.CommentID = f.CommentID "
subj_query = "SELECT subjectivity, polarity, c.CommentID, c.EditorSelection, c.CommentText FROM Comments c, Features f WHERE c.CommentID = f.CommentID "
jaccard_query = "SELECT jaccard, EditorSelection FROM Features c WHERE CommentID > 1 "
nltk_query = "SELECT * FROM Features c WHERE CommentID > 1 "

#Initialize features model:
cf = CommentFeatures()

#Set cutoff on review count, verbosity, features query:
cf.limitNumComments(50000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(nltk_query)

#Choose classifier: (Choose ONE)
cf.setLinearSVM()
#cf.setSGD()

#Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.featuresAndCommentWordsModel()
#cf.bagOfWordsModel()
#cf.calcPCA()

#Perform the classification step, show metrics:
cf.classify()
cf.topNCoefficients(20) #Check to see which coefficients are assigned highest classification weight

#Close up the database, cursors, etc
cf.close()