import string
from collections import defaultdict

def nltk_feats(text):
    import nltk
    # Penn Discourse Treebank
    POS_TREEBANK_TAGS = {'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD', 'NN', 'NNS', 'NNP', 'NNPS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR', 'RBS', 'RP', 'SYM', 'TO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB'}
    MAX_CHARS_PER_WORD = 20

    feats = defaultdict(float)
    tokens = nltk.word_tokenize(text)

    # Basic length features.
    feats['n_chars'] = len(text)
    feats['n_words'] = len(tokens)
    feats['n_periods'] = sum(1 for c in tokens if c == '.')
    feats['n_questions'] = sum(1 for c in tokens if c == '?')
    feats['n_exclamations'] = sum(1 for c in tokens if c == '!')
    feats['n_upper'] = sum(1 for c in text if c.isupper())
    feats['avg_word_len'] = feats['n_chars'] / float(feats['n_words'])
    n_sentences = max(feats['n_periods'] + feats['n_questions'] + feats['n_exclamations'], 1)
    feats['n_sentences'] = n_sentences
    feats['avg_sentence_len'] = feats['n_chars'] / float(n_sentences)
    feats['words_per_sentence'] = feats['n_words'] / float(n_sentences)
    for i in range(1, MAX_CHARS_PER_WORD + 1):
        # Record number/percent of tokens of length i.
        key = str(i) + '_char_words'
        n_iletter_words = sum(1 for w in tokens if len(w) == i)
        feats['n_' + key] = n_iletter_words
        feats['perc_' + key] = n_iletter_words / float(feats['n_words'])

    # Extraneous feats
    feats['starts_with_I'] = 1.0 if text[:2] == 'I ' else 0.0

    # Bag of parts of speech
    '''
    tagged = nltk.pos_tag(tokens)
    feats['n_novel_tags'] = 0.0
    for word, tag in tagged:
        if tag not in POS_TREEBANK_TAGS:
            feats['n_novel_tags'] += 1.0
        if tag not in string.punctuation:
	    feats[tag] += 1
	#feats[tag.replace(":", "colon")] += 1.0
	    #print tag
    #print feats
    '''
    return feats

def textblob_feats(text):
    from textblob import TextBlob
    feats = defaultdict(float)
    blob = TextBlob(text)
    feats['polarity'] = blob.polarity
    feats['subjectivity'] = blob.subjectivity
    return feats

def all_comment_feats(text):
    f = nltk_feats(text)
    #f2 = textblob_feats(text)
    #assert len(set(f.keys()).union(f2.keys())) == 0
    #f.update(f2)
    return f

def jaccard_distance(textA, textB):
    import nltk
    from nltk.metrics.distance import jaccard_distance
    return jaccard_distance(set(nltk.word_tokenize(textA)), set(nltk.word_tokenize(textB)))

if __name__ == '__main__':
    simple = 'This is my comment'
    feats = basic_feats(simple)
    featsNLTK = nltk_feats(simple)
    for k, v in feats.items():
        assert feats[k] == featsNLTK[k]
    assert feats['n_chars'] == len(simple)
    print feats['perc_2_char_words']
    assert feats['perc_2_char_words'] == 0.5
    assert feats['n_sentences'] == 1
    long = "I the only danger. But the only danger he had really been in was in the last half-hour of his imprisonment, when Owl, who had just flown up, sat on a branch of his tree to comfort him, and told him a very long story about an aunt who had once laid a seagull's egg by mistake, and the story went on and on, rather like this sentence."
    feats = nltk_feats(long)
    assert feats['starts_with_I'] == 1.0
    assert feats['n_periods'] == 2
    assert jaccard_distance('What how be', 'What how be 2') == 0.25
    print 'All tests passed'