#!/usr/bin/env python3
import json
import os
import sys
import pickle
import bcrypt
import random
import time
import datetime
import getpass
import signal

BASE_DIR = os.path.dirname(__file__)
QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.dat')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.dat')
FEEDBACK_FILE = os.path.join(BASE_DIR, 'feedback.dat')


class TimeoutExpired(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutExpired


def get_input_timeout(prompt, timeout):
    # Use signal.alarm which works on Unix (macOS)
    signal.signal(signal.SIGALRM, lambda s, f: alarm_handler(s, f))
    signal.alarm(int(timeout))
    start = time.time()
    try:
        ans = input(prompt)
        elapsed = time.time() - start
        return ans, elapsed, False
    except TimeoutExpired:
        return '', timeout, True
    finally:
        signal.alarm(0)


def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        print('Error: questions.json not found. Please create the question bank.')
        sys.exit(1)
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'Error: questions.json is malformed — {e}.')
        sys.exit(1)
    if 'questions' not in data or not isinstance(data['questions'], list):
        print('Error: questions.json is malformed — missing "questions" list.')
        sys.exit(1)
    # Validate required fields per question
    questions = data['questions']
    for i, q in enumerate(questions):
        if 'question' not in q or 'type' not in q or 'answer' not in q:
            print(f'Error: questions.json is malformed — question at index {i} missing required fields.')
            sys.exit(1)
        # normalize some fields
        if 'difficulty' not in q:
            q['difficulty'] = 'Medium'
        if 'category' not in q:
            q['category'] = 'General'
        if 'time_limit' not in q:
            q['time_limit'] = 10
    return questions


