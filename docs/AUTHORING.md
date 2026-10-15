# Authoring Guide

How lesson, project, and reference pages in `docs/` are built. The live gallery of every component is
`docs/authoring/components.html` (`pixi run serve`, then open `/authoring/components.html`).

`pixi run check-site` validates links, anchors, quizzes, exercise test blocks, and visualizer names. It must pass.

## Page skeleton

Module pages live at `docs/modules/<id>-<slug>.html` with the exact `href` from `docs/assets/js/curriculum.js`.
Project pages live at `docs/projects/`, reference pages at `docs/reference/`. All use `data-root="../"`.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M05 · Functions · Python Practicum</title>
<link rel="stylesheet" href="../assets/css/course.css">
<script src="../assets/js/curriculum.js"></script>
<script src="../assets/js/viz.js" defer></script>
<script src="../assets/js/viz-ds.js" defer></script>
<script src="../assets/js/viz-algo.js" defer></script>
<script src="../assets/js/viz-data.js" defer></script>
<script src="../assets/js/course.js" defer></script>
</head>
<body data-root="../" data-module="m05">
<main class="lesson">
  <header class="lesson-hero">
    <p class="eyebrow">Part 1 · Foundations · Module 05</p>
    <h1>Functions</h1>
    <p class="lede">One or two sentences on why this matters.</p>
    <div class="lesson-meta"><span>⏱ ~2.5 hours</span><span>Prerequisites: <a href="m04-control-flow.html">M04</a></span></div>
    <ul class="objectives"><li>…</li></ul>
  </header>
  <section class="lesson-section" id="some-topic"><h2>Some topic</h2> … </section>
  …
</main>
</body>
</html>
```

`course.js` wraps `<main>` with the header, sidebar, table of contents (built from each
`section.lesson-section[id] > h2`), the "Mark complete" box, notes, and previous/next links. Do not write those yourself.
Project pages use `data-module="p01"` (the manifest id) so completion tracking works; reference pages use
`data-page="ref-py315"` etc.

## Required module structure

1. Hero: eyebrow, `h1`, lede, meta (time and prerequisites), objectives (4–7 items).
2. Six to ten teaching sections. Each one explains the idea in plain language, shows a worked example, and makes the
   learner do something: a runnable cell, a `data-predict` cell, a tracer, a visualizer, or a "think" callout.
3. `id="practice"`: three to six graded exercises, from easy to hard.
4. `id="mini-project"`: a `.project-box` with a small build the learner does locally with Pixi
   (spec, acceptance criteria as a `.checklist`, stretch goals).
5. `id="quiz"`: an end-of-module quiz of 10–15 questions mixing `single`, `multi`, `output`, and `text`.
6. `id="recap"`: a summary list, flashcards (8–12 cards), and "Going further" links to docs.python.org and similar.

Write for a motivated beginner who becomes a professional: define every term on first use, explain *why* as well as
*how*, show common mistakes, and finish each section with what to remember. Aim for the depth of a good textbook chapter.

## Components

### Static code

```html
<pre><code class="language-python">x = 1 &lt; 2</code></pre>
<pre data-label="Terminal"><code class="language-bash">pixi run python app.py</code></pre>
```

Escape `<`, `>`, and `&` inside `<pre>`. Languages: python, bash, toml, yaml, json, sql, ini, diff.

### Runnable cells (Pyodide, real CPython 3.14 in the browser)

```html
<div class="runnable" data-title="Try it">
<textarea>
print("hello")
</textarea>
</div>
```

- Code inside `<textarea>` is written literally (no escaping) and dedented automatically. Never write `</textarea>`.
- `data-predict`: the learner must type a prediction, then Run compares it to the real output.
- `data-stdin="line1\nline2"`: lines fed to `input()`.
- `data-autorun`: run on page load (use sparingly).
- `data-python="3.15"`: Python 3.15-only code. It is shown highlighted with instructions to run locally via
  `pixi exec --spec "python=3.15" python file.py`.
- `data-local="reason"`: code that cannot run in the browser (threads needing real parallelism, multiprocessing,
  subprocess, sockets/network, `asyncio.run` with real I/O, packages missing from Pyodide such as torch, polars,
  duckdb, httpx, fastapi, structlog). The reason is shown to the learner.
- Browser packages that load automatically on import: numpy, scipy, pandas, scikit-learn, matplotlib, and the stdlib.
- matplotlib figures are rendered automatically after the cell finishes. Do not call `plt.show()`; it's unnecessary.
- `asyncio`: use top-level `await main()` in browser cells and explain that local scripts use `asyncio.run(main())`.

### Step-through tracer

```html
<div class="tracer" data-title="Watch the recursion">
<textarea>
def fact(n):
    return 1 if n == 0 else n * fact(n - 1)
