
import base64
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Change only these settings.
MODEL = "muse-ember-1.0"
EFFORT = "max"
TESTS = None  # Example: ["tool_order", "tool_no_call"]. None = all 8 tests.
REPEATS = 1

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
client = OpenAI(base_url="https://api.meta.ai/v1", api_key=os.environ["MODEL_API_KEY"])
instructions = (ROOT / "instructions.txt").read_text(encoding="utf-8")
cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))

catalog = {"A12": {"price": 19.99, "stock": 12}, "B07": {"price": 7.50, "stock": 8}}
tools = [
    {"type": "function", "name": "lookup_item", "description": "Look up current SKU price and stock.",
     "parameters": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"type": "function", "name": "calculate_total", "description": "Calculate total AFTER checking stock.",
     "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": {
         "type": "object", "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}},
         "required": ["sku", "quantity"]}}}, "required": ["items"]}},
]


def use_tool(name, a):
    try:
        if name == "lookup_item":
            sku = a["sku"].upper()
            return {"sku": sku, **catalog[sku]}
        if name == "calculate_total":
            total = 0
            for item in a["items"]:
                sku, n = item["sku"].upper(), item["quantity"]
                if not 1 <= n <= catalog[sku]["stock"]:
                    return {"error": "Invalid quantity or insufficient stock"}
                total += catalog[sku]["price"] * n
            return {"total_usd": round(total, 2)}
    except (KeyError, TypeError, ValueError):
        pass
    return {"error": "Unknown tool or invalid arguments"}


def is_correct(case, answer, trace):
    if case["name"] == "tool_no_call":
        return not trace and answer.strip() == "READY"
    if case["name"] == "tool_order":
        lookups = [x for x in trace if x["name"] == "lookup_item"]
        totals = [x for x in trace if x["name"] == "calculate_total"]
        if not lookups or not totals:
            return False
        quantities = {i["sku"]: i["quantity"] for i in totals[0]["args"]["items"]}
        return ({x["args"]["sku"] for x in lookups} >= {"A12", "B07"}
                and max(x["turn"] for x in lookups) < min(x["turn"] for x in totals)
                and quantities == {"A12": 2, "B07": 3} and "62.48" in answer
                and totals[0]["result"] == {"total_usd": 62.48})
    extracted = json.loads(answer)
    return isinstance(extracted, dict) and all(extracted.get(k) == v for k, v in case["expected"].items())


def run(case):
    content = [{"type": "input_text", "text": case["prompt"]}]
    if case.get("image"):
        encoded = base64.b64encode((ROOT / case["image"]).read_bytes()).decode()
        content.append({"type": "input_image", "image_url": f"data:image/png;base64,{encoded}"})
    request = {"model": MODEL, "instructions": instructions, "reasoning": {"effort": EFFORT},
               "max_output_tokens": 6000, "input": [{"role": "user", "content": content}]}
    if case.get("type") in ("tool", "no_tool"):
        request["tools"] = tools

    start = time.perf_counter()
    trace, answer, error, finished = [], "", "", False
    inp = out = reasoning = api_calls = 0
    try:
        for turn in range(1, 6):  # At most 5 API requests per test.
            response = client.responses.create(**request)
            api_calls += 1
            if response.usage:
                inp += response.usage.input_tokens or 0
                out += response.usage.output_tokens or 0
                reasoning += getattr(response.usage.output_tokens_details, "reasoning_tokens", 0) or 0
            if response.status != "completed":
                raise RuntimeError(f"Response status: {response.status}")
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                answer, finished = response.output_text or "", True
                break
            outputs = []
            for call in calls:
                args = json.loads(call.arguments)
                result = use_tool(call.name, args)
                trace.append({"turn": turn, "name": call.name, "args": args, "result": result})
                outputs.append({"type": "function_call_output", "call_id": call.call_id,
                                "output": json.dumps(result)})
            request.update(input=outputs, previous_response_id=response.id)
        if not finished:
            raise RuntimeError("Too many tool calls")
        passed = is_correct(case, answer, trace)
    except Exception as exc:
        passed, error = False, str(exc)
    return {"name": case["name"], "passed": passed, "latency_s": round(time.perf_counter() - start, 3),
            "input_tokens": inp, "output_tokens": out, "reasoning_tokens": reasoning,
            "api_calls": api_calls, "tool_calls": len(trace), "answer": answer, "trace": trace, "error": error}


results = []
for _ in range(REPEATS):
    for case in cases:
        if TESTS is None or case["name"] in TESTS:
            result = run(case)
            results.append(result)
            print(f'{result["name"]}: {"PASS" if result["passed"] else "FAIL"} '
                  f'| {result["latency_s"]}s | tools={result["tool_calls"]}'
                  + (f' | ERROR: {result["error"]}' if result["error"] else ""))

if results:
    folder = ROOT / "results"
    folder.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {"accuracy": round(sum(r["passed"] for r in results) / len(results), 3),
               "avg_latency_s": round(sum(r["latency_s"] for r in results) / len(results), 3)}
    (folder / f"{stamp}.json").write_text(json.dumps({"model": MODEL, "effort": EFFORT,
        "instructions": instructions, "summary": summary, "results": results}, indent=2), encoding="utf-8")
    columns = ["name", "passed", "latency_s", "input_tokens", "output_tokens", "reasoning_tokens", "api_calls", "tool_calls", "error"]
    with (folder / f"{stamp}.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: r[k] for k in columns} for r in results)
    print("\nSummary:", summary, "\nReports saved to results/")
