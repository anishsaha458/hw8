# Code Review — Quiz App

Date: 2026-03-30

Summary: This review compares `quiz.py` (the app) against the project `SPEC.md` and inspects `questions.json` and data handling. Each finding below is marked [PASS], [FAIL], or [WARN], and references specific files and line numbers in `quiz.py`.

1. [PASS] Missing question bank handling (SPEC 1)
	- File/lines: `quiz.py` lines 43–46 (`load_questions()`)
	- Notes: If `questions.json` is missing the app prints a clear error and exits with code 1.

2. [PASS] Account creation and non-plaintext password storage (SPEC 2)
	- File/lines: `signup()` and `login()` — `quiz.py` lines 96–104 and 121–126
	- Notes: Passwords are hashed with bcrypt and persisted; a created user can log in later.

3. [WARN] Persistence uses `pickle` (security concern)
	- File/lines: `load_data()` / `save_data()` — `quiz.py` lines 72–79 and 82–84
	- Why: `pickle` can execute arbitrary code when loading maliciously-crafted files. The spec requires non-human-readable storage, but `pickle` is not safe against tampering. Recommend JSON (or encrypted storage) and/or setting strict file permissions.

4. [PASS] Quiz flow: final summary and personal comparison present (SPEC 3)
	- File/lines: Summary printing and comparison in `start_quiz()` — `quiz.py` lines 315–336
	- Notes: Score, streak bonus, time taken, and a comparison to the user's average are printed.

5. [FAIL] Percentage calculation miscomputes when speed bonuses apply
	- File/lines: speed bonus added to `score` at `quiz.py` lines 273–279; percent computed at line 311
	- Issue: `percent = int((score / total_possible) * 100)` uses `score` which may include +1 speed bonuses, but `total_possible` equals number of questions. This allows percent > 100 and misrepresents correctness.
	- Recommendation: compute percent from base-correct count (exclude speed/streak bonuses) or compute relative to the defined maximum possible points (and document the rule). Ensure reported percent does not exceed 100.

6. [WARN] `total_with_streak` computed but not displayed
	- File/lines: `start_quiz()` lines 312–313 compute `total_with_streak`, but it's not printed.

7. [PASS] Feedback influences selection (SPEC 4)
	- File/lines: weight computation and sampling in `start_quiz()` and `weighted_sample_without_replacement()` — `quiz.py` lines 186–198 and 134–158
	- Notes: Likes increase weight, dislikes decrease it; disliked questions are less likely to be selected (floor 0.1 maintains some chance).

8. [WARN] When selecting all questions (k >= n) selection is not randomized
	- File/lines: `weighted_sample_without_replacement()` `if k >= len(items_copy): return items_copy` — `quiz.py` lines 138–139
	- Issue: returning the original list preserves deterministic order. If a user requests all questions, expect random order; instead consider returning a shuffled copy.

9. [PASS] Stats persistence across sessions (SPEC 5)
	- File/lines: session saved at `start_quiz()` lines 338–350; `view_stats()` reads history at lines 353–366 and `main()` loads at lines 369–374
	- Notes: History is appended and saved; data persists between runs (subject to the `pickle` caveat above).

10. [PASS] Timer expiry behavior (SPEC 6)
	 - File/lines: `get_input_timeout()` lines 28–40 and its use for questions (e.g., lines 221–224)
	 - Notes: A timed question raises a timeout and the app prints "Time expired!" and advances — it does not hang on macOS.

11. [WARN] `signal.alarm()` portability and edge-cases
	 - File/lines: `get_input_timeout()` lines 28–40
	 - Notes: Works on Unix/macOS but not on Windows. Also interacts poorly with multi-threading. Acceptable for macOS but mention platform limitation in docs.

