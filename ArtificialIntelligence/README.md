# Artificial Intelligence Utilities

## Chat Sentiment Over Time
Use `chat_sentiment_over_time.py` to score chat logs with VADER or a Hugging Face sentiment model, aggregate results by day and session, and plot how sentiment changes over time.

### Files
- `chat_sentiment_over_time.py`: CLI that loads a chat CSV, scores messages, aggregates sentiment, and saves a matplotlib plot.
- `sample_chat_log.csv`: Example chat data with ISO timestamps, session identifiers, and messages.

### Setup
```bash
pip install -r requirements.txt
```
The script downloads the VADER lexicon on first run. To use a Hugging Face model instead of VADER, also install `transformers` (and a backend such as `torch`).

### Run the analysis
From the repository root:
```bash
python ArtificialIntelligence/chat_sentiment_over_time.py --output ArtificialIntelligence/sentiment_over_time.png
```

### View the results
- The command above saves `sentiment_over_time.png` next to the script. Open the PNG in an image viewer to inspect the plot.
- To render the plot interactively (if your environment supports GUI windows), add `--show`.
- To try a Hugging Face model, pass its name: 
  ```bash
  python ArtificialIntelligence/chat_sentiment_over_time.py \
    --model distilbert-base-uncased-finetuned-sst-2-english \
    --output ArtificialIntelligence/sentiment_over_time.png
  ```

### Custom logs
Provide your own CSV with columns `timestamp`, `session`, and `message`:
```bash
python ArtificialIntelligence/chat_sentiment_over_time.py --log-path path/to/your_log.csv
```
