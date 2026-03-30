The app will build a command-line Python quiz app with a local login system from a JSON file, quizzes user, tracks scores and performance, statistics securely in a non-human readable format, and allows users to provide feedback on questions to influence future quiz selections and saves results. 

Behavior:
The app will greet the user in a friendly way with their login username and asks how many questions they want and randomly selects that many from the question bank

Data Format: 
The question bank should be a JSON file using the format below. 
{
  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics",
      "time_limit": 15
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures",
      "time_limit": 10
    },
    {
      "question": "What built-in function returns the number of items in a list?",
      "type": "short_answer",
      "answer": "len",
      "category": "Python Basics",
      "time_limit": 20
    },
    {
      "question": "Which of the following is used to handle exceptions in Python?",
      "type": "multiple_choice",
      "options": ["try/catch", "try/except", "catch/finally", "error/handle"],
      "answer": "try/except",
      "category": "Error Handling",
      "time_limit": 20
    },
    {
      "question": "What is the time complexity of looking up a key in a Python dictionary?",
      "type": "multiple_choice",
      "options": ["O(n)", "O(log n)", "O(1)", "O(n²)"],
      "answer": "O(1)",
      "category": "Data Structures",
      "time_limit": 25
    },
    {
      "question": "In Python, a generator function uses the 'yield' keyword instead of 'return'.",
      "type": "true_false",
      "answer": "true",
      "category": "Advanced Python",
      "time_limit": 15
    },
    {
      "question": "What dunder method is called when an object is created?",
      "type": "short_answer",
      "answer": "__init__",
      "category": "OOP",
      "time_limit": 20
    },
    {
      "question": "Which sorting algorithm has an average-case time complexity of O(n log n)?",
      "type": "multiple_choice",
      "options": ["Bubble Sort", "Insertion Sort", "Merge Sort", "Selection Sort"],
      "answer": "Merge Sort",
      "category": "Algorithms",
      "time_limit": 30
    },
    {
      "question": "Python's Global Interpreter Lock (GIL) prevents true multi-threaded CPU parallelism.",
      "type": "true_false",
      "answer": "true",
      "category": "Advanced Python",
      "time_limit": 25
    },
    {
      "question": "What decorator is used to create a context manager from a generator function?",
      "type": "short_answer",
      "answer": "contextmanager",
      "category": "Advanced Python",
      "time_limit": 30
    }
  ]
}

Main Menu
After login the user sees:
Start Quiz
View My Stats
Quit
Starting a Quiz

The app asks: How many questions would you like? 

The app asks: Choose difficulty: [1] Easy  [2] Medium  [3] Hard  [4] Any

The app randomly selects the requested number of questions, weighted by the
user's feedback history (liked questions appear more often; disliked questions
appear less often). Questions the user has never seen are weighted neutrally.
For each question the app:

a. Prints the question number, category, difficulty tag, and question text.

b. For multiple_choice: prints labelled options (A/B/C/D) and waits for a
single letter.

c. For true_false: prompts [T]rue / [F]alse.

d. For short_answer: accepts free text; comparison is case-insensitive and
strips leading/trailing whitespace.

e. After the user answers, prints ✓ Correct / ✗ Incorrect + the correct
answer, and the user's running score for this session.

f. Prompts: Rate this question: [L]ike  [D]islike  [S]kip
(response is recorded immediately).

After all questions, prints a summary:

Score (e.g., 7 / 10  (70%))
Difficulty breakdown if mixed mode was used
Streak bonus points earned (see Extension)
Time taken (total session time)
Comparison to the user's personal average: "This is above/below your average
of X%."

Returns to the Main Menu.

File Structure:
There should be a json file with in the question format

File Roles
FileHuman-readableContains
questions.json - should be human readable All quiz questions; edit freely to change subject matter
users.dat Not human readable (plaintext) + bcrypt password hashes
history.dat Not human readable  NoPer-user session records (scores, dates, streaks, difficulty)
feedback.dat Not human readable NoPer-user per-question like/dislike counts

Error Handling

1. questions.json is missing Print "Error: questions.json not found. Please create the question bank." and exit with code 1.

2. questions.json is present but malformed (invalid JSON or missing required fields)Print "Error: questions.json is malformed — <detail>." and exit with code 1.

3. questions.json has fewer questions than the user requestedPrint "Only <N> questions available. Running a <N>-question quiz instead." and continue.




The required features are a local login system for a username and password(or allow them to enter a new username and password). The passwords should not be easily discoverable.

A score history file that tracks performance and other useful statistics over time for each user. This specific file should not be easily readable and should be relatively secure.

Users should be able to provide feedback on whether they like a question or not, and should inform what questions they would like next

The questions should exist in their human-readable.json file so that they can be easily modified. Lets the project be used fo other classes.

None of code generated should require a backend, HTML, CSS, a graphical user interface, or the use of APIs. All should be local.

In addition to this, implement timed questions that give the user 10 seconds to answer a question


Quitting
Prints Goodbye <username> and exits

ACCEPTANCE CRITERIA:

1 — Missing question bank: Running the app when questions.json
does not exist prints a clear error message and exits with code 1 (verified
with echo $?).
2 — Account creation and login: A new user can create an account;
their password is not stored in plaintext anywhere on disk. The same user
can log back in successfully in a fresh session.
3 — Quiz flow completeness: A logged-in user can complete a full
quiz (any difficulty, any count) and see a final score, streak bonus,
and comparison to their personal average.
4 — Feedback influences selection: After disliking a question
multiple times, running another quiz of the same size draws that question
noticeably less often than unliked questions (manually testable with a
small question bank).
5 — Stats persistence: Session results appear correctly in "View My
Stats" after the quiz ends and after fully restarting the app.
6 — Timer expiry: On a timed question where no input is given before
the countdown reaches zero, the app prints the timeout message, marks the
question incorrect, and advances automatically — it does not hang.
7 — Speed bonus: Answering a timed question within the first half
of its allotted time awards a +1 speed bonus visible in both the live
score and the session summary.

