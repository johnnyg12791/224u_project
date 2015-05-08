from itertools import groupby

def basic_feats(text):
        # Length features
        MAX_CHARS_PER_WORD = 20
        words = text.split()
        feats = {
            'n_chars': len(text),
            'n_words': len(words),
            'n_periods': sum(1 for c in text if c == '.'),
            'n_questions': sum(1 for c in text if c == '?'),
            'n_exclamations': sum(1 for c in text if c == '!'),
            'n_upper': sum(1 for c in text if c.isupper())
        }
        feats['avg_word_len'] = feats['n_chars'] / float(feats['n_words'])
        n_sentences = feats['n_periods'] + feats['n_questions'] + feats['n_exclamations'] + 1
        feats['n_sentences'] = n_sentences
        feats['avg_sentence_len'] = feats['n_chars'] / float(n_sentences)
        feats['words_per_sentence'] = feats['n_words'] / float(n_sentences)
        for i in range(1, MAX_CHARS_PER_WORD + 1):
            key = str(i) + '_char_words'
            n_iletter_words = sum(1 for w in words if len(w) == i)
            feats['n_' + key] = n_iletter_words
            feats['perc_' + key] = n_iletter_words / feats['n_words']
        return feats

def nltk_feats(text):
    import nltk
    POS_TREEBANK_TAGS = {'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD', 'NN', 'NNS', 'NNP', 'NNPS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR', 'RBS', 'RP', 'SYM', 'TO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB'}
    # NLTK features
    tokens = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(tokens)
    feats = {k: 0 for k in POS_TREEBANK_TAGS}
    # for key, group in
    return feats

def textblob_feats(text):
    from textblob import TextBlob

def similarity_word_feature(textA, textB):
    splitA = textA.split()
    splitB = textB.split()
    num_same_words = len(set(splitA).intersection(set(splitB)))
    num_total_words = len(set(splitA + splitB))
    return float(num_same_words) / num_total_words

if __name__ == '__main__':
    text = 'This is my. Comment?'
    feats = basic_feats(text)
    assert feats['n_chars'] == len(text)
    assert feats['words_per_sentence'] == 2.0
    assert feats['n_sentences'] == 2
    print 'All tests passed'