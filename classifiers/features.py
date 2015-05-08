import string
# import nltk
# from textblob import TextBlob
from collections import Counter

class Features:
    MAX_CHARS_PER_WORD = 20

    @staticmethod
    def len_feats(text):
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
        n_sentences = feats['n_periods'] + feats['n_questions'] + feats['n_exclamations']
        feats['n_sentences'] = n_sentences
        feats['avg_sentence_len'] = feats['n_chars'] / float(n_sentences)
        feats['words_per_sentence'] = feats['n_words'] / float(n_sentences)
        for i in range(1, MAX_CHARS_PER_WORD + 1):
            key = str(i) + '_char_words'
            n_iletter_words = sum(1 for w in words if len(w) == i)
            feats['n_' + key] = n_iletter_words
            feats['perc_' + key] = n_iletter_words / feats['n_words']
        return feats

    @staticmethod
    def similarity_word_feature(textA, textB):
        splitA = textA.split()
        splitB = textB.split()
        num_same_words = len(set(splitA).intersection(set(splitB)))
        num_total_words = len(set(splitA + splitB))
        return float(num_same_words) / num_total_words

if __name__ == '__main__':
    text = 'This is my. Comment?'
    feats = Features.len_feats(text)
    assert feats['n_chars'] == len(text)
    assert feats['words_per_sentence'] == 2.0
    assert feats['n_sentences'] == 2
    print 'All tests passed'