12. [PASS] Speed bonus implemented (SPEC 7)
	 - File/lines: speed bonus logic at `quiz.py` lines 273–279; saved in session at 339–346
	 - Notes: A +1 bonus is awarded for answering within the first half of the allowed time; it is added to running score and saved in history. (See #5 for percentage implications.)

13. [WARN] Missing robust input EOF/interrupt handling
	 - File/lines: multiple `input()` and `getpass.getpass()` calls, e.g. `signup()` lines 87–105, `login()` lines 108–131, rating loop lines 288–304, main menu line 383
	 - Issue: `EOFError` (Ctrl-D) or unexpected stream closure may raise and crash the app. Suggest catching `EOFError` and `KeyboardInterrupt` around user input and exiting/handling gracefully.

14. [WARN] `load_data()` silently swallows loading errors
	 - File/lines: `load_data()` lines 72–79
	 - Issue: corrupted files cause the function to return `default` without notifying the user. Recommend printing/logging a warning so users know their data couldn't be loaded.

15. [WARN] Feedback keyed by question index — fragile across edits
	 - File/lines: `_index` assigned at `start_quiz()` lines 171–175; feedback stored using that index at lines 291–299
	 - Issue: If `questions.json` changes order or items shift, feedback will no longer map to the same question. Recommend adding a stable `id` field to each question and using it as the feedback key.

16. [WARN] `save_data()` doesn't enforce secure file permissions or atomic writes
	 - File/lines: `save_data()` lines 82–84
	 - Impact: Sensitive files (users/history/feedback) may be world-readable depending on umask. Suggest creating files with mode 0o600 and/or `os.chmod()` after write; consider atomic write via temp + rename.

17. [WARN] Repeated code and helper extraction opportunities (code quality)
	 - File/lines: repeated try/except around `get_input_timeout()` at lines 221–224, 234–237, 247–250; rating save duplication at 291–300
	 - Suggestion: factor repeated patterns (timed input, rating update) into helper functions to reduce duplication and centralize error handling.

18. [WARN] Weighted sampling algorithm: behavior and efficiency
	 - File/lines: `weighted_sample_without_replacement()` lines 134–158
	 - Notes: Implementation works but is O(k*n) and uses a non-standard fallback. Consider using a more standard approach (shuffle when k>=n, or use cumulative weights each pick). Also ensure reproducible randomness if desired.

19. [WARN] Minor normalization mismatch for multiple-choice answers
	 - File/lines: correctness checks at `quiz.py` lines 261–270
	 - Issue: multiple-choice comparison uses string equality (case-sensitive) while short_answer/true_false use `.lower()`. Recommend normalizing both sides for textual answers to avoid accidental mismatches (e.g., option capitalization/whitespace).

20. [WARN] Minor formatting/readability concerns
	 - File/lines: long f-strings and duplicated literal difficulty strings (e.g. `diff_map` at line 168, prints at lines 208–210)
	 - Suggestion: centralize constants (difficulty enum) and tidy formatting for maintainability.

Requirements coverage summary:
- AC 1 (missing JSON): PASS (lines 43–46)
- AC 2 (account creation/login non-plaintext): PASS (lines 96–126) — see WARN about `pickle` permissions
- AC 3 (quiz flow, summary, streak, comparison): PARTIAL — features present (lines 315–336) but FAIL on percent computation when speed bonuses exist (lines 273–279, 311)
- AC 4 (feedback influences selection): PASS (lines 186–198, 134–158)
- AC 5 (stats persistence): PASS (lines 338–350, 353–366) — see WARN about `pickle`
- AC 6 (timer expiry): PASS (lines 28–40 and usage)
- AC 7 (speed bonus): PASS (lines 273–279 and 339–346); percent handling needs fix.

Recommended prioritized fixes (small, high-value):
1. Fix percent calculation so percent represents correctness (exclude speed/streak bonus from percent OR compute against a documented max possible). A minimal change: track `correct_count` separately and use it for percent.
	- Files/lines: `start_quiz()` around lines 272–313.
2. Shuffle when `k >= n` in `weighted_sample_without_replacement()` so requesting all questions randomizes order.
	- Files/lines: `weighted_sample_without_replacement()` lines 134–139.
3. Add a warning/log when `load_data()` fails to unpickle (so corrupted data isn't silently ignored) and set secure permissions when writing data files.
	- Files/lines: `load_data()` / `save_data()` lines 72–84.

If you'd like, I can implement these three prioritized fixes and run a quick smoke test on macOS. I can also prepare a larger change to move from `pickle` to JSON (or encrypted JSON) for safer storage and add stable question IDs for feedback mapping.

---