result = fact(4)
</textarea>
</div>
```

Records every line, call, and return; shows frames, locals, changed values, and object-identity tags (two names with
the same "obj N" tag point to the same object). Keep programs small (under 1500 steps). Optional `data-stdin`.

### Exercises (auto-graded in the browser)

```html
<div class="exercise" data-id="m05-e1" data-title="Write is_even">
  <div class="exercise-prompt"><p>Task description…</p></div>
<textarea class="starter">
def is_even(n):
    ...
</textarea>
  <script type="text/x-python" class="tests">
def test_even():
    assert is_even(4) is True, "is_even(4) should be True"
def test_prints():
    assert program_output.strip() == "ready", "print exactly 'ready'"
  </script>
  <details class="hint"><summary>Hint</summary><p>…</p></details>
  <details class="solution"><summary>Show solution</summary><pre><code class="language-python">…</code></pre></details>
</div>
```

- `data-id` must be unique across the site: `<module id>-e<n>` (for example `m05-e3`).
- Tests are `test_*` functions that run in the learner's namespace after their code. Every assert carries a helpful
  message. `program_output` holds everything the learner's code printed. `capture_output(func, *args, stdin=None)`
  returns `(result, printed_text)`. Tests must not contain `</script>`.
- Verify each solution passes its tests (paste both into `pixi run python` locally).

### Quizzes

```html
<div class="quiz" data-id="m05-quiz">
<script type="application/json">
{"title": "Functions quiz", "passScore": 0.7, "questions": [
  {"type": "single", "prompt": "HTML allowed", "code": "optional python shown above options", "options": ["a", "b"], "answer": 1, "explanation": "<p>Why.</p>"},
  {"type": "multi", "prompt": "…", "options": ["…", "…", "…"], "answer": [0, 2], "explanation": "…"},
  {"type": "output", "prompt": "What does this print?", "code": "print(1 + 1)", "answer": "2", "explanation": "…"},
  {"type": "text", "prompt": "Which keyword…?", "answer": ["def"], "explanation": "…"}
]}
</script>
</div>
```

The payload must be strict JSON (double quotes, no trailing commas, `\n` for newlines inside strings). `answer` is a
0-based index (`single`), a list of indexes (`multi`), or the exact text/accepted list (`output`/`text`; `text` is
case-insensitive). Every question needs an `explanation` that teaches, not just says "correct".

### Callouts, tags, and layout helpers

```html
<aside class="callout note|tip|warn|danger|py314|py315|pixi|pro|think"><p>…</p></aside>
<aside class="callout note" data-title="Custom heading"><p>…</p></aside>
<span class="tag v314">3.14</span> <span class="tag v315">3.15</span> <span class="tag pixi">pixi</span>
<div class="two-col">…</div>   <div class="card-grid"><div class="card"><h4>…</h4>…</div></div>
<div class="tabs"><div class="tab" data-label="Version A">…</div><div class="tab" data-label="Version B">…</div></div>
<details class="reveal"><summary>Reveal</summary>…</details>
<ul class="checklist" data-id="m05-mini">…</ul>          (persisted checkboxes; unique data-id)
<pre class="mermaid">flowchart LR; A-->B</pre>          (Mermaid diagrams)
<figure class="figure"><svg class="diagram" viewBox="…">…</svg><figcaption>…</figcaption></figure>
```

Inline SVG diagrams should use CSS variables for color (`fill="var(--viz-1)"`, `stroke="var(--fg-muted)"`) so they work
in light and dark themes.

### Project box

```html
<div class="project-box">
  <div class="widget-head"><span class="w-kind">Mini-project</span><span class="w-title">Title</span></div>
  <div class="widget-body"> spec, steps, <ul class="checklist" data-id="m05-mini">…</ul> </div>
