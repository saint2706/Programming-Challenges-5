"""Minimal spam filter example using multinomial Naive Bayes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB


@dataclass
class SpamExample:
    text: str
    label: str


def build_corpus() -> List[SpamExample]:
    """Return a tiny corpus of spam and ham emails."""
    spam_messages = [
        "Limited time offer: Earn cash fast from home!",
        "Congratulations, you have won a free cruise. Click to claim now",
        "Lowest mortgage rates available. Refinance today",
        "Act now! Claim your $1000 gift card by clicking this link",
        "You have been selected for a prize. Provide bank details to proceed",
    ]

    ham_messages = [
        "Team lunch is scheduled for Friday at noon",
        "Can we reschedule the meeting to next Tuesday?",
        "Thanks for sending the project update earlier",
        "Here are the notes from today\'s call. Let me know if anything is missing",
        "Please review the latest draft when you have time",
    ]

    corpus: List[SpamExample] = [SpamExample(text, "spam") for text in spam_messages]
    corpus.extend(SpamExample(text, "ham") for text in ham_messages)
    return corpus


def vectorize_corpus(
    corpus: Sequence[SpamExample],
    *,
    stop_words: str | None = "english",
) -> Tuple[CountVectorizer, np.ndarray, np.ndarray]:
    """Vectorize text into bag-of-words counts."""
    vectorizer = CountVectorizer(stop_words=stop_words)
    texts = [example.text for example in corpus]
    labels = np.array([example.label for example in corpus])
    features = vectorizer.fit_transform(texts)
    return vectorizer, features, labels


def train_sklearn_nb(features: np.ndarray, labels: np.ndarray) -> MultinomialNB:
    """Train scikit-learn's MultinomialNB model."""
    model = MultinomialNB()
    model.fit(features, labels)
    return model


def train_manual_nb(features, labels, alpha: float = 1.0):
    """Train a simple multinomial NB model manually using NumPy.

    Returns a tuple of (classes, log_prior, log_conditional_probabilities).
    """
    classes, class_indices = np.unique(labels, return_inverse=True)
    class_counts = np.bincount(class_indices)

    # Token counts per class
    feature_counts = np.zeros((len(classes), features.shape[1]), dtype=np.float64)
    for idx, cls in enumerate(classes):
        cls_rows = features[class_indices == idx]
        feature_counts[idx] = np.asarray(cls_rows.sum(axis=0)).ravel()

    # Laplace smoothing
    smoothed_fc = feature_counts + alpha
    smoothed_cc = smoothed_fc.sum(axis=1)

    log_class_prior = np.log(class_counts / labels.shape[0])
    log_conditional = np.log(smoothed_fc / smoothed_cc[:, None])
    return classes, log_class_prior, log_conditional


def manual_predict(vectorizer: CountVectorizer, params, samples: Iterable[str]) -> List[str]:
    classes, log_prior, log_conditional = params
    X = vectorizer.transform(list(samples))
    log_likelihood = X @ log_conditional.T
    log_posterior = log_likelihood + log_prior
    predictions = np.asarray(classes)[np.asarray(log_posterior.argmax(axis=1)).ravel()]
    return predictions.tolist()


def main() -> None:
    corpus = build_corpus()
    vectorizer, features, labels = vectorize_corpus(corpus)

    sklearn_model = train_sklearn_nb(features, labels)
    manual_params = train_manual_nb(features, labels)

    sample_emails = [
        "Free money waiting for you, click this link",
        "Can we push our 1:1 to tomorrow?",
        "Urgent! Verify your account to avoid suspension",
        "Thanks for your thoughtful feedback on the document",
    ]

    print("=== scikit-learn MultinomialNB ===")
    for email, label, proba in zip(
        sample_emails,
        sklearn_model.predict(vectorizer.transform(sample_emails)),
        sklearn_model.predict_proba(vectorizer.transform(sample_emails)),
    ):
        spam_prob = proba[sklearn_model.classes_ == "spam"][0]
        print(f"{label.upper():>4} | spam probability={spam_prob:.3f} | {email}")

    print("\n=== Manual multinomial NB ===")
    for email, label in zip(sample_emails, manual_predict(vectorizer, manual_params, sample_emails)):
        print(f"{label.upper():>4} | {email}")


if __name__ == "__main__":
    main()
