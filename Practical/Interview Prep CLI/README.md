# Interview Prep CLI

A command-line tool for practicing interview questions using spaced repetition.

## Usage

1. **Add Questions**: Manually edit `questions.json` or use the tool (if supported) to add Q&A.
   *Format of `questions.json`:*
   ```json
   [
     {
       "id": 1,
       "question": "What is a closure?",
       "answer": "...",
       "next_review": "2023-10-27T10:00:00",
       "interval": 1
     }
   ]
   ```

2. **Run the Drill**:
   ```bash
   python "Practical/Interview Prep CLI/prep.py"
   ```
   The tool will show you questions due for review. Rate your confidence to update the schedule.

## Requirements
* Python 3+
