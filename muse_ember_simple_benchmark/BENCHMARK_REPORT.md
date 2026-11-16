# Muse Ember Max Benchmark Report

## 1. Benchmark Overview

This benchmark tests whether Muse Ember follows custom instructions, uses tools appropriately, fixes simple code, and extracts information from images. **All eight cases passed their automated checks in the single saved run.** This is a small functional check, not evidence of production reliability.

| Setting | Evidence |
|---|---|
| Model | Muse Ember, `muse-ember-1.0`, recorded in the result JSON |
| Reasoning effort | `max`, recorded in the result JSON and configured in code |
| API configuration | Current code uses the OpenAI Python client with `https://api.meta.ai/v1` and `client.responses.create` |
| Request limits | Current code sets `max_output_tokens=6000` per request and allows at most five API requests per case |
| Authentication | Environment-based credential; no credential values are included here |
| Coverage | Eight defined cases; eight saved executions, one per case; current settings are `TESTS=None`, `REPEATS=1` |
| Saved run | `20261116_140939`; filename timestamp has no recorded timezone |
| Evaluation | Deterministic checks in `is_correct`; no model judge or generated-code execution |

**Evidence:** [benchmark.py](benchmark.py), [cases.json](cases.json), [instructions.txt](instructions.txt), [saved JSON](results/20261116_140939.json), [saved CSV](results/20261116_140939.csv), and the four PNG inputs linked below. JSON and CSV metrics match; they represent the same eight executions and are counted once. The JSON also stores answers, executed-tool traces, model, effort, and instructions. API endpoint and request limits come from current code, rather than a saved request snapshot.

Every request includes the shared instructions: follow the task exactly, return only valid JSON when requested, use tools only when needed, check inventory before calculating prices, and never invent tool results or actions. Images are attached as base64 PNG inputs to the model; there is no separate OCR or vision tool.

For six cases, the evaluator parses the answer as a JSON object and checks the expected fields for equality. Extra fields are allowed. The two tool cases use custom checks described below. In this report, **PASS** means the automated check succeeded; **FAIL** means it returned false without an exception; **ERROR** means an exception was recorded; **NOT TESTED** means no saved execution exists. The script itself stores errors as `passed=false` plus an error string. All defined cases were tested; there are no failures or errors in this run.

**README discrepancy:** The README describes command-line flags, richer scores and per-check records, different filenames, and an absence of live runs. The current script has no argument parser, uses editable constants, and saves the simpler records analyzed here. This report follows the implementation and saved evidence.

## 2. Test Cases Explained

Shared instructions from Section 1 apply to every case. “No tools” below means no function definitions were supplied, and no function calls were recorded.

### Test Name: `tool_order`

- **Category:** Tool Calling / Inventory.
- **Objective:** Check tool selection, stock-before-price sequencing, arguments, and the final total.
- **Input:** Request for two units of A12 and three units of B07; a local catalog supplies price and stock.
- **Instructions:** Check stock for **both** SKUs before calculating; report USD; do not place an order.
- **Expected Behavior:** Look up both SKUs in earlier API turns than calculation, calculate the requested quantities, and report $62.48.
- **Actual Behavior:** Requested both lookups on turn 1, calculation on turn 2, and returned the correct stock, unit prices, and **$62.48 USD** on turn 3, followed by “No order placed.”
- **Tools Used:** Both tools available; `lookup_item` requested and executed twice, `calculate_total` once. No order-placement tool exists.
- **Result:** **PASS — 1/1.** The checker verifies lookup coverage, turn ordering, quantities, the first total result, and the presence of `62.48` in the answer. It does not fully validate the final prose.

### Test Name: `tool_no_call`

- **Category:** Tool Calling / Instruction Following.
- **Objective:** Test restraint when tools are available but unnecessary.
- **Input:** A greeting test explicitly described as unrelated to inventory.
- **Instructions:** Call no tools; reply exactly `READY` and nothing else.
- **Expected Behavior:** Empty tool trace and `READY` after trimming surrounding whitespace.
- **Actual Behavior:** Returned exactly `READY`; no tool requests or executions were recorded.
- **Tools Used:** `lookup_item` and `calculate_total` available; neither selected.
- **Result:** **PASS — 1/1.**

