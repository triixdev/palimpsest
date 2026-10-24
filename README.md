# Palimpsest

`#strands-decider-2b` `#context-memory`

**Palimpsest stops your AI from mixing the old rule with the new one. When it cannot tell which one counts it says so and asks a person.**

**Live demo:** https://triixdev.github.io/palimpsest/ replays a real run. The gate and retriever are the project code and the Decider 2B scores were recorded on my laptop. Run the project locally to ask your own questions.

A palimpsest is a manuscript that was scraped clean and written over. The old words still show faintly underneath. Document folders work the same way. Someone updates a rule and the old file stays. Search returns both. The model reads both and blends the old number with the new one. It sounds sure and it is wrong.

A small local model called Strands Decider 2B reads each pair of overlapping passages and answers one yes or no question. Plain code turns that answer and any printed dates into a verdict. **Amazon Bedrock only sees what survived.**

## Does this already exist

Partly. VersionRAG is a research system that tracks versions with a graph. Many teams also tag old files as superseded by hand. Both need clean metadata. Palimpsest works when the only evidence is the text itself. It also refuses to guess. You can run it in front of any of them.

## How the decision works

Decider reads one passage and answers one question.

Does this passage say it replaces or revises an earlier rule

It is asked once per passage and the answer is cached. Code does the rest. The rules live in `palimpsest/gate.py`.

1. A passage that names another one as replaced is settled by code. The model is never called. If the naming passage is dated earlier the verdict is a conflict.
2. When both passages have dates the later one is newer. If the older passage claims to revise the newer one the verdict is a conflict.
3. If the newer passage says it revises the other the older one is dropped. If it also says the rest stays in force both are kept and labelled base and amendment.
4. If neither passage mentions revising and both share a document title the later date wins. Passages without a title or with different titles are a conflict.
5. With no dates the wording decides. If the wording is unclear the verdict is a conflict.

I tried three more questions per pair. Whether two passages cover the same situation scored 0.07 to 0.17 even on pairs that clearly did. Whether the old rule stays in force was too close to call. Only the revising question separated the cases. That is the one decision the model owns and code handles everything else.

HIGH and LOW in `gate.py` are 0.60 and 0.45. They come from a small probe on one laptop. The two passages that really revise a rule scored 0.67 and 0.88 and the other seven scored 0.31 or lower. That is a tiny sample. Run `python -m palimpsest.probe` on your own documents and adjust them. The static demo in `docs/` is built by `python make_static.py` from those recorded scores.

The wiring is one wrapped retrieval tool in `palimpsest/agent.py`.

```python
@tool
def search_policies(question: str) -> str:
    kept, verdicts = gate(question, top_k(question, PASSAGES), cache=CACHE)
    return render(kept, verdicts)
```

To use it in your own agent swap `top_k` for your retriever and pass `Passage` objects. If the decider is down the real tool returns a message that tells the agent to ask a person.

## Run it

```
pip install strands-decider strands-agents boto3
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8000 --device cpu
python -m palimpsest.probe
python app.py
python -m unittest discover -s tests
```

The demo opens at http://127.0.0.1:8080 after it checks the sample pairs. For the benchmark and the agent set `BEDROCK_MODEL_ID` to the Nova Lite model or inference profile in your region. Then run `python -m bench.run` or `python -m palimpsest.agent`.

The decider server has no login. Keep it on 127.0.0.1 and never start it with `--host 0.0.0.0`.

## What I measured

On one Windows laptop with no GPU the model took about 28 seconds per passage. A GPU is far faster so report your own numbers. The demo checks four pairs at startup and then answers every question instantly. **The Bedrock agent in `palimpsest/agent.py` is written but I could not run it end to end. My AWS account could not call Bedrock before the deadline. I also did not run the Nova Lite comparison so I make no claim about it.** The gate and the demo and the tests all ran. `python -m palimpsest.agent --dry-run` prints exactly what Bedrock would receive.

## What to keep in mind

The sample documents and the starter cases in `bench/cases.py` are invented. Twenty cases is a smoke test. Add more cases the model has never seen before you trust any number. The bench prints accuracy and wrong version rate and lost passage rate and how often a method guessed when it should have abstained. Decider 2B is small and trained mostly on English. Try it on your own documents first.

## Privacy

The decision model runs on your machine. The demo server stores nothing and logs no questions. Only passages that pass the gate go to Bedrock under your own AWS account.

Released under the MIT license.
