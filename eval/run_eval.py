"""
Run a question set against the chat API and score it

    python -m <module_name> ~ takes module name without the .py extension
    python -m eval.run_eval --api http://127.0.0.1:8000 --questions eval/questions.examples.jsonl
    python -m eval.run_eval ... --judge                 # also grade answers against reference answers
    python -m eval.run_eval ... --judge --gate          # exit 1 if any threshold is missed (CI)


Each line of the questions file is JSON:
    - reference --> used by --judge
    - expected_sources --> any of these in a cited title or URL = hit

Scores:
    - source hit rate   cited sources include an expected one       (should_answer questions)
    - answer rate       the bot answered with citations             (should_answer questions)
    - decline rate      the bot declined instead of answering       (should_answer = false)
    - correctness       1-5 from the judge model vs the reference   (--judge)
"""