def load_data(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception:
        return default


def save_data(path, data):
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def signup(users):
    while True:
        username = input('Choose a username: ').strip()
        if not username:
            print('Username cannot be empty.')
            continue
        if username in users:
            print('Username already exists. Please choose another.')
            continue
        passwd = getpass.getpass('Choose a password: ')
        passwd2 = getpass.getpass('Confirm password: ')
        if passwd != passwd2:
            print('Passwords do not match.')
            continue
        pw_hash = bcrypt.hashpw(passwd.encode('utf-8'), bcrypt.gensalt())
        users[username] = pw_hash
        save_data(USERS_FILE, users)
        print(f'Account created. Welcome, {username}!')
        return username


def login(users):
    while True:
        username = input('Username: ').strip()
        if not username:
            continue
        if username not in users:
            yn = input('User not found. Create new account? [Y/n]: ').strip().lower()
            if yn in ('', 'y', 'yes'):
                return signup(users)
            else:
                continue
        attempts = 3
        for _ in range(attempts):
            passwd = getpass.getpass('Password: ')
            try:
                if bcrypt.checkpw(passwd.encode('utf-8'), users[username]):
                    print(f'Welcome back, {username}!')
                    return username
                else:
                    print('Incorrect password.')
            except Exception:
                print('Password check failed. Corrupt user data?')
                break
        print('Failed to login. Try again.')


def weighted_sample_without_replacement(items, weights, k):
    items_copy = list(items)
    weights_copy = list(weights)
    selected = []
    if k >= len(items_copy):
        return items_copy
    for _ in range(k):
        total = sum(weights_copy)
        if total <= 0:
            # fallback uniform
            choice = random.randrange(len(items_copy))
        else:
            r = random.random() * total
            upto = 0
            choice = None
            for i, w in enumerate(weights_copy):
                upto += w
                if r <= upto:
                    choice = i
                    break
            if choice is None:
                choice = len(items_copy) - 1
        selected.append(items_copy.pop(choice))
        weights_copy.pop(choice)
    return selected


def start_quiz(username, questions, feedback, history):
    try:
        num = int(input('How many questions would you like? ').strip())
    except Exception:
        print('Invalid number. Using 5 questions.')
        num = 5
    print('Choose difficulty: [1] Easy  [2] Medium  [3] Hard  [4] Any')
    diff_map = {'1': 'Easy', '2': 'Medium', '3': 'Hard', '4': None}
    choice = input('Choose: ').strip()
    desired = diff_map.get(choice, None)
    pool = []
    for idx, q in enumerate(questions):
        qcopy = dict(q)
        qcopy['_index'] = idx
        pool.append(qcopy)
    if desired is not None:
        pool = [q for q in pool if q.get('difficulty', 'Medium') == desired]
    available = len(pool)
    if available == 0:
        print('No questions available for that difficulty. Using all questions instead.')
        pool = [dict(q, _index=i) for i, q in enumerate(questions)]
        available = len(pool)
    if num > available:
        print(f'Only {available} questions available. Running a {available}-question quiz instead.')
        num = available
    # compute weights based on feedback for this user
    weights = []
    user_fb = feedback.get(username, {})
    for q in pool:
        idx = q['_index']
        fb = user_fb.get(idx, {'like': 0, 'dislike': 0})
        likes = fb.get('like', 0)
        dislikes = fb.get('dislike', 0)
        w = 1.0 + 0.5 * (likes - dislikes)
        if w < 0.1:
            w = 0.1
        weights.append(w)
    selected = weighted_sample_without_replacement(pool, weights, num)

    score = 0
    speed_bonus = 0
    total_possible = num
    correct_sequence = 0
    longest_streak = 0
    start_time = time.time()
    difficulty_counts = {}
    for i, q in enumerate(selected, start=1):
        print('')
        print(f'Question {i}/{num}  |  Category: {q.get("category","General")}  |  Difficulty: {q.get("difficulty","Medium")}')
        print(q['question'])
        qtype = q['type']
        ans = None
        timed_out = False
        time_limit = int(q.get('time_limit', 10))
        if qtype == 'multiple_choice':
            opts = q.get('options', [])
            labels = ['A', 'B', 'C', 'D', 'E']
            for idx_o, opt in enumerate(opts):
                label = labels[idx_o] if idx_o < len(labels) else str(idx_o+1)
                print(f'  {label}) {opt}')
            try:
                resp, elapsed, timed_out = get_input_timeout('Your answer: ', time_limit)
            except Exception:
                resp, elapsed, timed_out = '', time_limit, True
            resp = resp.strip().upper()
            if not timed_out and resp:
                # map letter to option
                letter_idx = ord(resp[0]) - ord('A')
                if 0 <= letter_idx < len(opts):
                    ans = opts[letter_idx]
                else:
                    ans = resp
        elif qtype == 'true_false':
            try:
                resp, elapsed, timed_out = get_input_timeout('[T]rue / [F]alse: ', time_limit)
            except Exception:
                resp, elapsed, timed_out = '', time_limit, True
            if not timed_out:
                resp = resp.strip().lower()
                if resp in ('t', 'true'):
                    ans = 'true'
                elif resp in ('f', 'false'):
                    ans = 'false'
                else:
                    ans = resp
        elif qtype == 'short_answer':
            try:
                resp, elapsed, timed_out = get_input_timeout('Answer: ', time_limit)
            except Exception:
                resp, elapsed, timed_out = '', time_limit, True
            ans = resp.strip()
        else:
            print('Unknown question type; skipping.')
            continue

        correct = False
        if timed_out:
            print('\nTime expired!')
        else:
            # check correctness
            correct_answer = q['answer']
            if qtype == 'short_answer':
                if ans.strip().lower() == str(correct_answer).strip().lower():
                    correct = True
            elif qtype == 'true_false':
                if str(ans).strip().lower() == str(correct_answer).strip().lower():
                    correct = True
            else:
                if str(ans).strip() == str(correct_answer).strip():
                    correct = True

        if correct:
            # speed bonus if answered in first half
            sb = 0
            if not timed_out and elapsed < (time_limit / 2.0):
                sb = 1
            score += 1 + sb
            speed_bonus += sb
            print(f'✓ Correct (+{1+sb}) — running score: {score}')
            correct_sequence += 1
            if correct_sequence > longest_streak:
                longest_streak = correct_sequence
        else:
            print(f'✗ Incorrect — correct answer: {q["answer"]}. running score: {score}')
            correct_sequence = 0

        # rating
        rating = ''
        while rating not in ('l', 'd', 's'):
            rating = input('Rate this question: [L]ike  [D]islike  [S]kip: ').strip().lower()
            if rating == 'l':
                user_fb = feedback.setdefault(username, {})
                entry = user_fb.setdefault(q['_index'], {'like': 0, 'dislike': 0})
                entry['like'] = entry.get('like', 0) + 1
                save_data(FEEDBACK_FILE, feedback)
            elif rating == 'd':
                user_fb = feedback.setdefault(username, {})
                entry = user_fb.setdefault(q['_index'], {'like': 0, 'dislike': 0})
                entry['dislike'] = entry.get('dislike', 0) + 1
                save_data(FEEDBACK_FILE, feedback)
            elif rating == 's':
                break
            else:
                print('Please enter L, D, or S.')

        # track difficulty counts
        d = q.get('difficulty', 'Medium')
        difficulty_counts[d] = difficulty_counts.get(d, 0) + 1

    total_time = time.time() - start_time
    percent = int((score / (total_possible or 1)) * 100)
    streak_bonus = longest_streak // 3
    total_with_streak = score + streak_bonus

    print('\n--- Session Summary ---')
    print(f'Score: {score} / {total_possible}  ({percent}%)')
    if len(difficulty_counts) > 1 or desired is None:
        print('Difficulty breakdown:')
        for k, v in difficulty_counts.items():
            print(f'  {k}: {v}')
    print(f'Streak bonus points earned: {streak_bonus}')
    print(f'Time taken: {int(total_time)} seconds')

    # personal average
    user_history = history.get(username, [])
    if user_history:
        avg = sum(h.get('percent', 0) for h in user_history) / len(user_history)
        if percent > avg:
            comp = 'above'
        elif percent < avg:
            comp = 'below'
        else:
            comp = 'equal to'
        print(f'This is {comp} your average of {avg:.0f}%')
    else:
        print('No prior history to compare.')

    # save session
    sess = {
        'date': datetime.datetime.utcnow().isoformat(),
        'score': score,
        'total': total_possible,
        'percent': percent,
        'time_seconds': int(total_time),
        'speed_bonus': speed_bonus,
        'streak_bonus': streak_bonus,
        'difficulty_counts': difficulty_counts,
    }
    history.setdefault(username, []).append(sess)
    save_data(HISTORY_FILE, history)


def view_stats(username, history):
    user_history = history.get(username, [])
    if not user_history:
        print('No history yet.')
        return
    total = len(user_history)
    avg = sum(h.get('percent', 0) for h in user_history) / total
    best = max(user_history, key=lambda h: h.get('percent', 0))
    print(f'Quizzes taken: {total}')
    print(f'Average score: {avg:.0f}%')
    print(f'Best session: {best.get("score")}/{best.get("total")} ({best.get("percent")}% ) on {best.get("date")}')
    print('\nRecent sessions:')
    for h in user_history[-5:]:
        print(f'  {h.get("date")}: {h.get("score")}/{h.get("total")} ({h.get("percent")}% )')


def main():
    questions = load_questions()
    users = load_data(USERS_FILE, {})
    history = load_data(HISTORY_FILE, {})
    feedback = load_data(FEEDBACK_FILE, {})

    print('Welcome to the Quiz App')
    username = login(users)

    while True:
        print('\nMain Menu')
        print('1) Start Quiz')
        print('2) View My Stats')
        print('3) Quit')
        sel = input('Choose: ').strip()
        if sel == '1':
            start_quiz(username, questions, feedback, history)
        elif sel == '2':
            view_stats(username, history)
        elif sel == '3':
            print(f'Goodbye {username}')
            sys.exit(0)
        else:
            print('Invalid selection.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted. Goodbye.')
        sys.exit(0)
