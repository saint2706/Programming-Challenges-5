"""Visualize chat sentiment over time using VADER or Hugging Face models."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import matplotlib

# Use a non-interactive backend so the script works in headless environments.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  # pylint: disable=wrong-import-position
import pandas as pd  # noqa: E402  # pylint: disable=wrong-import-position


@dataclass
class SentimentResult:
    """Container for scored chat messages."""

    timestamp: pd.Timestamp
    session: str
    message: str
    sentiment: float


@dataclass
class AggregatedSentiment:
    """Container for aggregated sentiment per date and session."""

    date: pd.Timestamp
    session: str
    mean_sentiment: float
    message_count: int


class SentimentScorer:
    """Score chat messages with either VADER or a Hugging Face model."""

    def __init__(self, model: str = "vader") -> None:
        """
        Docstring for __init__.
        """
        self.model = model
        self._vader_analyzer = None
        self._hf_pipeline = None

    def _load_vader(self):
        """
        Docstring for _load_vader.
        """
        if self._vader_analyzer is not None:
            return self._vader_analyzer

        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer

        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon")
        self._vader_analyzer = SentimentIntensityAnalyzer()
        return self._vader_analyzer

    def _load_huggingface(self):
        """
        Docstring for _load_huggingface.
        """
        if self._hf_pipeline is not None:
            return self._hf_pipeline

        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover - handled at runtime
            raise RuntimeError(
                "Transformers is not installed. Install it with `pip install transformers torch` "
                "or run with --model vader."
            ) from exc

        model_name = None if self.model.lower() == "huggingface" else self.model
        self._hf_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name or "distilbert-base-uncased-finetuned-sst-2-english",
        )
        return self._hf_pipeline

    def score_messages(self, messages: pd.DataFrame) -> List[SentimentResult]:
        """
        Docstring for score_messages.
        """
        scorer = self.model.lower()
        if scorer == "vader":
            analyzer = self._load_vader()

            def score_fn(text: str) -> float:
                """
                Docstring for score_fn.
                """
                return analyzer.polarity_scores(text)["compound"]

        else:
            pipeline = self._load_huggingface()

            def score_fn(text: str) -> float:
                """
                Docstring for score_fn.
                """
                result = pipeline(text)[0]
                label = result["label"].lower()
                score = result["score"]
                return score if "pos" in label else -score

        results: List[SentimentResult] = []
        for _, row in messages.iterrows():
            sentiment_value = score_fn(str(row["message"]))
            results.append(
                SentimentResult(
                    timestamp=row["timestamp"],
                    session=str(row["session"]),
                    message=str(row["message"]),
                    sentiment=float(sentiment_value),
                )
            )
        return results


def load_chat_log(path: Path) -> pd.DataFrame:
    """
    Docstring for load_chat_log.
    """
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def aggregate_sentiment(results: Iterable[SentimentResult]) -> List[AggregatedSentiment]:
    """
    Docstring for aggregate_sentiment.
    """
    df = pd.DataFrame([r.__dict__ for r in results])
    df["date"] = df["timestamp"].dt.date
    grouped = (
        df.groupby(["date", "session"], as_index=False)
        .agg(mean_sentiment=("sentiment", "mean"), message_count=("message", "count"))
        .sort_values(["date", "session"])
    )
    aggregated: List[AggregatedSentiment] = []
    for _, row in grouped.iterrows():
        aggregated.append(
            AggregatedSentiment(
                date=pd.to_datetime(row["date"]),
                session=str(row["session"]),
                mean_sentiment=float(row["mean_sentiment"]),
                message_count=int(row["message_count"]),
            )
        )
    return aggregated


def plot_sentiment(aggregated: List[AggregatedSentiment], output_path: Path, show: bool) -> None:
    """
    Docstring for plot_sentiment.
    """
    if not aggregated:
        raise ValueError("No sentiment scores to plot.")

    fig, ax = plt.subplots(figsize=(10, 6))
    df = pd.DataFrame([a.__dict__ for a in aggregated])
    df.sort_values("date", inplace=True)
    for session, group in df.groupby("session"):
        ax.plot(
            group["date"],
            group["mean_sentiment"],
            marker="o",
            label=f"{session} (n={group['message_count'].sum()})",
        )

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_title("Chat Sentiment Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Average Sentiment (compound)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    output_path = output_path.resolve()
    fig.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")
    if show:
        plt.show()


def parse_args() -> argparse.Namespace:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description="Plot chat sentiment over time.")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=Path(__file__).with_name("sample_chat_log.csv"),
        help="Path to a CSV log with timestamp, session, and message columns.",
    )
    parser.add_argument(
        "--model",
        default="vader",
        help=(
            "Which sentiment model to use. 'vader' uses NLTK's VADER analyzer. "
            "Any other value will be treated as a Hugging Face model name (e.g., distilbert-base-uncased-finetuned-sst-2-english)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("sentiment_over_time.png"),
        help="Where to save the output plot.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the matplotlib window after saving the plot (requires a GUI-capable environment).",
    )
    return parser.parse_args()


def main() -> None:
    """
    Docstring for main.
    """
    args = parse_args()
    messages = load_chat_log(args.log_path)
    scorer = SentimentScorer(model=args.model)
    results = scorer.score_messages(messages)
    aggregated = aggregate_sentiment(results)
    plot_sentiment(aggregated, args.output, show=args.show)


if __name__ == "__main__":
    main()
