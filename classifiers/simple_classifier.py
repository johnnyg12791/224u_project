__author__ = 'mark'
import pickle
import numpy as np
import os, sys

# Run
# ln -s /afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db comments.db
# to make it point to the main db.
PICKLE_COMMENTS = 'comments.pickle'
PICKLE_SMALL_TRAIN = 'small_train.pickle'
PICKLE_SMALL_TEST = 'small_test.pickle'
WORKING_DIR = 'default_data_dir60000/'
N_SMALL = 60000


def save_comments():
    import sqlite3

    db = sqlite3.connect("comments.db")
    cursor = db.cursor()
    comments_data = [(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in cursor.execute(
        "SELECT CommentID, CommentText, EditorSelection, TrainTest FROM Comments LIMIT {}".format(N_SMALL)) if tt != 3]
    # with open(PICKLE_COMMENTS, 'w') as f:
    # pickle.dump(comments_data, f)
    with open(WORKING_DIR + PICKLE_SMALL_TRAIN, 'w') as f:
        pickle.dump([(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in comments_data if tt == 1], f)
    with open(WORKING_DIR + PICKLE_SMALL_TEST, 'w') as f:
        pickle.dump([(c_id, c_text, ed_sel, tt) for c_id, c_text, ed_sel, tt in comments_data if tt == 2], f)


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
    Y = np.array(Y)
    all_keys = list(all_keys)
    X = []
    for i, feats in enumerate(all_features):
        X.append([feats[key] for key in all_keys])
    X = np.array(X)
    print X
    print X.shape
    with open(WORKING_DIR + 'features_' + filename, 'w') as f:
        pickle.dump((X, Y), f)

def bump_metrics(train):
    import random
    X = train[0]
    Y = train[1]
    to_select = [random.random() > (0.1 if ylabel else 0.9) for ylabel in Y]
    X = [x for i, x in enumerate(X) if to_select[i]]
    Y = [y for i, y in enumerate(Y) if to_select[i]]
    return X, Y

def calcPCA(X):
    from sklearn import decomposition

    X = (X - np.mean(X, 0)) / np.std(X, 0) # You need to normalize your data first
    pca = decomposition.PCA(n_components='mle') # n_components is the components number after reduction
    X = pca.fit(X).transform(X)
    return X

def SGDClassify(train, test):
    from sklearn import linear_model
    from sklearn import metrics

    # train = bump_metrics(train)
    # test = bump_metrics(test)

    print '{} Train, {} Test, {} Positive Train, {} Positive Test'.format(len(train[1]), len(test[1]),
                                                                          np.sum(train[1]), np.sum(test[1]))

    train = list(train)
    test = list(test)
    train[0] = calcPCA(train[0])
    test[0] = calcPCA(test[0])

    clf = linear_model.SGDClassifier()
    clf.fit(*train)
    predicted = clf.predict(test[0])
    print 'Number of 1s predicted is {} out of {}'.format(np.sum(predicted), len(predicted))
    print(metrics.classification_report(test[1], predicted))

    # def todo():

# from sklearn.linear_model import SGDClassifier
#     text_clf = Pipeline([('vect', CountVectorizer()),
#                          ('tfidf', TfidfTransformer()),
#                          ('clf', SGDClassifier(loss='hinge', penalty='l2'])
#     text_clf.fit(twenty_train.data, twenty_train.target)
#     predicted = text_clf.predict(docs_test)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        WORKING_DIR = sys.argv[1]
    if os.path.isdir(WORKING_DIR):
        print 'Directory ' + WORKING_DIR + ' already exists.'
    else:
        os.mkdir(WORKING_DIR)
    save_comments()
    save_features(PICKLE_SMALL_TRAIN)
    save_features(PICKLE_SMALL_TEST)
    traintest = (pickle.load(open(WORKING_DIR + 'features_' + PICKLE_SMALL_TRAIN)),
                 pickle.load(open(WORKING_DIR + 'features_' + PICKLE_SMALL_TEST)))
    SGDClassify(*traintest)