# Palimpsest

Tags for this project: `#strands-decider-2b` `#context-memory`

A palimpsest is a manuscript that was scraped clean and written over. The old words are still faintly there underneath. Document folders work the same way. Someone updates a rule and the old file stays. Search returns both. The model reads both and writes one smooth answer that mixes the old number with the new one. It sounds sure and it is wrong.

Palimpsest puts a small decision in front of the model. A local Strands Decider 2B reads each pair of overlapping passages and answers a few yes or no questions about them. Code turns those answers and any printed dates into a verdict. If the evidence cannot settle it the agent says the sources conflict and a person decides. Amazon Bedrock only sees what survived.

## Does this already exist

Partly. Version aware retrieval is a known problem and papers like VersionRAG and TimelyRAG tackle it with version graphs and date filters. Many teams also tag old files as superseded by hand. Those routes need clean metadata. Palimpsest is for the messy case where the only evidence is the text itself. It also refuses to guess. You can run it in front of any of those systems.

## The decision pattern you can reuse

Decider 2B reads one passage at a time and answers one yes or no question.

Does this passage say it replaces or revises an earlier rule

It is asked once per passage and the answer is cached. Code does the rest. The rules live in `palimpsest/gate.py`.

1. A passage that names another one as replaced is settled in code and the model is never called.
2. With printed dates on both the later one is the newer. If the older passage claims to revise the newer one the verdict is a conflict.
3. If the newer passage says it revises the other the older one is dropped. If the newer one also says the rest stays in force both are kept and labelled base and amendment.
4. If neither says anything about revising and both belong to the same document the later date wins. Different documents with no sign that one replaces the other are a conflict.
5. With no dates the wording decides. If the wording does not settle it the verdict is a conflict.

I tried asking the model three more questions per pair. Whether two passages cover the same situation scored 0.07 to 0.17 even on pairs that plainly did. Whether the old rule stays in force was too close to call. Only the revising question separated the cases so that is the one decision the model owns. Everything else is code.

HIGH and LOW at the top of `gate.py` are 0.60 and 0.45. They come from a probe of five pairs on one laptop where the two passages that really revise a rule scored 0.67 and 0.82 and the rest scored 0.37 or lower. That is a tiny sample. Run `python -m palimpsest.probe` on your own documents and adjust them.

The wiring is one wrapped retrieval tool in `palimpsest/agent.py`.

```python
@tool
def search_policies(question: str) -> str:
    kept, verdicts = gate(question, top_k(question, PASSAGES), cache=CACHE)
    return render(kept, verdicts)
```

To use it in your own agent swap `top_k` for your retriever and pass `Passage` objects.

## Run it

```
pip install strands-decider strands-agents boto3
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8000 --device cpu
python -m palimpsest.probe
python app.py
python -m unittest discover -s tests
```

The demo opens at http://127.0.0.1:8080 after it finishes checking the sample pairs. For the benchmark and the agent set `BEDROCK_MODEL_ID` to the Nova Lite model or inference profile available in your region and run `python -m bench.run` or `python -m palimpsest.agent`.

Speed depends on your hardware. A GPU is far faster than a laptop CPU. Report your own numbers.

The decider server has no login. Leave it bound to 127.0.0.1.

## What I measured

On one Windows laptop with no GPU the model answered about 28 seconds per passage. The docs quote about 115 milliseconds on better hardware so your numbers will differ. Probing nine passages gave 0.88 and 0.67 for the two that revise a rule and 0.31 or lower for the other seven. The demo checks four pairs at startup and then answers every question instantly. I did not run the Nova Lite comparison in `bench/run.py` before the deadline so I make no claim about it.

## What to keep in mind

The sample documents and the starter cases in `bench/cases.py` are made up and written by hand. Twenty cases is a smoke test and not proof. Add more cases the model has never seen before you trust any number. Decider 2B is small and was trained mostly on English. Try it on your own documents first.

## Privacy

The decision model runs on your machine. The demo server stores nothing on disk and does not log what you ask. Only the passages that pass the gate go to Bedrock under your own AWS account.

Released under the MIT license.
