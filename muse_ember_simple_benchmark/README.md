# Muse Ember Max — Simple Instructions + Tool Calling Benchmark

One script, one editable instructions file, one editable cases file, and four small sample images. There is **no LangChain, agent framework, database, Docker, or UI**.

## Setup (Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set your real `MODEL_API_KEY` in `.env`. Never commit or share the key.

## Edit your benchmark

- **`instructions.txt`** — your developer-level instructions; these are passed via Meta's Responses API `instructions=` on *every API turn*.
- **`cases.json`** — edit prompts, expected values, image path, or add another JSON test case.
- **`benchmark.py`** — contains only two local read-only tools: `lookup_item(sku)` and `calculate_total(items)`; replace these if benchmarking your own tools. Tool calling is real: the model picks a function, Python runs it locally, and the result is sent back to the model.

**Reasoning:** Every API request explicitly sends `reasoning={"effort": "max"}` by default. You can override it with `--effort` to compare settings.

## Run

```powershell
python benchmark.py
python benchmark.py --tests tool_order,tool_no_call
python benchmark.py --tests vision,document,counting,ocr
python benchmark.py --repeats 3
python benchmark.py --instructions instructions.txt --effort max
```

## Results

Files are saved after every run to `results/benchmark_<timestamp>.json` (full details and tool trace) and `.csv` (one row per test).

Each test saves: `score`, `passed`, total `latency_seconds`, `api_turns`, `tool_calls`, `input_tokens`, `output_tokens`, `reasoning_tokens` (if provided by API), raw final answer, per-check results, and errors. Summary includes average score, pass rate, and total tokens and elapsed time. A **score is just the fraction of the built-in checks passed**, not a standardized benchmark or a judge of all valid answers. The coding case checks its numerical examples, not execution of AI-generated code.

A *tool* test checks stock lookup before calculation, correct calculated total, and final answer; a *no-tool* test checks the model does not needlessly call tools. These tools only read an in-memory fake catalog and never execute arbitrary model-generated code.

**Note:** No live calls have been made here because the API key is only on your computer. Some third-party hosting routes may not accept `previous_response_id`, which this example uses for Meta's official Model API.

## Documentation

- [Meta Muse Ember](https://dev.meta.ai/docs/muse-ember)
- [Meta Responses API — instructions](https://dev.meta.ai/docs/protocols/responses)
- [Meta Tool Calling](https://dev.meta.ai/docs/tool-calling)
- [Meta Reasoning](https://dev.meta.ai/docs/reasoning)
