import argparse
import json
import os
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(__file__), 'questions.json')

def load_questions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_questions(questions):
    with open(DATA_FILE, 'w') as f:
        json.dump(questions, f, indent=4)

def add_question(args):
    questions = load_questions()
    new_id = max([q['id'] for q in questions], default=0) + 1
    question = {
        "id": new_id,
        "question": args.question,
        "answer": args.answer,
        "next_review": datetime.now().strftime("%Y-%m-%d"),
        "interval": 0,
        "ease_factor": 2.5
    }
    questions.append(question)
    save_questions(questions)
    print(f"Question added with ID {new_id}.")

def list_questions(args):
    questions = load_questions()
    if not questions:
        print("No questions found.")
        return
    for q in questions:
        print(f"[{q['id']}] {q['question']} (Next review: {q['next_review']})")

def review_questions(args):
    questions = load_questions()
    today = datetime.now().strftime("%Y-%m-%d")
    due_questions = [q for q in questions if q['next_review'] <= today]

    if not due_questions:
        print("No questions due for review today!")
        return

    print(f"You have {len(due_questions)} questions to review.\n")
    
    for q in due_questions:
        print(f"Question: {q['question']}")
        input("Press Enter to see the answer...")
        print(f"Answer: {q['answer']}")
        
        while True:
            try:
                rating = int(input("Rate recall (0=Blackout, 3=Pass, 5=Perfect): "))
                if 0 <= rating <= 5:
                    break
            except ValueError:
                pass
            print("Please enter a number between 0 and 5.")

        # SuperMemo-2 Algorithm Simplified
        if rating >= 3:
            if q['interval'] == 0:
                q['interval'] = 1
            elif q['interval'] == 1:
                q['interval'] = 6
            else:
                q['interval'] = int(q['interval'] * q['ease_factor'])
            
            q['ease_factor'] = q['ease_factor'] + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
            if q['ease_factor'] < 1.3:
                q['ease_factor'] = 1.3
        else:
            q['interval'] = 1
            
        q['next_review'] = (datetime.now() + timedelta(days=q['interval'])).strftime("%Y-%m-%d")
        print(f"Next review in {q['interval']} days.\n")
        save_questions(questions)

def main():
    parser = argparse.ArgumentParser(description="Interview Prep CLI with Spaced Repetition")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new question')
    add_parser.add_argument('question', help='The question text')
    add_parser.add_argument('answer', help='The answer text')

    # List command
    list_parser = subparsers.add_parser('list', help='List all questions')

    # Review command
    review_parser = subparsers.add_parser('review', help='Start review session')

    args = parser.parse_args()

    if args.command == 'add':
        add_question(args)
    elif args.command == 'list':
        list_questions(args)
    elif args.command == 'review':
        review_questions(args)

if __name__ == "__main__":
    main()