</div>
```

### Visualizers

```html
<div class="viz" data-viz="NAME" data-config='{"key": "value"}'></div>
```

`data-config` is optional JSON. Available visualizers (`viz-ds.js`, `viz-algo.js`, `viz-data.js`):

| Name | Purpose | Config (all optional) |
|---|---|---|
| `references` | Names → objects diagrams for aliasing, copying, and mutation | `scenario`: `alias` \| `rebind` \| `copy` \| `deepcopy` \| `immutable` \| `default-arg` \| `nested` |
| `bigo` | Growth-rate chart and operation counts | `functions`: subset of `["1","log n","n","n log n","n^2","n^3","2^n","n!"]`, `maxN` |
| `dynamic-array` | `append` with capacity growth and copy cost (amortized O(1)) | `growth` (factor, default 1.125 like CPython or 2) |
| `linked-list` | Insert, delete, search, and reverse with pointer animation | `values`, `doubly` |
| `stack-queue` | Push/pop, enqueue/dequeue, deque operations | `mode`: `stack` \| `queue` \| `deque`, `values` |
| `hash-table` | Hashing, buckets, collisions, probing, load factor, resize | `size`, `strategy`: `chaining` \| `linear` \| `python` |
| `bst` | BST insert/delete/search, traversals, AVL rotations | `values`, `avl` |
| `heap` | Binary heap tree plus array view with sift-up/down | `kind`: `min` \| `max`, `values` |
| `trie` | Insert and prefix search | `words` |
| `union-find` | Union by rank with path compression | `n` |
| `lru-cache` | Hash map plus doubly linked list LRU eviction | `capacity` |
| `bloom-filter` | Bit array with k hashes and false positives | `m`, `k` |
| `matrix` | Matrix/vector ops: dot product, matrix multiply, transpose, broadcasting | `op`: `dot` \| `matmul` \| `transpose` \| `broadcast` |
| `sorting` | Bar animation of sorts with comparison and swap counters | `algorithms`: subset of `["bubble","insertion","selection","merge","quick","heap","counting","radix"]`, `default`, `size`, `array` |
| `binary-search` | Binary vs linear search, step by step | `array`, `target` |
| `array-technique` | Two pointers, sliding window, prefix sums | `technique`: `two-sum-sorted` \| `sliding-window` \| `prefix-sum`, `array`, `target`, `k` |
| `recursion-tree` | Call tree with optional memoization | `fn`: `fib` \| `factorial` \| `hanoi` \| `permutations` \| `merge-sort` \| `power-set`, `n`, `memo` |
| `graph` | BFS, DFS, Dijkstra, Bellman-Ford, topological sort, Prim, Kruskal | `preset`: `small` \| `weighted` \| `dag` \| `grid`, `algorithms`, `start` |
| `grid-path` | Draw walls, then BFS, DFS, Dijkstra, greedy, A* | `rows`, `cols`, `algorithms` |
| `dp-table` | Table filling with dependencies and traceback | `problem`: `lcs` \| `edit-distance` \| `knapsack` \| `coin-change` \| `lis` \| `grid-paths`, plus inputs (`a`, `b`, `items`, `capacity`, `coins`, `amount`, `array`) |
| `n-queens` | Backtracking search with pruning | `n` |
| `bits` | Integer bits with bitwise operators, plus IEEE-754 float view | `value`, `width`, `mode`: `int` \| `float` |
| `kmp` | KMP failure table and matching | `text`, `pattern` |
| `huffman` | Huffman tree construction and codes | `text` |
| `event-loop` | asyncio event loop timeline vs sequential vs threads | `scenario`: `sequential` \| `asyncio` \| `threads` |
| `gradient-descent` | 1-D/2-D loss surface with learning-rate slider | `fn`: `quadratic` \| `bowl` \| `rosenbrock`, `lr` |
| `kmeans` | k-means iterations on 2-D points | `k`, `points` |
| `neural-net` | Small feed-forward net forward pass and weights | `layers` |
| `pipeline` | Data-pipeline stages with records flowing through (ETL) | `stages` |

Additional optional keys (every visualizer also accepts `title`):

- `sorting`: `default` picks the first algorithm; learners choose a second one in the widget's "race vs" menu to race
  two algorithms on the same array.
- `array-technique`: `technique: "longest-substring"` with `text`; `queries` (inclusive `[lo, hi]` pairs) for `prefix-sum`.
- `graph`: `start` is a vertex name such as `"A"`; topological sort is `topo`; `default` picks the first algorithm.
- `grid-path`: `default`, `walls` (list of `[row, col]`).
- `dp-table`: `rows`, `cols`, `blocked` for `grid-paths`. `n-queens`: `all` (find all solutions). `bits`: `op`.
- `event-loop`: `build` (`gil` | `free-threaded`), `workload` (`io` | `cpu`). `gradient-descent`: `momentum`.
- `kmeans`: `init` (`random` | `kmeans++`). `neural-net`: `mode` (`forward` | `train`).
- `pipeline`: `mode` (`batch` | `streaming`), `write` (`append` | `upsert`).

The galleries `/authoring/viz-ds.html`, `/authoring/viz-algo.html`, and `/authoring/viz-data.html` show every
visualizer with sample configs.

## Python 3.14 and 3.15 content

Teach Python 3.14 as the current version. Where relevant, include a `callout py314` for 3.14 features and a
`callout py315` plus `data-python="3.15"` cells for 3.15. Facts to use:

**3.14:** PEP 750 template strings (`t"..."`, `string.templatelib`); PEP 649/749 deferred evaluation of annotations
(`annotationlib`); PEP 758 `except A, B:` without parentheses; PEP 765 warnings for `return`/`break`/`continue` in
`finally`; PEP 779 free-threaded build officially supported; PEP 734 `concurrent.interpreters` and
`InterpreterPoolExecutor`; PEP 784 `compression.zstd`; PEP 768 safe external debugger attach (`python -m pdb -p PID`);
asyncio introspection (`python -m asyncio ps PID` / `pstree`); syntax highlighting and color in the REPL and in
unittest/argparse output; `heapq.heapify_max`, `heappush_max`, `heappop_max`, `heappushpop_max`, `heapreplace_max`;
`uuid.uuid7()`; `pathlib.Path.copy()`/`move()`; the tail-call interpreter; the experimental JIT in official builds;
incremental garbage collection (reverted in 3.15); `map(strict=True)`; `functools.Placeholder` for `partial`;
`annotationlib.get_annotations`; Zstandard support in `tarfile`/`zipfile`/`shutil`.

**3.15:** PEP 810 explicit lazy imports (`lazy import json`, `lazy from x import y`, module scope only); PEP 814
`frozendict` built-in; PEP 661 `sentinel` built-in; PEP 686 UTF-8 is the default encoding for `open()`; PEP 798
unpacking in comprehensions (`[*xs for xs in lists]`, `{**d for d in dicts}`); PEP 799 `profiling` package with
`profiling.tracing` (cProfile) and `profiling.sampling` (the Tachyon sampling profiler, `--flamegraph`, `--live`);
PEP 791 `math.integer`; TOML 1.1 in `tomllib`; `Counter` symmetric difference `^`; `asyncio.TaskGroup.cancel()`;
better "did you mean" `AttributeError` suggestions (for example `list.push` suggests `.append`); typing PEP 728
(TypedDict `extra_items`/`closed`), PEP 747 `TypeForm`, PEP 800 disjoint bases; a significantly upgraded JIT; frame
pointers enabled by default (PEP 831); the generational GC restored.

## Pixi conventions taught by the course

Pixi is the only tool learners use to install Python and packages, and to run code. Never tell the learner to use
`pip install`, `python -m venv`, `uv`, or bare `python`/`pytest`. Use `pixi init`, `pixi add <pkg>` (conda-forge
first), `pixi add --pypi <pkg>` only when a package isn't on conda-forge, `pixi run python file.py`, `pixi run <task>`,
`pixi shell`, `pixi exec --spec "python=3.15" python`, `pixi global install`, features/environments, and `pixi.lock`.
Project pages use this repository's helpers: `pixi run projects`, `pixi run start p01`, `pixi run grade p01`.

Beginner lessons use `print()` freely. Professional modules (Part 6 onward) explain why production code uses
structured logging (structlog) instead of `print()`.
