from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.* FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"


cf = CommentFeatures()
cf.limitNumComments(300)
cf.setVerbose()
cf.setFeaturesQuery(all_query)
cf.setLinearSVM()
cf.featureModel()
cf.classify()
cf.close()