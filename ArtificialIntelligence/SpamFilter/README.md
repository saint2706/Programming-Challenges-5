# Spam Filter Walkthrough

This folder contains a minimal example of training a multinomial Naive Bayes spam filter using scikit-learn and a manual NumPy implementation.

## Setup

1. Install dependencies (scikit-learn and NumPy):
   ```bash
   pip install scikit-learn numpy
   ```
2. Run the demonstration script:
   ```bash
   python spam_filter.py
   ```

## What the script does

- Defines a small spam vs. ham corpus using short email-like sentences.
- Vectorizes the text with `CountVectorizer` (stop words removed) to create bag-of-words counts.
- Trains scikit-learn's `MultinomialNB` and a manual multinomial Naive Bayes variant with Laplace smoothing.
- Scores several sample emails and prints predictions and spam probabilities.

## Sample output

```
=== scikit-learn MultinomialNB ===
SPAM | spam probability=0.845 | Free money waiting for you, click this link
 HAM | spam probability=0.500 | Can we push our 1:1 to tomorrow?
 HAM | spam probability=0.500 | Urgent! Verify your account to avoid suspension
 HAM | spam probability=0.305 | Thanks for your thoughtful feedback on the document

=== Manual multinomial NB ===
SPAM | Free money waiting for you, click this link
 HAM | Can we push our 1:1 to tomorrow?
 HAM | Urgent! Verify your account to avoid suspension
 HAM | Thanks for your thoughtful feedback on the document
```

Because the corpus is intentionally tiny, probabilities around 0.5 indicate ambiguous signals; experiment with the corpus or `stop_words` argument to see how outputs change.