### Test Name: `instructions`

- **Category:** Classification / Instruction Following.
- **Objective:** Select the correct category and honor JSON-only formatting.
- **Input:** “I was charged twice for my October invoice.”
- **Instructions:** Classify as billing, bug, or feature; return only JSON with `category`.
- **Expected Behavior:** `{"category":"billing"}`.
- **Actual Behavior:** Returned exactly that JSON object.
- **Tools Used:** No tools.
- **Result:** **PASS — 1/1.**

### Test Name: `coding`

- **Category:** Coding / Arithmetic.
- **Objective:** Repair a discount function that returns the discount amount instead of the price after discount.
- **Input:** `def final_price(price, percent): return price * (percent / 100)` and examples `(100,20)`, `(80,12.5)`, `(18,100)`.
- **Instructions:** Return JSON containing `fixed_return_line` and `example_prices`.
- **Expected Behavior:** A corrected return expression and example prices `[80,70,0]`.
- **Actual Behavior:** Returned `"fixed_return_line": "return price * (1 - percent / 100)"` and `"example_prices": [80.0,70.0,0.0]`. The expression is consistent with the requested calculation.
- **Tools Used:** No tools; the generated code was not executed.
- **Result:** **PASS — 1/1.** Only `example_prices` is automatically checked. The checker does not validate the presence or correctness of `fixed_return_line`; Python numeric equality accepts the returned floats.

### Test Name: `vision`

- **Category:** Vision / Chart Understanding.
- **Objective:** Identify the largest bar and calculate its lead over the second largest.
- **Input:** [chart.png](samples/chart.png): North 20, South 35, East 15, West 50, in thousands of orders.
- **Instructions:** Return only JSON with `highest_region` and numeric `difference_from_second`.
- **Expected Behavior:** West; a difference of 15 thousand orders.
- **Actual Behavior:** `{"highest_region":"West","difference_from_second":15}`.
- **Tools Used:** No tools; direct image input.
- **Result:** **PASS — 1/1.**

### Test Name: `document`

- **Category:** Document Understanding / Extraction.
- **Objective:** Extract five invoice fields from an image.
- **Input:** [invoice.png](samples/invoice.png), showing Northwind Stationery, invoice INV-2026-014, blue pens and notebooks, and printed totals.
- **Instructions:** Return only JSON with invoice ID, vendor, subtotal, tax, and total.
- **Expected Behavior:** ID `INV-2026-014`, vendor `Northwind Stationery`, subtotal 37.5, tax 3.75, total 41.25.
- **Actual Behavior:** Returned all five expected fields and values as valid JSON.
- **Tools Used:** No tools; direct image input.
- **Result:** **PASS — 1/1.** Line-item extraction and independent invoice reconciliation were not evaluated.

### Test Name: `counting`

- **Category:** Vision / Object Counting.
- **Objective:** Count all objects of two specified shapes and colors.
- **Input:** [counting.png](samples/counting.png): two rows of six orange circles, six blue squares in a row, and one additional square below.
- **Instructions:** Return only JSON with integer `orange_circles` and `blue_squares`.
- **Expected Behavior:** 12 circles and 7 squares.
- **Actual Behavior:** `{"orange_circles":12,"blue_squares":7}`.
- **Tools Used:** No tools; direct image input.
- **Result:** **PASS — 1/1.**

### Test Name: `ocr`

- **Category:** OCR / Text Extraction.
- **Objective:** Read exact identifying text from a delivery label.
- **Input:** [ocr.png](samples/ocr.png), a clear label containing a tracking ID and destination.
- **Instructions:** Return only JSON with `tracking_id` and `destination`.
- **Expected Behavior:** `TRK-2048-XQ` and `Alexandria`.
- **Actual Behavior:** `{"tracking_id":"TRK-2048-XQ","destination":"Alexandria"}`.
- **Tools Used:** No tools; direct image input.
- **Result:** **PASS — 1/1.**

