__author__ = 'mark'
import pickle
import numpy as np
import os, sys
import sqlite3
import sklearn
import scipy
from operator import itemgetter
from sklearn import linear_model

# Run
# ln -s /afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db comments.db
# to make it point to the main db.
PICKLE_COMMENTS = 'comments.pickle'
PICKLE_TRAIN = 'train.pickle'
PICKLE_TEST = 'test.pickle'
WORKING_DIR = 'data_dir_all/'

N_COMMENTS = 866388


def save_comments():
    import sqlite3

    db = sqlite3.connect("comments.db")
    cursor = db.cursor()
    comments_data = [(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in cursor.execute(
        "SELECT CommentID, CommentText, EditorSelection, TrainTest FROM Comments") if tt != 3]
    with open(WORKING_DIR + PICKLE_COMMENTS, 'w') as f:
        pickle.dump(comments_data, f)
        # with open(WORKING_DIR + PICKLE_TRAIN, 'w') as f:
        # pickle.dump([(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in comments_data if tt == 1], f)
        # with open(WORKING_DIR + PICKLE_TEST, 'w') as f:
        #     pickle.dump([(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in comments_data if tt == 2], f)


def save_features_to_db(dbIn, dbOut, get_feats, all_keys):
    if not os.path.exists(dbIn):
        raise Exception('Path {} does not exist!'.format(dbOut))
    dbIn = sqlite3.connect(dbIn)
    cursorIn = dbIn.cursor()
    if os.path.exists(dbOut):
        raise Exception('Path {} already exists!'.format(dbOut))
    dbOut = sqlite3.connect(dbOut)
    cursorOut = dbOut.cursor()

    create_statement = 'CREATE TABLE Features (CommentID integer PRIMARY KEY, EditorSelection integer, TrainTest integer, ' + ' REAL, '.join(
        all_keys) + ' REAL);'
    cursorOut.execute(create_statement)

    i = 0
    print_every = N_COMMENTS / 100
    insert_statement = 'INSERT INTO Features VALUES (' + ','.join('{}' for _ in range(len(all_keys) + 3)) + ')'
    for c_id, c_text, ed_sel, tt, a_text in cursorIn.execute(
            'SELECT CommentID, CommentText, EditorSelection, TrainTest, FullText FROM Comments JOIN ArticleText ON ArticleURL = URL'):
        feats = get_feats(c_text, a_text)
        featVals = [feats[key] for key in all_keys]
        cursorOut.execute(insert_statement.format(*([c_id, ed_sel, tt] + featVals)))
        if i % print_every == 0:
            dbOut.commit()
            print 'Finished loading row {} ({} percent complete)'.format(i, i / print_every)
        i += 1

    print 'Finished, processed %d rows' % i
    if i != N_COMMENTS:
        print 'Oh no, expected to process %d rows' % N_COMMENTS

    dbOut.commit()
    cursorOut.close()
    dbOut.close()
    cursorIn.close()
    dbIn.close()


def save_overlap_to_db(dbIn, dbOut):
    all_keys = ['jaccard']
    from features import jaccard_distance

    if not os.path.exists(dbIn):
        raise Exception('Path {} does not exist!'.format(dbOut))
    dbIn = sqlite3.connect(dbIn)
    cursorIn = dbIn.cursor()
    if os.path.exists(dbOut):
        raise Exception('Path {} already exists!'.format(dbOut))
    dbOut = sqlite3.connect(dbOut)
    cursorOut = dbOut.cursor()

    create_statement = 'CREATE TABLE Features (CommentID integer PRIMARY KEY, EditorSelection integer, TrainTest integer, ' + ' REAL, '.join(
        all_keys) + ' REAL);'
    cursorOut.execute(create_statement)

    i = 0
    print_every = N_COMMENTS / 100
    insert_statement = 'INSERT INTO Features VALUES (' + ','.join('{}' for _ in range(len(all_keys) + 3)) + ')'
    for c_id, c_text, ed_sel, tt, a_text in cursorIn.execute(
            'SELECT CommentID, CommentText, EditorSelection, TrainTest, FullText FROM Comments JOIN ArticleText ON ArticleURL = URL'):
        c_jacc_dist = jaccard_distance(c_text, a_text)
        cursorOut.execute(insert_statement.format(c_id, ed_sel, tt, c_jacc_dist))
        if i % print_every == 0:
            dbOut.commit()
            print 'Finished loading row {} ({} percent complete)'.format(i, i / print_every)
        i += 1

    print 'Finished, processed %d rows' % i
    if i != N_COMMENTS:
        print 'Oh no, expected to process %d rows' % N_COMMENTS

    dbOut.commit()
    cursorOut.close()
    dbOut.close()
    cursorIn.close()
    dbIn.close()


# def save_features_to_db(filename, db=None):
# all_keys = ['perc_5_char_words', 'n_8_char_words', 'God', 'n_words', 'perc_2_char_words', 'PhD', 'perc_15_char_words', 'perc_10_char_words', 'n_6_char_words', 'n_9_char_words', 'subjectivity', 'perc_16_char_words', 'perc_18_char_words', 'n_sentences', 'n_18_char_words', 'n_13_char_words', 'avg_word_len', 'perc_20_char_words', 'perc_3_char_words', 'perc_14_char_words', 'n_10_char_words', 'n_16_char_words', 'perc_11_char_words', 'n_4_char_words', 'perc_13_char_words', 'starts_with_I', 'n_periods', 'n_3_char_words', 'avg_sentence_len', 'n_14_char_words', 'n_17_char_words', 'n_12_char_words', 'words_per_sentence', 'polarity', 'n_1_char_words', 'n_2_char_words', 'n_7_char_words', 'perc_6_char_words', 'n_chars', 'n_upper', 'perc_8_char_words', 'president', 'n_15_char_words', 'n_11_char_words', 'n_questions', 'n_exclamations', 'perc_1_char_words', 'perc_17_char_words', 'perc_4_char_words', 'perc_19_char_words', 'n_20_char_words', 'perc_9_char_words', 'n_5_char_words', 'perc_7_char_words', 'perc_12_char_words', 'n_19_char_words']
#     from features import all_comment_feats
#
#     if os.path.exists(db):
#         raise Exception('Path {} already exists!'.format(db))
#     db = sqlite3.connect(db)
#     cursor = db.cursor()
#
#     with open(WORKING_DIR + filename) as f:
#         comments_data = pickle.load(f)
#
#     create_statement = 'CREATE TABLE Features (CommentID integer PRIMARY KEY, EditorSelection integer, TrainTest integer, ' + ' REAL, '.join(all_keys) + ' REAL);'
#     cursor.execute(create_statement)
#
#     i = 0
#     print_every = len(comments_data) / 100
#     insert_statement = 'INSERT INTO Features VALUES (' + ','.join('{}' for _ in range(len(all_keys) + 3)) + ')'
#     for c_id, c_text, ed_sel, tt in comments_data:
#         feats = all_comment_feats(c_text)
#         cursor.execute(insert_statement.format(*([c_id, ed_sel, tt] + [feats[key] for key in all_keys])))
#         if i % print_every == 0:
#             db.commit()
#             print 'Finished loading row {} ({} percent complete)'.format(i, i / print_every)
#         i += 1
#
#     db.commit()
#     cursor.close()
#     db.close()

def save_features(filename):
    from features import all_comment_feats

    with open(WORKING_DIR + filename) as f:
        comments_data = pickle.load(f)
    all_keys = set()
    all_features = []
    Y = []
    for c_id, c_text, ed_sel, tt in comments_data:
        feats = all_comment_feats(c_text)
        all_features.append(feats)
        all_keys.update(feats.keys())
        Y.append(ed_sel)
    all_keys = list(all_keys)
    print all_keys
    Y = np.array(Y)
    X = []
    for i, feats in enumerate(all_features):
        X.append([feats[key] for key in all_keys])
    X = np.array(X)
    # with open(WORKING_DIR + 'features_' + filename, 'w') as f:
    #     pickle.dump((X, Y), f)


# Ensures that there will be a 50/50 split (within N_OFF_BY)
def bump_metrics(train):
    import random

    N_OFF_BY = 2
    X = train[0]
    Y = train[1]
    to_select = []
    n_pos = 0
    n_neg = 0
    prev_diff = 0
    for ylabel in Y:
        diff = abs(n_pos - n_neg + (1 if ylabel else -1))
        if diff < prev_diff or diff < N_OFF_BY:
            if ylabel:
                n_pos += 1
            else:
                n_neg += 1
            to_select.append(True)
        else:
            to_select.append(False)
        prev_diff = diff
    X = [x for select, x in zip(to_select, X) if select]
    Y = [y for select, y in zip(to_select, Y) if select]
    return X, Y

def changeFeatures(traintest, fn):
    traintest[0][0] = fn(traintest[0][0])
    traintest[1][0] = fn(traintest[1][0])

def getNormalized(X):
    std = np.std(X, 0)
    mean = np.mean(X, 0)
    return (X - mean) / std

def doNormalization(traintest):
    changeFeatures(traintest, getNormalized)

def doPCA(traintest):
    from sklearn import decomposition
    X = traintest[0][0]
    pca = decomposition.PCA(n_components='mle')
    model = pca.fit(X)
    changeFeatures(traintest, model.transform)

def calcPCA(X):
    from sklearn import decomposition

    X = np.array(X)
    print X.shape
    std = np.std(X, 0)
    mean = np.mean(X, 0)
    X = (X - mean) / std  # You need to normalize your data first
    pca = decomposition.PCA(n_components='mle')  # n_components is the components number after reduction
    X = pca.fit(X).transform(X)
    return X

def remove_useless(train, test):
    n_cols = train[0].shape[1]
    useful_cols = np.var(train[0], axis=0) > 0
    train[0] = train[0][:,useful_cols]
    test[0] = test[0][:,useful_cols]
    print 'Removed {}/{} columns.'.format(n_cols - train[0].shape[1], n_cols)


def classify(train, test, clf):
    from sklearn import metrics

    # remove_useless(train, test)

    train = bump_metrics(train)
    test = bump_metrics(test)

    # print '\n{}/{}={} Train\n{}/{}={} Test'.format(np.sum(train[1]), len(train[1]),
    #                                                   np.sum(train[1]) / float(len(train[1])),
    #                                                   np.sum(test[1]), len(test[1]),
    #                                                   np.sum(test[1]) / float(len(test[1])))

    # train[0] = calcPCA(train[0])
    # test[0] = calcPCA(test[0])

    clf.fit(*train)
    predicted = clf.predict(test[0])
    print 'Number of 1s predicted is {} out of {}'.format(np.sum(predicted), len(predicted))
    return metrics.classification_report(test[1], predicted)


def addPickCommentsToTable():
    xlabel = ['perc_5_char_words', 'n_8_char_words', 'God', 'n_words', 'perc_2_char_words', 'PhD', 'perc_15_char_words',
              'perc_10_char_words', 'n_6_char_words', 'n_9_char_words', 'subjectivity', 'perc_16_char_words',
              'perc_18_char_words', 'n_sentences', 'n_18_char_words', 'n_13_char_words', 'avg_word_len',
              'perc_20_char_words', 'perc_3_char_words', 'perc_14_char_words', 'n_10_char_words', 'n_16_char_words',
              'perc_11_char_words', 'n_4_char_words', 'perc_13_char_words', 'starts_with_I', 'n_periods',
              'n_3_char_words', 'avg_sentence_len', 'n_14_char_words', 'n_17_char_words', 'n_12_char_words',
              'words_per_sentence', 'polarity', 'n_1_char_words', 'n_2_char_words', 'n_7_char_words',
              'perc_6_char_words', 'n_chars', 'n_upper', 'perc_8_char_words', 'president', 'n_15_char_words',
              'n_11_char_words', 'n_questions', 'n_exclamations', 'perc_1_char_words', 'perc_17_char_words',
              'perc_4_char_words', 'perc_19_char_words', 'n_20_char_words', 'perc_9_char_words', 'n_5_char_words',
              'perc_7_char_words', 'perc_12_char_words', 'n_19_char_words']
    import sqlite3

    db = sqlite3.connect("nltk_features.db")
    cursor = db.cursor()

    # for label in xlabel:
    #     cursor.execute("ALTER TABLE Features ADD COLUMN %s REAL" % label)

    print 'Done altering table'
    with open('data_dir_all/features_comments.pickle') as f:
        all_features, labels = pickle.load(f)
    print 'Done loading features'
    with open(WORKING_DIR + PICKLE_COMMENTS) as f:
        all_comments = pickle.load(f)
    print 'Done loading %d comments' % len(all_comments)
    print all_features.shape
    assert all_features.shape[0] == len(all_comments)
    assert all_features.shape[1] == len(xlabel)
    i = 0
    print_every = len(all_comments) / 100
    insert_statement = 'INSERT INTO Features VALUES (' + ','.join('{}' for _ in range(len(xlabel) + 3)) + ')'
    for comment, features, label in zip(all_comments, all_features, labels):
        c_id, c_text, ed_sel, tt = comment
        assert label == ed_sel
        cursor.execute(insert_statement.format(*([c_id, ed_sel, tt] + list(features))))
        if i % print_every == 0:
            print 'Finished loading row {} ({} percent complete)'.format(i, i / print_every)
        i += 1

    cursor.close()
    db.close()


#def todo ():
# from sklearn.linear_model import SGDClassifier
#     text_clf = Pipeline([('vect', CountVectorizer()),
#                          ('tfidf', TfidfTransformer()),
#                          ('clf', SGDClassifier(loss='hinge', penalty='l2'])
#     text_clf.fit(twenty_train.data, twenty_train.target)
#     predicted = text_clf.predict(docs_test)


def load_train_test(*db_col_names):
    db = sqlite3.connect(db_col_names[0][0])
    cursor = db.cursor()

    get_all_select = 'SELECT'.format()
    get_all_from_join = 'FROM'
    for i, (db_name, col_names) in enumerate(db_col_names):
        new_db_name = db_name[:-3]
        cursor.execute("ATTACH '{}' AS {}".format(db_name, new_db_name))
        table_name = 'f' + str(i)
        get_all_select += ''.join(' ' + table_name + '.' + cn + ',' for cn in col_names)
        if i != 0:
            get_all_from_join += ' JOIN ' + new_db_name + '.Features ' + table_name
            get_all_from_join += ' ON f{}.CommentID = f{}.CommentID'.format(i - 1, i)
        else:
            get_all_from_join += ' Features ' + table_name

    get_all_statement = get_all_select[:-1] + ' ' + get_all_from_join + ';'

    print '>>>> Running sql statement:'
    print get_all_statement

    cursor.execute(get_all_statement)
    data = cursor.fetchall()
    print '>>>> Done running sql statement.'

    # if np.any(np.isnan(data)):
    #     raise ValueError('Some of the data is not a valid number.')

    trainX = np.array([d[3:] for d in data if d[2] == 1])
    trainY = np.array([d[1] for d in data if d[2] == 1])
    testX = np.array([d[3:] for d in data if d[2] == 2])
    testY = np.array([d[1] for d in data if d[2] == 2])

    cursor.close()
    db.close()

    return [[trainX, trainY], [testX, testY]]

def report(grid_scores, n_top=3):
    top_scores = sorted(grid_scores, key=itemgetter(1), reverse=True)[:n_top]
    for i, score in enumerate(top_scores):
        print("Model with rank: {0}".format(i + 1))
        print("Mean validation score: {0:.3f} (std: {1:.3f})".format(
            score.mean_validation_score,
            np.std(score.cv_validation_scores)))
        print("Parameters: {0}".format(score.parameters))
        print("")

if __name__ == '__main__':
    from features import all_comment_feats
    from features import all_comment_keys
    from features import jaccard_distance

    # if len(sys.argv) > 1:
    #     WORKING_DIR = sys.argv[1]
    # if os.path.isdir(WORKING_DIR):
    #     print 'Directory ' + WORKING_DIR + ' already exists.'
    # else:
    #     os.mkdir(WORKING_DIR)

    # save_comments()
    # save_features(PICKLE_COMMENTS)

    # save_features(PICKLE_SMALL_TRAIN)
    # save_features(PICKLE_SMALL_TEST)
    traintest = load_train_test(('all_features.db', ['*']))

    # param_dist = {"loss": ['hinge', 'log', 'squared_hinge', 'squared_loss', 'huber'],
    #               'penalty': ['none', 'l2', 'l1', 'elasticnet'],
    #               'alpha': scipy.stats.expon(scale=0.0001)
    #              }
    # clf = sklearn.linear_model.SGDClassifier(average=True)
    # random_search = sklearn.grid_search.RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=30)
    # random_search.fit(*bump_metrics(traintest[0]))
    # report(random_search.grid_scores_)
    # with open('feats.pickle') as f:
    #     traintest = pickle.load(f)
    print 'Done loading.'

    # print 'with no penalty'
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='hinge', penalty='none')))
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='log', penalty='none')))
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='squared_hinge', penalty='none')))
    # print 'with no l1'

    print 'As is'
    remove_useless(*traintest)
    print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='hinge', penalty='l1')))

    print 'Normalized'
    doNormalization(traintest)
    print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='hinge', penalty='l1')))

    print 'PCA'
    doPCA(traintest)
    print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='hinge', penalty='l1')))

    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='log', penalty='l1')))
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='squared_hinge', penalty='l1')))
    # print 'with no l2'
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='hinge', penalty='l2')))
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='log', penalty='l2')))
    # print(classify(traintest[0], traintest[1], sklearn.linear_model.SGDClassifier(average=True, alpha=1e-5, loss='squared_hinge', penalty='l2')))
    # # classify(*traintest)

    # save_features_to_db('comments.pickle', 'nltk_features.db')

    # save_features_to_db('comments.db', 'all_features.db', all_comment_feats, list(all_comment_keys()))
