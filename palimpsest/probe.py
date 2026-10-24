"""Print the probability Decider gives each passage for 'says it replaces or revises an earlier rule'."""
from . import decider
from .gate import QUESTION
from .retrieve import load

for p in load("corpus"):
    ans, ms = decider.ask(p.text, QUESTION)
    print(f"{p.pid}: revises={ans['revises']['noul']:.2f}  ({ms:.0f} ms)", flush=True)