## 3. Tool Calling Analysis

Both tool scenarios expose the same two function definitions. `lookup_item(sku)` reads current price and stock from an in-memory catalog. `calculate_total(items)` checks requested quantities against that catalog and sums prices. Both are local, read-only functions dispatched by `use_tool`; neither places orders or contacts an inventory service.

### Inventory execution sequence

User request → Model requests two lookups → Python executes both → Results returned → Model requests calculation → Python executes calculation → Result returned → Model gives final answer.

| API turn | Model request and arguments | Benchmark execution and output returned to model |
|---|---|---|
| 1, first call | `lookup_item({"sku":"A12"})` | `{"sku":"A12","price":19.99,"stock":12}` |
| 1, second call | `lookup_item({"sku":"B07"})` | `{"sku":"B07","price":7.5,"stock":8}` |
| 2 | `calculate_total({"items":[{"sku":"A12","quantity":2},{"sku":"B07","quantity":3}]})` | `{"total_usd":62.48}` |
| 3 | No function request | Final answer reports both stocks and prices, $62.48 USD, and no order placed |

The two lookups were requested in the same response and executed sequentially by Python in the recorded order. They are two tool calls, not two API calls. The benchmark decodes each request's JSON arguments, executes the local function, records its output, and sends it back as `function_call_output`. Follow-up requests use `previous_response_id` and retain the shared instructions and tool definitions.

All three recorded calls returned successful results. Both stock checks preceded calculation in a separate API turn, arguments matched the request, and no unnecessary calls appeared. The calculation is `2 × 19.99 + 3 × 7.50 = 62.48`. The final response agrees with these outputs and the user instructions.

The calculator's quantity check does **not** enforce that prior lookups occurred. That sequencing requirement is evaluated separately from the trace. Tool execution success alone would therefore not establish a passing answer.

### No-call execution sequence

Greeting request → Model returns `READY` → No local tool execution.

This used one API call. There are no arguments, tool outputs, or execution order to inspect because neither available tool was selected. The answer and empty trace both satisfy the test.

## 4. Benchmark Results Comparison

Pass rate is passing executions divided by saved executions for each case. Averages are arithmetic means over those executions, including any failures or errors if present. Each case has only one execution, so its average equals its recorded measurement. The overall row gives equal weight to all eight executions. Values are rounded to three decimal places where needed.

| Test Case | Accuracy / Pass Rate | Avg Latency (s) | Avg Input Tokens | Avg Output Tokens | Avg Tool Calls | Result |
|---|---|---|---|---|---|---|
| tool_order | 100% (1/1) | 14.273 | 2529 | 801 | 3 | PASS |
| tool_no_call | 100% (1/1) | 0.961 | 648 | 108 | 0 | PASS |
| instructions | 100% (1/1) | 1.887 | 102 | 262 | 0 | PASS |
| coding | 100% (1/1) | 1.360 | 155 | 545 | 0 | PASS |
| vision | 100% (1/1) | 1.906 | 1151 | 118 | 0 | PASS |
| document | 100% (1/1) | 1.492 | 1468 | 432 | 0 | PASS |
| counting | 100% (1/1) | 1.006 | 1182 | 184 | 0 | PASS |
| ocr | 100% (1/1) | 1.278 | 551 | 104 | 0 | PASS |
| **Overall** | **100% (8/8)** | **3.020** | **973.250** | **319.250** | **0.375** | **8 PASS; 0 FAIL; 0 ERROR** |

| Test Case | Avg API Calls | Avg Reasoning Tokens |
|---|---|---|
| tool_order | 3 | 501 |
| tool_no_call | 1 | 98 |
| instructions | 1 | 248 |
| coding | 1 | 499 |
| vision | 1 | 94 |
| document | 1 | 377 |
| counting | 1 | 159 |
| ocr | 1 | 75 |
| **Overall** | **1.250** | **256.375** |

Totals: **24.163 seconds** summed case latency, **7,786 input tokens**, **2,554 output tokens**, **2,051 reasoning tokens**, **10 API calls**, and **3 executed tool calls**. Reasoning tokens are an output-token detail, not an additional amount to add to output tokens.

Latency covers each case's API loop, local tool execution, and correctness check; image reading/encoding occurs before timing starts. Tokens are summed from usage across API responses, not unique prompt text. API calls count responses returned successfully to the script; tool calls count recorded local executions. Separate tool durations, API-turn timings, monetary cost, and latency variability are **Not reported**. The script substitutes zero for missing usage details, but every saved case here has a positive reasoning-token value.

The inventory case accounts for approximately **59.1%** of summed latency and has the highest input/output token usage. It also has three API calls versus one for every other case. The seven cases without executed tools average **1.413 seconds**. These observations do not isolate the cost of tool execution from model processing or network time.

## 5. Tool Comparison

Counts below cover all eight saved executions. A successful execution means the local function returned a normal result rather than an error object.

| Tool | Purpose | Times Called | Successful Executions | Errors | Observations |
|---|---|---|---|---|---|
| `lookup_item` | Read a SKU's price and stock | 2 | 2 | 0 | A12 then B07 on turn 1; both required and correctly selected |
| `calculate_total` | Validate quantities against stock and calculate USD total | 1 | 1 | 0 | Called on turn 2 with quantities 2 and 3; returned 62.48 |

Lookup accepts a required string `sku`; calculation accepts a required `items` array containing SKU strings and integer quantities. Lookup returns individual catalog data; calculation returns an aggregate total or an error. No incorrect selection, invalid arguments, ordering problems, or unnecessary calls appear in the saved trace. Neither tool was used in the greeting test.

Unknown SKUs, malformed arguments, insufficient stock, and recovery from tool errors are **NOT TESTED**. Although the implementation contains error paths, this run provides no evidence of how the model responds to them. The 3/3 execution success rate is separate from the model's 8/8 case pass rate.

## 6. Key Findings

- **Accuracy is tied:** All cases passed once; none can be ranked above another for reliability. There were no observed failures, but no repetitions from which to measure inconsistency.
- **Fastest and lowest usage differ:** `tool_no_call` was fastest at 0.961 seconds; `instructions` used the fewest input tokens (102); `ocr` used the fewest output tokens (104) and reasoning tokens (75).
- **Tool calling worked in the tested paths:** The model selected the correct functions and quantities, waited for both stock lookups, used actual returned values, and avoided tools when instructed. Only one positive tool workflow and one no-call workflow were tested.
- **Custom instructions were followed in the saved answers:** All six JSON cases returned valid JSON, the greeting returned exactly `READY`, and the inventory response agreed with the tool outputs. More difficult or conflicting instructions were not evaluated.
- **Max effort produced correct checked answers here:** This supports success on these inputs, not a general reliability claim. No other effort levels or models were tested, so no comparative advantage can be inferred.
- **Coverage and evaluator limits matter:** Inputs are simple and clean. Coding checks only example values, image cases check selected fields, and JSON checks allow extra keys without strict schema/type validation. Broader coding competence, robust perception, and full instruction compliance are not established by these passes.

## 7. Final Conclusion

Muse Ember with Max reasoning handled this small set of structured extraction, basic visual interpretation, classification, discount arithmetic, and controlled tool use successfully. The observed performance tradeoff is the inventory workflow's higher latency and token usage. No incorrect answer was observed under the existing checks, but the single execution per case and limited evaluator coverage leave reliability uncertain.

**The evidence is insufficient for a production recommendation.** Next, repeat cases to measure stability and latency distribution; expand to representative workload inputs and degraded or complex images; execute and test generated code; enforce stricter output schemas; and exercise invalid tool arguments, insufficient stock, tool failures, and recovery. Compare effort levels and models under the same conditions before drawing efficiency or quality conclusions. This report used existing files only; no new benchmark or paid API request was run.
