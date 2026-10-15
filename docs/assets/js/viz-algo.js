/* Algorithm visualizers: sorting, searching, array techniques, recursion, graphs, grids, DP, backtracking, bits, KMP, Huffman. */
(() => {
  "use strict";
  if (!window.PPViz) return;
  const { registerViz, api } = window.PPViz;
  const { h, s, esc } = api;

  /* ---------------- shared helpers ---------------- */
  const V = (n) => `var(--viz-${n})`;
  const COL = {
    base: "var(--viz-1)", cmp: "var(--viz-active)", swap: "var(--viz-4)", pivot: "var(--viz-5)", key: "var(--viz-2)",
    done: "var(--viz-done)", node: "var(--viz-node)", edge: "var(--viz-edge)", fg: "var(--fg)", muted: "var(--fg-muted)",
    faint: "var(--fg-faint)", sunk: "var(--bg-sunk)", border: "var(--border-strong)", path: "var(--viz-3)", teal: "var(--viz-6)",
  };
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const range = (n) => Array.from({ length: n }, (_, i) => i);
  const fmt = (v) => (v === Infinity ? "∞" : v === -Infinity ? "-∞" : String(v));

  function svgBox(w, hgt, { minScale = 0.55 } = {}) {
    return s("svg", {
      viewBox: `0 0 ${w} ${hgt}`, width: w, height: hgt, role: "img",
      style: `width:100%;max-width:${w}px;min-width:${Math.round(Math.min(w, 640) * minScale)}px;height:auto;overflow:visible`,
    });
  }
  function txt(x, y, str, { size = 12, fill = COL.fg, anchor = "middle", weight = 400, mono = true, base = "central" } = {}) {
    return s("text", {
      x, y, "text-anchor": anchor, "dominant-baseline": base, text: String(str),
      style: `fill:${fill};font-size:${size}px;font-weight:${weight};font-family:${mono ? "var(--font-mono)" : "var(--font-sans)"};pointer-events:none`,
    });
  }
  function rect(x, y, w, hgt, fill, { stroke = COL.border, rx = 4, sw = 1, opacity = 1, extra = "" } = {}) {
    return s("rect", { x, y, width: Math.max(0, w), height: Math.max(0, hgt), rx, style: `fill:${fill};stroke:${stroke};stroke-width:${sw};opacity:${opacity};${extra}` });
  }
  function line(x1, y1, x2, y2, stroke = COL.edge, sw = 1.5, extra = "") {
    return s("line", { x1, y1, x2, y2, style: `stroke:${stroke};stroke-width:${sw};${extra}` });
  }
  function circle(cx, cy, r, fill, stroke = COL.border, sw = 1.5) {
    return s("circle", { cx, cy, r, style: `fill:${fill};stroke:${stroke};stroke-width:${sw}` });
  }
  function soft(color, pct = 35) { return `color-mix(in srgb, ${color} ${pct}%, var(--viz-node))`; }

  /** An extra row of input controls placed above the player row. */
  function inputRow(ui) {
    const row = h("div", { class: "viz-controls" });
    ui.root.insertBefore(row, ui.controls);
    return row;
  }
  function numInput(value, attrs = {}) { return h("input", { type: "number", value, style: "width:5.5em", ...attrs }); }
  function textInput(value, width = "14em", attrs = {}) { return api.input({ value, style: `width:${width}`, ...attrs }); }

  /** A small monospaced stats bar: setStats([[label, value], ...]). */
  function statsBar() {
    const el = h("div", { style: "display:flex;flex-wrap:wrap;gap:6px 14px;font:0.78rem var(--font-mono);color:var(--fg-muted);padding:4px 2px" });
    return {
      el,
      set(items) { el.innerHTML = items.map(([k, v]) => `<span>${esc(k)}: <b style="color:var(--fg)">${esc(v)}</b></span>`).join(""); },
    };
  }

  /** Python pseudo-code panel with one highlighted line. */
  function codePanel(lines = []) {
    const el = h("pre", { style: "margin:0;font:0.76rem/1.6 var(--font-mono);background:var(--bg-code);border:1px solid var(--border);border-radius:6px;padding:6px 0;overflow-x:auto;color:var(--fg)" });
    let rows = [];
    const setLines = (ls) => {
      el.innerHTML = "";
      rows = ls.map((t) => h("div", { style: "padding:0 10px;white-space:pre;border-left:3px solid transparent", text: t }));
      el.append(...rows);
    };
    setLines(lines);
    return {
      el, setLines,
      set(i) {
        rows.forEach((r, k) => {
          const on = k === i;
          r.style.background = on ? "color-mix(in srgb, var(--viz-active) 40%, transparent)" : "transparent";
          r.style.borderLeftColor = on ? "var(--viz-2)" : "transparent";
        });
      },
    };
  }

  /** Two-column layout: main (svg) and side panel. */
  function split(stage, sideWidth = "240px") {
    const main = h("div", { style: "flex:3 1 340px;min-width:0" });
    const side = h("div", { style: `flex:1 1 ${sideWidth};min-width:0;font-size:0.8rem` });
    stage.append(h("div", { style: "display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start" }, main, side));
    return { main, side };
  }
  const sideBox = (title, body) => `<div style="margin-bottom:8px"><div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--fg-faint);font-weight:700;margin-bottom:2px">${esc(title)}</div><div style="font-family:var(--font-mono);font-size:0.78rem;color:var(--fg);word-break:break-word">${body}</div></div>`;
  const chip = (t, color = "var(--viz-node)") => `<span style="display:inline-block;padding:0 6px;margin:1px 2px;border-radius:4px;border:1px solid var(--border-strong);background:${color}">${esc(t)}</span>`;
  function miniTable(headers, rows) {
    const th = headers.map((x) => `<th style="padding:1px 6px;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap">${esc(x)}</th>`).join("");
    const trs = rows.map((r) => `<tr${r.hl ? ' style="background:color-mix(in srgb, var(--viz-active) 35%, transparent)"' : ""}>${r.cells.map((c) => `<td style="padding:1px 6px;white-space:nowrap">${esc(c)}</td>`).join("")}</tr>`).join("");
    return `<table style="border-collapse:collapse;font:0.76rem var(--font-mono);margin:0">${th ? `<thead><tr>${th}</tr></thead>` : ""}<tbody>${trs}</tbody></table>`;
  }

  /** A row of labelled boxes: cells = [{v, fill, top, bottom, opacity, stroke}]. */
  function cellRow(g, x0, y, cells, cw, ch = 30, { size = 13, idx = true } = {}) {
    cells.forEach((c, i) => {
      const x = x0 + i * cw;
      g.append(rect(x + 1, y, cw - 2, ch, c.fill || COL.node, { opacity: c.opacity ?? 1, stroke: c.stroke || COL.border, sw: c.stroke ? 2.5 : 1 }));
      g.append(txt(x + cw / 2, y + ch / 2, c.v, { size: Math.min(size, cw * 0.55) }));
      if (idx) g.append(txt(x + cw / 2, y - 8, c.top ?? i, { size: 9.5, fill: COL.faint }));
      if (c.bottom) g.append(txt(x + cw / 2, y + ch + 11, c.bottom, { size: 10, fill: c.bottomFill || COL.muted, weight: 700 }));
    });
  }

  /* =====================================================================
   * sorting
   * ===================================================================== */
  const SORTS = {
    bubble: {
      name: "Bubble sort",
      code: [
        "for i in range(n - 1):",
        "    swapped = False",
        "    for j in range(n - 1 - i):",
        "        if a[j] > a[j + 1]:",
        "            a[j], a[j + 1] = a[j + 1], a[j]",
        "            swapped = True",
        "    if not swapped:",
        "        break",
      ],
    },
    insertion: {
      name: "Insertion sort",
      code: [
        "for i in range(1, n):",
        "    key = a[i]",
        "    j = i - 1",
        "    while j >= 0 and a[j] > key:",
        "        a[j + 1] = a[j]",
        "        j -= 1",
        "    a[j + 1] = key",
      ],
    },
    selection: {
      name: "Selection sort",
      code: [
        "for i in range(n - 1):",
        "    m = i",
        "    for j in range(i + 1, n):",
        "        if a[j] < a[m]:",
        "            m = j",
        "    a[i], a[m] = a[m], a[i]",
      ],
    },
    merge: {
      name: "Merge sort",
      code: [
        "def merge_sort(a, lo, hi):",
        "    if hi - lo <= 1: return",
        "    mid = (lo + hi) // 2",
        "    merge_sort(a, lo, mid)",
        "    merge_sort(a, mid, hi)",
        "    left, right = a[lo:mid], a[mid:hi]",
        "    i = j = 0; k = lo",
        "    while i < len(left) and j < len(right):",
        "        if left[i] <= right[j]: a[k] = left[i]; i += 1",
        "        else: a[k] = right[j]; j += 1",
        "        k += 1",
        "    a[k:hi] = left[i:] + right[j:]",
      ],
    },
    quick: {
      name: "Quick sort (Lomuto)",
      code: [
        "def quick_sort(a, lo, hi):",
        "    if lo >= hi: return",
        "    pivot = a[hi]           # Lomuto: last element",
        "    i = lo",
        "    for j in range(lo, hi):",
        "        if a[j] < pivot:",
        "            a[i], a[j] = a[j], a[i]",
        "            i += 1",
        "    a[i], a[hi] = a[hi], a[i]",
        "    quick_sort(a, lo, i - 1)",
        "    quick_sort(a, i + 1, hi)",
      ],
    },
    heap: {
      name: "Heap sort",
      code: [
        "def sift_down(a, i, n):",
        "    while (c := 2 * i + 1) < n:",
        "        if c + 1 < n and a[c + 1] > a[c]: c += 1",
        "        if a[i] >= a[c]: break",
        "        a[i], a[c] = a[c], a[i]; i = c",
        "for i in range(n // 2 - 1, -1, -1):",
        "    sift_down(a, i, n)      # build a max-heap",
        "for end in range(n - 1, 0, -1):",
        "    a[0], a[end] = a[end], a[0]",
        "    sift_down(a, 0, end)",
      ],
    },
    counting: {
      name: "Counting sort",
      code: [
        "k = max(a)",
        "count = [0] * (k + 1)",
        "for x in a:",
        "    count[x] += 1",
        "i = 0",
        "for v in range(k + 1):",
        "    for _ in range(count[v]):",
        "        a[i] = v; i += 1",
      ],
    },
    radix: {
      name: "Radix sort (LSD, base 10)",
      code: [
        "exp = 1",
        "while max(a) // exp > 0:",
        "    buckets = [[] for _ in range(10)]",
        "    for x in a:",
        "        buckets[(x // exp) % 10].append(x)",
        "    a = [x for b in buckets for x in b]",
        "    exp *= 10",
      ],
    },
  };

  function sortFrames(algo, input) {
    const a = [...input];
    const n = a.length;
    const frames = [];
    let cmp = 0, wr = 0, pass = 0;
    const done = new Set();
    const rec = (line, msg, { hl = {}, range: rg = null, aux = null } = {}) =>
      frames.push({ a: [...a], hl, line, msg, cmp, wr, pass, done: new Set(done), range: rg, aux });
    const allDone = () => range(n).forEach((i) => done.add(i));
    const swap = (i, j) => { [a[i], a[j]] = [a[j], a[i]]; wr++; };
    rec(-1, `Start: ${SORTS[algo].name} on ${n} values.`);

    if (algo === "bubble") {
      for (let i = 0; i < n - 1; i++) {
        pass++;
        let swapped = false;
        rec(0, `Pass ${i + 1}: bubble the largest remaining value to index ${n - 1 - i}.`);
        for (let j = 0; j < n - 1 - i; j++) {
          cmp++;
          rec(3, `Compare a[${j}]=${a[j]} with a[${j + 1}]=${a[j + 1]}.`, { hl: { [j]: "cmp", [j + 1]: "cmp" } });
          if (a[j] > a[j + 1]) {
            swap(j, j + 1);
            swapped = true;
            rec(4, `${a[j + 1]} > ${a[j]}, so swap them.`, { hl: { [j]: "swap", [j + 1]: "swap" } });
          }
        }
        done.add(n - 1 - i);
        if (!swapped) { allDone(); rec(7, `No swaps in pass ${i + 1}: the array is already sorted, so stop early.`); break; }
      }
    } else if (algo === "insertion") {
      for (let i = 1; i < n; i++) {
        pass++;
        const key = a[i];
        rec(1, `key = a[${i}] = ${key}. Everything left of index ${i} is already sorted.`, { hl: { [i]: "key" }, range: [0, i + 1] });
        let j = i - 1;
        while (j >= 0) {
          cmp++;
          rec(3, `Is a[${j}]=${a[j]} > key=${key}?`, { hl: { [j]: "cmp", [j + 1]: "key" }, range: [0, i + 1] });
          if (a[j] <= key) break;
          a[j + 1] = a[j];
          wr++;
          rec(4, `Yes: shift ${a[j]} one slot right (key is held aside).`, { hl: { [j + 1]: "swap" }, range: [0, i + 1] });
          j--;
        }
        a[j + 1] = key;
        wr++;
        rec(6, `Insert key ${key} at index ${j + 1}.`, { hl: { [j + 1]: "swap" }, range: [0, i + 1] });
      }
      allDone();
    } else if (algo === "selection") {
      for (let i = 0; i < n - 1; i++) {
        pass++;
        let m = i;
        rec(1, `Pass ${i + 1}: find the minimum of a[${i}:]; start with m = ${i}.`, { hl: { [i]: "key" } });
        for (let j = i + 1; j < n; j++) {
          cmp++;
          rec(3, `Is a[${j}]=${a[j]} < current min a[${m}]=${a[m]}?`, { hl: { [j]: "cmp", [m]: "key" } });
          if (a[j] < a[m]) { m = j; rec(4, `Yes: new minimum at index ${m}.`, { hl: { [m]: "key" } }); }
        }
        if (m !== i) swap(i, m);
        done.add(i);
        rec(5, m !== i ? `Swap the minimum ${a[i]} into index ${i}.` : `a[${i}] is already the minimum; no swap needed.`, { hl: { [i]: "swap", [m]: "swap" } });
      }
      allDone();
    } else if (algo === "merge") {
      const ms = (lo, hi) => {
        if (hi - lo <= 1) return;
        const mid = (lo + hi) >> 1;
        rec(2, `Split a[${lo}:${hi}] at mid = ${mid}.`, { range: [lo, hi] });
        ms(lo, mid);
        ms(mid, hi);
        pass++;
        const left = a.slice(lo, mid), right = a.slice(mid, hi);
        let i = 0, j = 0, k = lo;
        const aux = () => ({ rows: [{ label: "left", vals: left, at: i }, { label: "right", vals: right, at: j }] });
        rec(5, `Merge sorted halves [${left}] and [${right}].`, { range: [lo, hi], aux: aux() });
        while (i < left.length && j < right.length) {
          cmp++;
          rec(7, `Compare left[${i}]=${left[i]} with right[${j}]=${right[j]}.`, { hl: { [k]: "cmp" }, range: [lo, hi], aux: aux() });
          if (left[i] <= right[j]) { a[k] = left[i]; i++; wr++; rec(8, `${a[k]} is smaller (or equal, which keeps the sort stable): write it to a[${k}].`, { hl: { [k]: "swap" }, range: [lo, hi], aux: aux() }); }
          else { a[k] = right[j]; j++; wr++; rec(9, `${a[k]} is smaller: write it to a[${k}].`, { hl: { [k]: "swap" }, range: [lo, hi], aux: aux() }); }
          k++;
        }
        const rest = left.slice(i).concat(right.slice(j));
        rest.forEach((v) => { a[k++] = v; wr++; });
        if (rest.length) rec(11, `Copy the leftover [${rest}] into a[${hi - rest.length}:${hi}].`, { range: [lo, hi], aux: aux() });
        if (lo === 0 && hi === n) allDone();
      };
      ms(0, n);
      allDone();
    } else if (algo === "quick") {
      const qs = (lo, hi) => {
        if (lo > hi) return;
        if (lo === hi) { done.add(lo); rec(1, `a[${lo}:${hi + 1}] has one element: it is in place.`, { range: [lo, hi + 1] }); return; }
        pass++;
        const pivot = a[hi];
        rec(2, `Partition a[${lo}..${hi}] around pivot ${pivot} (the last element).`, { hl: { [hi]: "pivot" }, range: [lo, hi + 1] });
        let i = lo;
        for (let j = lo; j < hi; j++) {
          cmp++;
          rec(5, `Is a[${j}]=${a[j]} < pivot ${pivot}? (i = ${i} marks the end of the "smaller" zone)`, { hl: { [j]: "cmp", [hi]: "pivot", [i]: i === j ? "cmp" : "key" }, range: [lo, hi + 1] });
          if (a[j] < pivot) {
            if (i !== j) swap(i, j);
            rec(6, i !== j ? `Yes: swap it into the smaller zone at index ${i}.` : `Yes: it is already at the zone boundary.`, { hl: { [i]: "swap", [hi]: "pivot" }, range: [lo, hi + 1] });
            i++;
          }
        }
        if (i !== hi) swap(i, hi);
        done.add(i);
        rec(8, `Move pivot ${pivot} to index ${i}: everything left is smaller, everything right is not.`, { hl: { [i]: "pivot" }, range: [lo, hi + 1] });
        qs(lo, i - 1);
        qs(i + 1, hi);
      };
      qs(0, n - 1);
      allDone();
    } else if (algo === "heap") {
      const sift = (i, m, line) => {
        for (;;) {
          let c = 2 * i + 1;
          if (c >= m) return;
          if (c + 1 < m) {
            cmp++;
            rec(2, `Children of a[${i}]: a[${c}]=${a[c]} and a[${c + 1}]=${a[c + 1]}; pick the larger.`, { hl: { [c]: "cmp", [c + 1]: "cmp", [i]: "key" }, range: [0, m] });
            if (a[c + 1] > a[c]) c++;
          }
          cmp++;
          rec(3, `Is parent a[${i}]=${a[i]} >= child a[${c}]=${a[c]}?`, { hl: { [i]: "key", [c]: "cmp" }, range: [0, m] });
          if (a[i] >= a[c]) return;
          swap(i, c);
          rec(4, `No: swap them and keep sifting down from index ${c}.`, { hl: { [i]: "swap", [c]: "swap" }, range: [0, m] });
          i = c;
        }
      };
      for (let i = (n >> 1) - 1; i >= 0; i--) { rec(6, `Build heap: sift down from index ${i}.`, { hl: { [i]: "key" } }); sift(i, n); }
      rec(7, `a is now a max-heap: a[0]=${a[0]} is the largest value.`, { hl: { 0: "pivot" } });
      for (let end = n - 1; end > 0; end--) {
        pass++;
        swap(0, end);
        done.add(end);
        rec(8, `Swap the max ${a[end]} to index ${end}; the heap shrinks to a[0:${end}].`, { hl: { 0: "swap", [end]: "swap" }, range: [0, end] });
        sift(0, end);
      }
      allDone();
    } else if (algo === "counting") {
      if (a.some((x) => !Number.isInteger(x) || x < 0 || x > 999)) {
        rec(-1, "Counting sort needs non-negative integers (0..999 here). Try a different array.");
        return frames;
      }
      const k = Math.max(...a);
      const count = new Array(k + 1).fill(0);
      const aux = (hlv) => ({ rows: [{ label: "count", cells: count.map((c, v) => ({ top: v, v: c, hl: v === hlv })).filter((c) => c.v > 0 || c.hl) }] });
      rec(1, `k = max(a) = ${k}; make ${k + 1} counters (only non-zero ones are shown).`, { aux: aux(-1) });
      a.forEach((x, i) => { count[x]++; rec(3, `count[${x}] += 1 → ${count[x]}. No comparisons: the value is the index.`, { hl: { [i]: "cmp" }, aux: aux(x) }); });
      pass++;
      let i = 0;
      for (let v = 0; v <= k; v++) {
        for (let c = 0; c < count[v]; c++) {
          a[i] = v; wr++; done.add(i);
          rec(7, `Write ${v} to a[${i}] (${c + 1} of ${count[v]}).`, { hl: { [i]: "swap" }, aux: aux(v) });
          i++;
        }
      }
    } else if (algo === "radix") {
      if (a.some((x) => !Number.isInteger(x) || x < 0)) {
        rec(-1, "This radix sort handles non-negative integers only. Try a different array.");
        return frames;
      }
      const mx = Math.max(...a);
      let exp = 1;
      rec(0, `Sort by one decimal digit at a time, least significant first. max(a) = ${mx}.`);
      while (Math.floor(mx / exp) > 0) {
        pass++;
        const buckets = range(10).map(() => []);
        rec(2, `Pass ${pass}: distribute by the ${exp === 1 ? "ones" : exp === 10 ? "tens" : exp === 100 ? "hundreds" : `10^${Math.log10(exp)}`} digit.`, { aux: { buckets: buckets.map((b) => [...b]), digit: -1 } });
        a.forEach((x, i) => {
          const d = Math.floor(x / exp) % 10;
          buckets[d].push(x); wr++;
          rec(4, `${x}: digit (${x} // ${exp}) % 10 = ${d} → bucket ${d}.`, { hl: { [i]: "cmp" }, aux: { buckets: buckets.map((b) => [...b]), digit: d } });
        });
        let i = 0;
        buckets.forEach((b) => b.forEach((x) => { a[i++] = x; }));
        rec(5, `Concatenate the buckets in order. Each pass is stable, so earlier digits stay ordered.`, { aux: { buckets: buckets.map((b) => [...b]), digit: -1 } });
        exp *= 10;
      }
      allDone();
    }
    allDone();
    rec(-1, `Done: ${cmp} comparisons, ${wr} swaps/writes, ${pass} ${algo === "merge" ? "merges" : algo === "quick" ? "partitions" : "passes"}.`);
    return frames;
  }

  function sortPanel(parent, title) {
    const head = h("div", { style: "font:600 0.82rem var(--font-sans);margin:2px 0" });
    const holder = h("div");
    const stats = statsBar();
    const wrap = h("div", { style: "flex:1 1 300px;min-width:0" }, head, stats.el, holder);
    parent.append(wrap);
    head.textContent = title;
    return {
      wrap, setTitle(t) { head.textContent = t; },
      draw(f, algo, compact) {
        const n = f.a.length;
        const W = compact ? 420 : 620, H = 190;
        const auxH = f.aux ? (f.aux.buckets ? 40 + 16 * Math.max(1, ...f.aux.buckets.map((b) => b.length)) : 58 * f.aux.rows.length) : 0;
        const svg = svgBox(W, H + 30 + auxH);
        const lo = Math.min(0, ...f.a), hi = Math.max(1, ...f.a);
        const y = (v) => 10 + (H - 10) * (1 - (v - lo) / (hi - lo || 1));
        const bw = W / Math.max(n, 1);
        f.a.forEach((v, i) => {
          const role = f.hl[i];
          let fill = role ? COL[role] : f.done.has(i) ? COL.done : COL.base;
          const out = f.range && (i < f.range[0] || i >= f.range[1]) && !f.done.has(i);
          const y0 = y(Math.max(v, 0)), y1 = y(Math.min(v, 0));
          svg.append(rect(i * bw + 1.5, y0, bw - 3, Math.max(2, y1 - y0), fill, { stroke: "none", rx: 2, opacity: out ? 0.35 : 1 }));
          if (n <= 26) svg.append(txt(i * bw + bw / 2, H + 12, v, { size: Math.min(11, bw * 0.45), fill: COL.muted }));
        });
        svg.append(line(0, y(0), W, y(0), COL.edge, 1));
        if (f.aux) {
          const top = H + 34;
          if (f.aux.buckets) {
            const cw = W / 10;
            f.aux.buckets.forEach((b, d) => {
              const x = d * cw;
              svg.append(rect(x + 2, top, cw - 4, auxH - 8, d === f.aux.digit ? soft(COL.cmp, 60) : COL.sunk, { rx: 4 }));
              svg.append(txt(x + cw / 2, top + 10, d, { size: 10, fill: COL.faint, weight: 700 }));
              b.forEach((x2, k) => svg.append(txt(x + cw / 2, top + 26 + 16 * k, x2, { size: 11 })));
            });
          } else {
            f.aux.rows.forEach((r, ri) => {
              const top2 = top + ri * 58 + 14;
              svg.append(txt(0, top2 + 14, r.label, { anchor: "start", size: 11, fill: COL.muted, weight: 700 }));
              const cells = r.cells || r.vals.map((v, k) => ({ v, top: k, hl: k === r.at }));
              const cw = Math.min(36, (W - 50) / Math.max(cells.length, 1));
              cellRow(svg, 48, top2, cells.map((c) => ({ ...c, fill: c.hl ? COL.cmp : r.cells ? COL.node : r.vals && cells.indexOf(c) < r.at ? COL.sunk : COL.node, opacity: !r.cells && cells.indexOf(c) < r.at ? 0.5 : 1 })), cw, 26, { size: 11 });
            });
          }
        }
        holder.replaceChildren(svg);
        stats.set([["comparisons", f.cmp], ["swaps/writes", f.wr], [algo === "merge" ? "merges" : algo === "quick" ? "partitions" : "passes", f.pass]]);
      },
    };
  }

  registerViz("sorting", (el, config, a) => {
    const all = Object.keys(SORTS);
    const algos = Array.isArray(config.algorithms) ? config.algorithms.filter((x) => SORTS[x]) : all;
    if (!algos.length) algos.push(...all);
    let algo = algos.includes(config.default) ? config.default : algos[0];
    let race = "";
    const size = clamp(Number(config.size) || 12, 2, 40);
    const randomArray = () => range(size).map(() => a.randInt(1, 60));
    const initial = Array.isArray(config.array) && config.array.length ? config.array.map(Number).filter(Number.isFinite) : randomArray();
    let arr = [...initial];

    const ui = a.shell(el, { title: config.title || "Sorting algorithms", kind: "Visualizer" });
    const panels = h("div", { style: "display:flex;flex-wrap:wrap;gap:14px" });
    const code = codePanel();
    const codeWrap = h("div", { style: "flex:1 1 260px;min-width:0" }, code.el);
    const body = h("div", { style: "display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start" }, h("div", { style: "flex:3 1 360px;min-width:0" }, panels), codeWrap);
    ui.stage.append(body);
    const left = sortPanel(panels, "");
    const right = sortPanel(panels, "");
    ui.setLegend([["comparing", COL.cmp], ["swap / write", COL.swap], ["pivot / heap top", COL.pivot], ["key / current min", COL.key], ["final position", COL.done], ["unsorted", COL.base]]);

    const inputs = inputRow(ui);
    const algoSel = a.select(algos.map((x) => [x, SORTS[x].name]), algo, (v) => { algo = v; build(); });
    const raceSel = a.select([["", "(none)"], ...algos.map((x) => [x, SORTS[x].name])], "", (v) => { race = v; build(); });
    const arrIn = textInput(arr.join(", "), "16em", { "aria-label": "Array" });
    inputs.append(
      a.label("algorithm", algoSel), a.label("race vs", raceSel), a.label("array", arrIn),
      a.button("Apply", () => { const v = a.parseList(arrIn.value); if (v.length >= 2) { arr = v.slice(0, 40); build(); } else ui.setLog("Enter at least two numbers, separated by commas or spaces."); }),
      a.button("Random", () => { arr = randomArray(); build(); }),
      a.button("Reversed", () => { arr = [...arr].sort((x, y) => y - x); build(); }),
      a.button("Reset", () => { arr = [...initial]; algo = algos.includes(config.default) ? config.default : algos[0]; algoSel.value = algo; race = ""; raceSel.value = ""; build(); }),
    );

    let fa = [], fb = [];
    const render = (idx) => {
      const f1 = fa[Math.min(idx, fa.length - 1)];
      left.draw(f1, algo, !!race);
      if (race) {
        const f2 = fb[Math.min(idx, fb.length - 1)];
        right.draw(f2, race, true);
        const fin = (fr, i) => (i >= fr.length - 1 ? " (finished)" : "");
        ui.setLog(`<b>${esc(SORTS[algo].name)}</b>${fin(fa, idx)}: ${esc(f1.msg)}<br><b>${esc(SORTS[race].name)}</b>${fin(fb, idx)}: ${esc(f2.msg)}`);
      } else {
        code.set(f1.line);
        ui.setLog(esc(f1.msg));
      }
    };
    const player = a.player(ui.controls, render);
    function build() {
      arrIn.value = arr.join(", ");
      fa = sortFrames(algo, arr);
      left.setTitle(race ? SORTS[algo].name : "");
      if (race) { fb = sortFrames(race, arr); right.setTitle(SORTS[race].name); }
      right.wrap.style.display = race ? "" : "none";
      codeWrap.style.display = race ? "none" : "";
      code.setLines(SORTS[algo].code);
      player.load(range(Math.max(fa.length, race ? fb.length : 0)));
    }
    build();
  });

  /* =====================================================================
   * binary-search
   * ===================================================================== */
  const BS_CODE = [
    "lo, hi = 0, len(a) - 1",
    "while lo <= hi:",
    "    mid = (lo + hi) // 2",
    "    if a[mid] == target: return mid",
    "    elif a[mid] < target: lo = mid + 1",
    "    else: hi = mid - 1",
    "return -1",
  ];
  function bsFrames(a, target) {
    const bs = [{ lo: 0, hi: a.length - 1, mid: -1, line: 0, cmp: 0, msg: `Binary: search the whole sorted array, lo = 0, hi = ${a.length - 1}.` }];
    let lo = 0, hi = a.length - 1, cmp = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      cmp++;
      if (a[mid] === target) { bs.push({ lo, hi, mid, line: 3, cmp, found: mid, msg: `Binary: mid = (${lo} + ${hi}) // 2 = ${mid}; a[${mid}] = ${a[mid]} equals ${target}. Found!` }); break; }
      if (a[mid] < target) { bs.push({ lo, hi, mid, line: 4, cmp, msg: `Binary: mid = ${mid}; a[${mid}] = ${a[mid]} < ${target}, so discard the left half: lo = ${mid + 1}.` }); lo = mid + 1; }
      else { bs.push({ lo, hi, mid, line: 5, cmp, msg: `Binary: mid = ${mid}; a[${mid}] = ${a[mid]} > ${target}, so discard the right half: hi = ${mid - 1}.` }); hi = mid - 1; }
    }
    if (bs[bs.length - 1].found === undefined) bs.push({ lo, hi, mid: -1, line: 6, cmp, msg: `Binary: lo = ${lo} > hi = ${hi}; the range is empty, so ${target} is not present.` });
    const ls = [{ i: -1, cmp: 0, msg: "Linear: start at index 0." }];
    for (let i = 0; i < a.length; i++) {
      if (a[i] === target) { ls.push({ i, cmp: i + 1, found: i, msg: `Linear: a[${i}] = ${a[i]} matches after ${i + 1} comparisons.` }); break; }
      ls.push({ i, cmp: i + 1, msg: `Linear: a[${i}] = ${a[i]} ≠ ${target}, keep going.` });
    }
    if (ls[ls.length - 1].found === undefined) ls.push({ i: a.length, cmp: a.length, msg: `Linear: checked all ${a.length} items; ${target} is not present.` });
    return range(Math.max(bs.length, ls.length)).map((k) => ({ b: bs[Math.min(k, bs.length - 1)], l: ls[Math.min(k, ls.length - 1)], bDone: k >= bs.length - 1, lDone: k >= ls.length - 1 }));
  }

  registerViz("binary-search", (el, config, a) => {
    const randomArray = () => [...new Set(range(16).map(() => a.randInt(1, 99)))].sort((x, y) => x - y);
    const initial = Array.isArray(config.array) && config.array.length ? config.array.map(Number).filter(Number.isFinite).sort((x, y) => x - y) : randomArray();
    const initialTarget = Number.isFinite(Number(config.target)) && config.target !== undefined ? Number(config.target) : initial[Math.floor(initial.length * 0.7)];
    let arr = [...initial], target = initialTarget;
    const ui = a.shell(el, { title: config.title || "Binary search vs linear search" });
    const { main, side } = split(ui.stage, "250px");
    const holder = h("div");
    const stats = statsBar();
    main.append(stats.el, holder);
    const code = codePanel(BS_CODE);
    side.append(code.el);
    ui.setLegend([["mid probe", COL.cmp], ["found", COL.done], ["discarded", COL.sunk], ["linear: current", COL.key]]);
    const inputs = inputRow(ui);
    const arrIn = textInput(arr.join(", "), "18em", { "aria-label": "Sorted array" });
    const tIn = numInput(target, { "aria-label": "Target" });
    inputs.append(
      a.label("array", arrIn), a.label("target", tIn),
      a.button("Apply", () => { const v = a.parseList(arrIn.value); if (v.length) { arr = v.slice(0, 40).sort((x, y) => x - y); target = Number(tIn.value); build(); } }),
      a.button("Random", () => { arr = randomArray(); target = Math.random() < 0.8 ? arr[a.randInt(0, arr.length - 1)] : a.randInt(1, 99); build(); }),
      a.button("Reset", () => { arr = [...initial]; target = initialTarget; build(); }),
    );
    const render = (f) => {
      const n = arr.length;
      const W = 640, cw = Math.min(44, (W - 20) / n), x0 = (W - cw * n) / 2;
      const svg = svgBox(W, 250);
      svg.append(txt(x0, 14, `binary search for ${target}`, { anchor: "start", size: 12, weight: 700, fill: COL.muted, mono: false }));
      const { b, l } = f;
      cellRow(svg, x0, 40, arr.map((v, i) => {
        const outside = i < b.lo || i > b.hi;
        return { v, fill: b.found === i ? COL.done : i === b.mid ? COL.cmp : outside ? COL.sunk : COL.node, opacity: outside && i !== b.mid ? 0.45 : 1 };
      }), cw);
      [["lo", b.lo, 0], ["mid", b.mid, 1], ["hi", b.hi, 2]].forEach(([name, i, k]) => {
        if (i < 0 || i >= n) return;
        svg.append(txt(x0 + i * cw + cw / 2, 82 + k * 13, `▲${name}`, { size: 10, weight: 700, fill: name === "mid" ? COL.key : COL.base }));
      });
      svg.append(txt(x0, 140, `linear search for ${target}`, { anchor: "start", size: 12, weight: 700, fill: COL.muted, mono: false }));
      cellRow(svg, x0, 166, arr.map((v, i) => ({ v, fill: l.found === i ? COL.done : i === l.i ? COL.key : i < l.i ? COL.sunk : COL.node, opacity: i < l.i ? 0.45 : 1 })), cw);
      if (l.i >= 0 && l.i < n) svg.append(txt(x0 + l.i * cw + cw / 2, 208, "▲i", { size: 10, weight: 700, fill: COL.key }));
      holder.replaceChildren(svg);
      stats.set([["binary comparisons", b.cmp + (f.bDone ? " ✓" : "")], ["linear comparisons", l.cmp + (f.lDone ? " ✓" : "")], ["n", n], ["⌈log2(n+1)⌉", Math.ceil(Math.log2(n + 1))]]);
      code.set(b.line);
      ui.setLog(`${esc(b.msg)}<br>${esc(l.msg)}`);
    };
    const player = a.player(ui.controls, render);
    function build() { arrIn.value = arr.join(", "); tIn.value = target; player.load(bsFrames(arr, target)); }
    build();
  });

  /* =====================================================================
   * array-technique
   * ===================================================================== */
  const AT = {
    "two-sum-sorted": {
      name: "Two pointers: pair with sum = target (sorted array)",
      code: [
        "l, r = 0, len(a) - 1",
        "while l < r:",
        "    s = a[l] + a[r]",
        "    if s == target: return l, r",
        "    elif s < target: l += 1   # need a bigger sum",
        "    else: r -= 1              # need a smaller sum",
        "return None",
      ],
    },
    "sliding-window": {
      name: "Sliding window: max sum of k consecutive items",
      code: [
        "window = sum(a[:k])",
        "best = window",
        "for i in range(k, len(a)):",
        "    window += a[i] - a[i - k]   # add new, drop old",
        "    best = max(best, window)",
        "return best",
      ],
    },
    "longest-substring": {
      name: "Sliding window: longest substring without repeats",
      code: [
        "last = {}",
        "start = best = 0",
        "for i, ch in enumerate(s):",
        "    if ch in last and last[ch] >= start:",
        "        start = last[ch] + 1     # shrink past the repeat",
        "    last[ch] = i",
        "    best = max(best, i - start + 1)",
      ],
    },
    "prefix-sum": {
      name: "Prefix sums with O(1) range-sum queries",
      code: [
        "P = [0] * (len(a) + 1)",
        "for i, x in enumerate(a):",
        "    P[i + 1] = P[i] + x",
        "def range_sum(l, r):          # inclusive l..r",
        "    return P[r + 1] - P[l]",
      ],
    },
  };

  function atFrames(tech, arr, { target, k, text, queries }) {
    const F = [];
    if (tech === "two-sum-sorted") {
      const a = [...arr].sort((x, y) => x - y);
      let l = 0, r = a.length - 1, steps = 0;
      const push = (line, msg, extra = {}) => F.push({ a, line, msg, l, r, steps, ...extra });
      push(0, `Start with l at the smallest value and r at the largest. Target = ${target}.`);
      let found = false;
      while (l < r) {
        const sum = a[l] + a[r];
        steps++;
        if (sum === target) { push(3, `a[${l}] + a[${r}] = ${a[l]} + ${a[r]} = ${sum} = target. Found the pair (${l}, ${r}).`, { found: true }); found = true; break; }
        if (sum < target) { push(4, `${a[l]} + ${a[r]} = ${sum} < ${target}: every pair with this l is too small, so move l right.`); l++; }
        else { push(5, `${a[l]} + ${a[r]} = ${sum} > ${target}: every pair with this r is too big, so move r left.`); r--; }
      }
      if (!found) push(6, `l met r: no pair sums to ${target}. Only ${steps} checks instead of ${(a.length * (a.length - 1)) / 2} pairs.`);
      else F.push({ ...F[F.length - 1], msg: `${F[F.length - 1].msg} ${steps} checks vs up to ${(a.length * (a.length - 1)) / 2} for brute force.` });
    } else if (tech === "sliding-window") {
      const a = arr;
      const kk = clamp(k, 1, a.length);
      let win = a.slice(0, kk).reduce((x, y) => x + y, 0), best = win, bestAt = 0;
      F.push({ a, line: 0, lo: 0, hi: kk - 1, win, best, bestAt, msg: `window = sum(a[0:${kk}]) = ${win}. Computing it once costs k additions.` });
      F.push({ a, line: 1, lo: 0, hi: kk - 1, win, best, bestAt, msg: `best = ${best}.` });
      for (let i = kk; i < a.length; i++) {
        win += a[i] - a[i - kk];
        const nb = win > best;
        if (nb) { best = win; bestAt = i - kk + 1; }
        F.push({ a, line: 3, lo: i - kk + 1, hi: i, win, best, bestAt, add: i, drop: i - kk, msg: `Slide: add a[${i}]=${a[i]}, drop a[${i - kk}]=${a[i - kk]} → window = ${win}${nb ? ` (new best)` : ""}. O(1) per step instead of re-summing k items.` });
      }
      F.push({ ...F[F.length - 1], line: 5, add: undefined, drop: undefined, lo: bestAt, hi: bestAt + kk - 1, msg: `Best window is a[${bestAt}:${bestAt + kk}] with sum ${best}. Total work O(n).` });
    } else if (tech === "longest-substring") {
      const str = [...text];
      const last = {};
      let start = 0, best = 0, bs = 0;
      F.push({ str, line: 1, lo: 0, hi: -1, last: {}, best, bs, msg: `Scan "${text}" once, keeping a window [start, i] with no repeated characters.` });
      str.forEach((ch, i) => {
        let msg = `i = ${i}, ch = '${ch}'.`;
        let line = 5;
        if (ch in last && last[ch] >= start) { msg += ` '${ch}' was seen at ${last[ch]} inside the window, so start jumps to ${last[ch] + 1}.`; start = last[ch] + 1; line = 4; }
        last[ch] = i;
        if (i - start + 1 > best) { best = i - start + 1; bs = start; msg += ` New best length ${best}.`; line = line === 4 ? 4 : 6; }
        F.push({ str, line, lo: start, hi: i, last: { ...last }, best, bs, cur: i, msg });
      });
      F.push({ str, line: 6, lo: bs, hi: bs + best - 1, last: { ...last }, best, bs, msg: `Longest substring without repeats: "${str.slice(bs, bs + best).join("")}" (length ${best}).` });
    } else {
      const a = arr;
      const P = [0];
      F.push({ a, P: [...P], line: 0, msg: "P[i] holds the sum of the first i items, so P[0] = 0." });
      a.forEach((x, i) => { P.push(P[i] + x); F.push({ a, P: [...P], line: 2, at: i, msg: `P[${i + 1}] = P[${i}] + a[${i}] = ${P[i]} + ${x} = ${P[i + 1]}.` }); });
      queries.forEach(([l, r]) => {
        if (!(l >= 0 && r < a.length && l <= r)) { F.push({ a, P: [...P], line: 3, msg: `Query (${l}, ${r}) is out of range for indices 0..${a.length - 1}.` }); return; }
        F.push({ a, P: [...P], line: 4, q: [l, r], msg: `sum(a[${l}..${r}]) = P[${r + 1}] - P[${l}] = ${P[r + 1]} - ${P[l]} = ${P[r + 1] - P[l]}: two lookups, no loop.` });
      });
    }
    return F;
  }

  registerViz("array-technique", (el, config, a) => {
    let tech = AT[config.technique] ? config.technique : "two-sum-sorted";
    const defaults = {
      "two-sum-sorted": [1, 3, 4, 6, 8, 11, 14, 17, 20], "sliding-window": [4, -1, 6, 2, -3, 7, 1, 5, -2, 3], "prefix-sum": [3, 1, 4, 1, 5, 9, 2, 6],
    };
    const cfgArr = Array.isArray(config.array) && config.array.length ? config.array.map(Number).filter(Number.isFinite) : null;
    const state = {
      arr: cfgArr || defaults[tech] || defaults["two-sum-sorted"], target: Number(config.target ?? 25), k: Number(config.k ?? 3),
      text: String(config.text ?? "abcabcbb"), queries: Array.isArray(config.queries) ? config.queries : [[1, 3], [0, 7], [4, 6]],
    };
    const init = JSON.parse(JSON.stringify({ ...state, tech }));
    const ui = a.shell(el, { title: config.title || "Array techniques" });
    const { main, side } = split(ui.stage, "260px");
    const holder = h("div"), stats = statsBar();
    main.append(stats.el, holder);
    const code = codePanel(AT[tech].code);
    const sideInfo = h("div", { style: "margin-top:8px" });
    side.append(code.el, sideInfo);
    const inputs = inputRow(ui);
    const techSel = a.select(Object.entries(AT).map(([k2, v]) => [k2, v.name.split(":")[0] + ": " + v.name.split(": ")[1]]), tech, (v) => { tech = v; if (!cfgArr && defaults[v]) state.arr = defaults[v]; sync(); build(); });
    const arrIn = textInput("", "14em", { "aria-label": "Array" });
    const tIn = numInput(state.target, { "aria-label": "Target" });
    const kIn = numInput(state.k, { min: 1, "aria-label": "Window size k" });
    const sIn = textInput(state.text, "10em", { "aria-label": "String" });
    const qIn = textInput("", "10em", { "aria-label": "Queries", title: "l r pairs separated by semicolons" });
    const lt = a.label("target", tIn), lk = a.label("k", kIn), ls = a.label("string", sIn), lq = a.label("queries l r;", qIn), la = a.label("array", arrIn);
    function sync() {
      arrIn.value = state.arr.join(", "); tIn.value = state.target; kIn.value = state.k; sIn.value = state.text;
      qIn.value = state.queries.map((q) => q.join(" ")).join("; ");
      la.style.display = tech === "longest-substring" ? "none" : "inline-flex";
      lt.style.display = tech === "two-sum-sorted" ? "inline-flex" : "none";
      lk.style.display = tech === "sliding-window" ? "inline-flex" : "none";
      ls.style.display = tech === "longest-substring" ? "inline-flex" : "none";
      lq.style.display = tech === "prefix-sum" ? "inline-flex" : "none";
    }
    const read = () => {
      const v = a.parseList(arrIn.value);
      if (v.length >= 2) state.arr = v.slice(0, 30);
      state.target = Number(tIn.value); state.k = Math.max(1, Math.round(Number(kIn.value)) || 1);
      state.text = sIn.value.slice(0, 30) || "abcabcbb";
      state.queries = qIn.value.split(";").map((q) => a.parseList(q).map(Math.round)).filter((q) => q.length === 2);
    };
    inputs.append(
      a.label("technique", techSel), la, lt, lk, ls, lq,
      a.button("Apply", () => { read(); build(); }),
      a.button("Random", () => {
        if (tech === "longest-substring") state.text = range(a.randInt(8, 14)).map(() => "abcdef"[a.randInt(0, 5)]).join("");
        else if (tech === "two-sum-sorted") { state.arr = [...new Set(range(10).map(() => a.randInt(1, 40)))].sort((x, y) => x - y); state.target = state.arr[a.randInt(0, 3)] + state.arr[a.randInt(4, state.arr.length - 1)]; }
        else state.arr = range(10).map(() => a.randInt(-5, 12));
        if (tech === "prefix-sum") state.queries = range(3).map(() => { const l = a.randInt(0, state.arr.length - 1); return [l, a.randInt(l, state.arr.length - 1)]; });
        sync(); build();
      }),
      a.button("Reset", () => { Object.assign(state, JSON.parse(JSON.stringify(init))); tech = init.tech; techSel.value = tech; sync(); build(); }),
    );
    ui.setLegend([["pointer / window", COL.cmp], ["answer", COL.done], ["added", COL.path], ["dropped", COL.swap]]);
    const render = (f) => {
      code.set(f.line);
      ui.setLog(esc(f.msg));
      sideInfo.innerHTML = "";
      const W = 640;
      if (tech === "two-sum-sorted") {
        const n = f.a.length, cw = Math.min(50, (W - 20) / n), x0 = (W - n * cw) / 2;
        const svg = svgBox(W, 110);
        cellRow(svg, x0, 30, f.a.map((v, i) => ({ v, fill: f.found && (i === f.l || i === f.r) ? COL.done : i === f.l || i === f.r ? COL.cmp : i < f.l || i > f.r ? COL.sunk : COL.node, opacity: i < f.l || i > f.r ? 0.45 : 1, bottom: i === f.l && i === f.r ? "l r" : i === f.l ? "▲ l" : i === f.r ? "▲ r" : "" })), cw);
        holder.replaceChildren(svg);
        stats.set([["target", state.target], ["a[l] + a[r]", f.l < f.r || f.found ? f.a[f.l] + f.a[f.r] : "–"], ["checks", f.steps]]);
      } else if (tech === "sliding-window") {
        const n = f.a.length, cw = Math.min(50, (W - 20) / n), x0 = (W - n * cw) / 2;
        const svg = svgBox(W, 110);
        svg.append(rect(x0 + f.lo * cw - 2, 22, (f.hi - f.lo + 1) * cw + 4, 46, "none", { stroke: COL.key, sw: 2.5, rx: 8 }));
        cellRow(svg, x0, 30, f.a.map((v, i) => ({ v, fill: i === f.add ? COL.path : i === f.drop ? COL.swap : i >= f.lo && i <= f.hi ? (f.line === 5 ? COL.done : COL.cmp) : COL.node })), cw);
        holder.replaceChildren(svg);
        stats.set([["k", clamp(state.k, 1, f.a.length)], ["window sum", f.win], ["best", f.best], ["best starts at", f.bestAt]]);
      } else if (tech === "longest-substring") {
        const n = f.str.length, cw = Math.min(44, (W - 20) / Math.max(n, 1)), x0 = (W - n * cw) / 2;
        const svg = svgBox(W, 110);
        if (f.hi >= f.lo) svg.append(rect(x0 + f.lo * cw - 2, 22, (f.hi - f.lo + 1) * cw + 4, 46, "none", { stroke: COL.key, sw: 2.5, rx: 8 }));
        cellRow(svg, x0, 30, f.str.map((v, i) => ({ v, fill: i === f.cur ? COL.cmp : i >= f.lo && i <= f.hi ? soft(f.line === 6 && f.cur === undefined ? COL.done : COL.cmp, 55) : COL.node, bottom: i === f.lo && f.hi >= f.lo ? "start" : i === f.cur ? "i" : "" })), cw);
        holder.replaceChildren(svg);
        stats.set([["window", f.hi >= f.lo ? `[${f.lo}, ${f.hi}]` : "empty"], ["length", Math.max(0, f.hi - f.lo + 1)], ["best", f.best]]);
        sideInfo.innerHTML = sideBox("last seen index", Object.entries(f.last).map(([c, i]) => chip(`${c}:${i}`)).join("") || "{}");
      } else {
        const n = f.a.length, cw = Math.min(48, (W - 60) / (n + 1)), x0 = 50;
        const svg = svgBox(W, 150);
        svg.append(txt(10, 45, "a", { anchor: "start", weight: 700, fill: COL.muted }));
        svg.append(txt(10, 115, "P", { anchor: "start", weight: 700, fill: COL.muted }));
        const q = f.q;
        cellRow(svg, x0 + cw / 2, 30, f.a.map((v, i) => ({ v, fill: i === f.at ? COL.cmp : q && i >= q[0] && i <= q[1] ? COL.done : COL.node })), cw);
        cellRow(svg, x0, 100, range(n + 1).map((i) => ({ v: i < f.P.length ? f.P[i] : "", fill: q && (i === q[1] + 1) ? COL.path : q && i === q[0] ? COL.swap : i === f.P.length - 1 && f.at !== undefined ? COL.cmp : i < f.P.length ? COL.node : COL.sunk })), cw);
        holder.replaceChildren(svg);
        stats.set([["n", n], ["prefix entries", f.P.length], ["query", q ? `${q[0]}..${q[1]} = ${f.P[q[1] + 1] - f.P[q[0]]}` : "–"]]);
      }
    };
    const player = a.player(ui.controls, render);
    function build() { code.setLines(AT[tech].code); player.load(atFrames(tech, state.arr, state)); }
    sync();
    build();
  });

  /* =====================================================================
   * recursion-tree
   * ===================================================================== */
  const RT = {
    fib: { name: "fib(n)", def: 5, max: 8, maxMemo: 15, code: ["def fib(n):", "    if n < 2:", "        return n", "    return fib(n - 1) + fib(n - 2)"],
      memoCode: ["def fib(n, memo={}):", "    if n in memo: return memo[n]   # cache hit", "    if n < 2: return n", "    memo[n] = fib(n - 1) + fib(n - 2)", "    return memo[n]"] },
    factorial: { name: "factorial(n)", def: 5, max: 10, code: ["def fact(n):", "    if n <= 1:", "        return 1", "    return n * fact(n - 1)"] },
    hanoi: { name: "hanoi(n)", def: 3, max: 5, code: ["def hanoi(n, src, dst, via):", "    if n == 1:", "        move(src, dst); return", "    hanoi(n - 1, src, via, dst)", "    move(src, dst)", "    hanoi(n - 1, via, dst, src)"] },
    permutations: { name: "permutations", def: 3, max: 4, code: ["def permute(prefix, rest):", "    if not rest:", "        out.append(prefix); return", "    for i in range(len(rest)):", "        permute(prefix + [rest[i]], rest[:i] + rest[i + 1:])"] },
    "merge-sort": { name: "merge_sort", def: 6, max: 10, code: ["def merge_sort(a):", "    if len(a) <= 1:", "        return a", "    mid = len(a) // 2", "    left = merge_sort(a[:mid])", "    right = merge_sort(a[mid:])", "    return merge(left, right)"] },
    "power-set": { name: "subsets", def: 3, max: 4, code: ["def subsets(i, chosen):", "    if i == len(items):", "        out.append(chosen); return", "    subsets(i + 1, chosen)                # skip items[i]", "    subsets(i + 1, chosen + [items[i]])   # take items[i]"] },
  };

  function recTree(fn, n, memo, mergeInput) {
    const nodes = [], frames = [], status = [], result = [], stack = [];
    let calls = 0, hits = 0;
    const extra = { out: [] };
    const snap = (line, msg) => frames.push({ count: nodes.length, status: [...status], result: [...result], line, msg, calls, hits, depth: stack.length, out: [...extra.out] });
    const make = (label) => {
      const id = nodes.length;
      const parent = stack.length ? stack[stack.length - 1] : null;
      const node = { id, label, children: [] };
      nodes.push(node);
      if (parent !== null) nodes[parent].children.push(node);
      calls++;
      return id;
    };
    const enter = (label, line = 0) => {
      const id = make(label);
      if (stack.length) status[stack[stack.length - 1]] = "stack";
      status[id] = "active"; result[id] = null; stack.push(id);
      snap(line, `call ${label} (stack depth ${stack.length})`);
      return id;
    };
    const leave = (id, res, line, msg) => {
      result[id] = String(res); status[id] = "done"; stack.pop();
      if (stack.length) status[stack[stack.length - 1]] = "active";
      snap(line, msg || `${nodes[id].label} returns ${res}`);
      return res;
    };
    const step = (line, msg) => snap(line, msg);
    if (fn === "fib") {
      const cache = new Map();
      const f = (k) => {
        if (memo && cache.has(k)) {
          const id = make(`fib(${k})`);
          status[id] = "hit"; result[id] = String(cache.get(k)); hits++;
          snap(1, `fib(${k}) is already in memo: return ${cache.get(k)} immediately. Its whole subtree is pruned.`);
          return cache.get(k);
        }
        const id = enter(`fib(${k})`, 0);
        if (k < 2) return leave(id, k, memo ? 2 : 2, `fib(${k}) is a base case: return ${k}.`);
        const v = f(k - 1) + f(k - 2);
        if (memo) cache.set(k, v);
        return leave(id, v, memo ? 3 : 3, `fib(${k}) = fib(${k - 1}) + fib(${k - 2}) = ${v}${memo ? `; store memo[${k}] = ${v}` : ""}.`);
      };
      f(n);
    } else if (fn === "factorial") {
      const f = (k) => {
        const id = enter(`fact(${k})`);
        if (k <= 1) return leave(id, 1, 2, `fact(${k}) is the base case: return 1.`);
        const v = k * f(k - 1);
        return leave(id, v, 3, `fact(${k}) = ${k} * fact(${k - 1}) = ${v}.`);
      };
      f(n);
    } else if (fn === "hanoi") {
      const f = (k, src, dst, via) => {
        const id = enter(`h(${k},${src}→${dst})`);
        if (k === 1) { extra.out.push(`${src}→${dst}`); return leave(id, 1, 2, `Move disk 1 from ${src} to ${dst} (move #${extra.out.length}).`); }
        const m1 = f(k - 1, src, via, dst);
        extra.out.push(`${src}→${dst}`);
        step(4, `Move disk ${k} from ${src} to ${dst} (move #${extra.out.length}).`);
        const m2 = f(k - 1, via, dst, src);
        return leave(id, m1 + m2 + 1, 5, `hanoi(${k}) done: ${m1 + m2 + 1} moves = 2^${k} - 1.`);
      };
      f(n, "A", "C", "B");
    } else if (fn === "permutations") {
      const items = range(n).map((i) => i + 1);
      const f = (prefix, rest) => {
        const id = enter(`[${prefix.join("")}]`);
        if (!rest.length) { extra.out.push(prefix.join("")); return leave(id, "✓", 2, `rest is empty: record permutation ${prefix.join("")} (#${extra.out.length}).`); }
        rest.forEach((x, i) => f([...prefix, x], [...rest.slice(0, i), ...rest.slice(i + 1)]));
        return leave(id, "", 4, `All choices after [${prefix.join(", ")}] explored.`);
      };
      f([], items);
    } else if (fn === "merge-sort") {
      const f = (arr) => {
        const id = enter(`[${arr.join(",")}]`);
        if (arr.length <= 1) return leave(id, `[${arr}]`, 2, `[${arr}] has at most one item: already sorted.`);
        const mid = arr.length >> 1;
        const l = f(arr.slice(0, mid)), r = f(arr.slice(mid));
        const m = [];
        let i = 0, j = 0;
        while (i < l.length && j < r.length) m.push(l[i] <= r[j] ? l[i++] : r[j++]);
        const res = [...m, ...l.slice(i), ...r.slice(j)];
        leave(id, `[${res}]`, 6, `merge([${l}], [${r}]) = [${res}].`);
        return res;
      };
      const g = (arr) => { const res = f(arr); return res; };
      g(mergeInput);
      nodes.forEach(() => {});
    } else if (fn === "power-set") {
      const items = "abcd".slice(0, n).split("");
      const f = (i, chosen) => {
        const id = enter(`${i}:{${chosen.join("")}}`);
        if (i === items.length) { extra.out.push(`{${chosen.join(",")}}`); return leave(id, "✓", 2, `All items decided: record {${chosen.join(", ")}}.`); }
        step(3, `Branch 1: skip '${items[i]}'.`);
        f(i + 1, chosen);
        step(4, `Branch 2: take '${items[i]}'.`);
        f(i + 1, [...chosen, items[i]]);
        return leave(id, "", 4, `Both choices for '${items[i]}' explored.`);
      };
      f(0, []);
    }
    // merge-sort results are arrays: normalize labels in the result list
    return { nodes, frames };
  }

  registerViz("recursion-tree", (el, config, a) => {
    let fn = RT[config.fn] ? config.fn : "fib";
    let n = Number(config.n) || RT[fn].def;
    let memo = !!config.memo;
    const init = { fn, n, memo };
    let mergeInput = range(n).map(() => a.randInt(1, 9));
    const ui = a.shell(el, { title: config.title || "Recursion call tree" });
    const { main, side } = split(ui.stage, "250px");
    const holder = h("div"), stats = statsBar();
    main.append(stats.el, holder);
    const code = codePanel();
    const outBox = h("div", { style: "margin-top:8px" });
    side.append(code.el, outBox);
    ui.setLegend([["active call", COL.cmp], ["on the call stack", soft(COL.key, 55)], ["returned", COL.done], ["memo hit (pruned)", soft(COL.pivot, 55)]]);
    const inputs = inputRow(ui);
    const fnSel = a.select(Object.entries(RT).map(([k, v]) => [k, v.name]), fn, (v) => { fn = v; n = RT[v].def; nIn.value = n; build(); });
    const nIn = numInput(n, { min: 1, max: 15, "aria-label": "n" });
    const memoBox = h("input", { type: "checkbox", "aria-label": "Memoize" });
    memoBox.checked = memo;
    memoBox.addEventListener("change", () => { memo = memoBox.checked; build(); });
    const memoLabel = a.label("memoize", memoBox);
    inputs.append(a.label("function", fnSel), a.label("n", nIn), memoLabel,
      a.button("Apply", () => { n = Math.round(Number(nIn.value)) || RT[fn].def; build(); }),
      a.button("Random input", () => { mergeInput = range(n).map(() => a.randInt(1, 9)); build(); }),
      a.button("Reset", () => { ({ fn, n, memo } = init); fnSel.value = fn; nIn.value = n; memoBox.checked = memo; build(); }));
    let tree = null, pos = null, layout = null;
    const render = (f) => {
      const { nodes } = tree;
      const maxLabel = Math.max(...nodes.map((x) => x.label.length), 4);
      const cellW = Math.max(44, maxLabel * 7 + 12), levelH = 58;
      const W = Math.max(layout.width * cellW, 200), H = layout.depth * levelH + 10;
      const svg = svgBox(W, H, { minScale: W > 900 ? 0.9 : 0.55 });
      const P = (node) => ({ x: pos.get(node).x * cellW + cellW / 2, y: pos.get(node).y * levelH + 22 });
      nodes.forEach((node) => {
        if (node.id >= f.count) return;
        node.children.forEach((c) => {
          if (c.id >= f.count) return;
          const p1 = P(node), p2 = P(c);
          const hot = (f.status[c.id] === "active" || f.status[c.id] === "stack");
          svg.append(line(p1.x, p1.y + 11, p2.x, p2.y - 11, hot ? COL.key : COL.edge, hot ? 3 : 1.3));
        });
      });
      nodes.forEach((node) => {
        if (node.id >= f.count) return;
        const { x, y } = P(node);
        const st = f.status[node.id];
        const fill = st === "active" ? COL.cmp : st === "stack" ? soft(COL.key, 55) : st === "hit" ? soft(COL.pivot, 55) : COL.done;
        const w = node.label.length * 7 + 10;
        svg.append(rect(x - w / 2, y - 11, w, 22, fill, { rx: 11, stroke: st === "active" ? COL.key : COL.border, sw: st === "active" ? 2 : 1 }));
        svg.append(txt(x, y, node.label, { size: 11 }));
        const r = f.result[node.id];
        if (r !== null && r !== undefined && r !== "") svg.append(txt(x, y + 20, `→ ${r}`, { size: 10, fill: st === "hit" ? COL.pivot : COL.muted, weight: 700 }));
      });
      holder.replaceChildren(svg);
      const st = [["calls so far", f.calls], ["total calls", tree.nodes.length], ["stack depth", f.depth]];
      if (fn === "fib") st.push(["memo hits", f.hits]);
      stats.set(st);
      code.set(f.line);
      ui.setLog(esc(f.msg));
      const outName = { hanoi: "moves", permutations: "permutations", "power-set": "subsets" }[fn];
      outBox.innerHTML = outName ? sideBox(`${outName} (${f.out.length})`, f.out.map((o) => chip(o)).join("")) : "";
    };
    const player = a.player(ui.controls, render);
    function build() {
      const spec = RT[fn];
      const max = fn === "fib" && memo ? spec.maxMemo : spec.max;
      n = clamp(n, fn === "merge-sort" ? 1 : 1, max);
      nIn.value = n;
      memoLabel.style.opacity = fn === "fib" ? 1 : 0.45;
      memoBox.disabled = fn !== "fib";
      if (fn === "merge-sort" && mergeInput.length !== n) mergeInput = range(n).map(() => a.randInt(1, 9));
      tree = recTree(fn, n, memo && fn === "fib", mergeInput);
      layout = api.layoutTree(tree.nodes[0], (x) => x.children);
      pos = layout.pos;
      code.setLines(fn === "fib" && memo ? spec.memoCode : spec.code);
      const frames = tree.frames;
      const last = frames[frames.length - 1];
      let tail = `Finished: ${tree.nodes.length} calls in total.`;
      if (fn === "fib") {
        const naive = (k) => (k < 2 ? 1 : naive(k - 1) + naive(k - 2) + 1);
        tail += memo ? ` Without memoization fib(${n}) makes ${naive(n)} calls.` : ` Calls grow like φ^n ≈ 1.618^n; turn on memoize to see the subtree pruning.`;
      }
      if (n >= max && fn !== "merge-sort") tail += ` (n is capped at ${max} here so the tree stays readable.)`;
      frames.push({ ...last, msg: tail });
      player.load(frames);
    }
    build();
  });

  /* =====================================================================
   * graph
   * ===================================================================== */
  const GRAPH_PRESETS = (() => {
    const mk = (directed, weighted, coords, edges) => ({
      directed, weighted,
      nodes: Object.entries(coords).map(([id, [x, y]]) => ({ id, x, y })),
      edges: edges.map(([u, v, w]) => ({ u, v, w: w ?? 1 })),
    });
    const grid = (() => {
      const coords = {}, edges = [];
      const name = (r, c) => "ABCDEFGHIJKL"[r * 4 + c];
      for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
        coords[name(r, c)] = [90 + c * 150, 60 + r * 120];
        if (c < 3) edges.push([name(r, c), name(r, c + 1), ((r * 7 + c * 3) % 5) + 1]);
        if (r < 2) edges.push([name(r, c), name(r + 1, c), ((r * 3 + c * 5 + 2) % 5) + 1]);
      }
      return mk(false, true, coords, edges);
    })();
    return {
      small: mk(false, false, { A: [80, 80], B: [240, 50], C: [400, 80], D: [130, 230], E: [300, 190], F: [500, 210], G: [320, 320] },
        [["A", "B"], ["A", "D"], ["B", "C"], ["B", "E"], ["C", "F"], ["D", "E"], ["D", "G"], ["E", "F"], ["E", "G"], ["F", "G"]]),
      weighted: mk(false, true, { A: [70, 180], B: [210, 60], C: [210, 300], D: [400, 60], E: [400, 300], F: [560, 180] },
        [["A", "B", 4], ["A", "C", 2], ["B", "C", 1], ["B", "D", 5], ["C", "D", 8], ["C", "E", 10], ["D", "E", 2], ["D", "F", 6], ["E", "F", 3]]),
      dag: mk(true, true, { A: [60, 180], B: [190, 70], C: [190, 290], D: [340, 70], E: [340, 290], F: [480, 180], G: [600, 70] },
        [["A", "B", 3], ["A", "C", 6], ["B", "C", 2], ["B", "D", 4], ["C", "E", 1], ["E", "D", 1], ["D", "F", 2], ["E", "F", 5], ["F", "G", 1], ["D", "G", 7]]),
      grid,
    };
  })();
  const GRAPH_ALGOS = { bfs: "Breadth-first search", dfs: "Depth-first search", dijkstra: "Dijkstra", "bellman-ford": "Bellman-Ford", topo: "Topological sort (Kahn)", prim: "Prim's MST", kruskal: "Kruskal's MST" };

  function graphFrames(G, algo, start) {
    const F = [];
    const ids = G.nodes.map((n) => n.id);
    const ekey = (u, v) => (G.directed ? `${u}>${v}` : [u, v].sort().join("-"));
    const adj = Object.fromEntries(ids.map((i) => [i, []]));
    G.edges.forEach((e) => { adj[e.u].push({ v: e.v, w: e.w }); if (!G.directed) adj[e.v].push({ v: e.u, w: e.w }); });
    Object.values(adj).forEach((l) => l.sort((x, y) => x.v.localeCompare(y.v)));
    const ns = {}, es = {};
    let dist = null;
    const push = (msg, side) => F.push({ ns: { ...ns }, es: { ...es }, dist: dist ? { ...dist } : null, msg, side });
    const order = [];
    const orderBox = () => sideBox("visit order", order.map((x) => chip(x, COL.done)).join("") || "–");

    if (algo === "bfs") {
      const q = [start], seen = new Set([start]), level = { [start]: 0 };
      ns[start] = "frontier";
      const side = () => sideBox("queue (front → back)", q.map((x) => chip(x, soft(COL.key, 50))).join("") || "empty") + orderBox() + sideBox("level (edges from start)", Object.entries(level).map(([k, v]) => chip(`${k}:${v}`)).join(""));
      push(`Enqueue the start node ${start} and mark it seen.`, side());
      while (q.length) {
        const u = q.shift();
        ns[u] = "current"; order.push(u);
        push(`Dequeue ${u} (FIFO: oldest first). Look at its neighbours.`, side());
        for (const { v } of adj[u]) {
          const k = ekey(u, v);
          if (!seen.has(v)) {
            seen.add(v); level[v] = level[u] + 1; q.push(v); ns[v] = "frontier"; es[k] = "tree";
            push(`${v} is new: mark seen, level ${level[v]}, enqueue it.`, side());
          } else if (es[k] !== "tree") {
            const prev = es[k]; es[k] = "consider";
            push(`${v} was already seen; skip it.`, side());
            es[k] = prev;
          }
        }
        ns[u] = "done";
      }
      push(`BFS finished. Tree edges give shortest paths by edge count from ${start}.`, side());
    } else if (algo === "dfs") {
      const seen = new Set(), stack = [];
      const side = () => sideBox("call stack (bottom → top)", stack.map((x) => chip(x, soft(COL.key, 50))).join("") || "empty") + orderBox();
      const dfs = (u) => {
        seen.add(u); stack.push(u); order.push(u); ns[u] = "current";
        push(`dfs(${u}): mark visited and explore its neighbours in order.`, side());
        for (const { v } of adj[u]) {
          const k = ekey(u, v);
          if (!seen.has(v)) {
            es[k] = "tree"; ns[u] = "frontier";
            push(`Edge ${u}–${v}: ${v} is unvisited, so go deeper.`, side());
            dfs(v);
            ns[u] = "current";
            push(`Back in dfs(${u}) after finishing ${v}.`, side());
          } else if (es[k] !== "tree") {
            es[k] = "consider";
            push(`Edge ${u}–${v}: ${v} already visited, skip.`, side());
            delete es[k];
          }
        }
        stack.pop(); ns[u] = "done";
        push(`dfs(${u}) returns: all neighbours explored.`, side());
      };
      dfs(start);
      push(`DFS finished. Visit order: ${order.join(" → ")}.`, side());
    } else if (algo === "dijkstra" || algo === "bellman-ford") {
      dist = Object.fromEntries(ids.map((i) => [i, Infinity]));
      const prev = {};
      dist[start] = 0;
      const distTable = (hl) => sideBox("dist / prev", miniTable(["node", "dist", "prev"], ids.map((i) => ({ cells: [i, fmt(dist[i]), prev[i] || "–"], hl: i === hl }))));
      const markTree = () => { Object.keys(es).forEach((k) => { if (es[k] === "tree") delete es[k]; }); Object.entries(prev).forEach(([v, u]) => { es[ekey(u, v)] = "tree"; }); };
      if (algo === "dijkstra") {
        const pq = [[0, start]];
        const done = new Set();
        const side = (hl) => sideBox("priority queue (dist, node)", pq.slice().sort((x, y) => x[0] - y[0] || x[1].localeCompare(y[1])).map(([d, v]) => chip(`(${d}, ${v})`, soft(COL.key, 50))).join("") || "empty") + distTable(hl);
        ns[start] = "frontier";
        push(`dist[${start}] = 0, every other node ∞. Push (0, ${start}).`, side(start));
        while (pq.length) {
          pq.sort((x, y) => x[0] - y[0] || x[1].localeCompare(y[1]));
          const [d, u] = pq.shift();
          if (done.has(u)) { push(`Pop (${d}, ${u}): ${u} is already final, so this entry is stale. Skip.`, side(u)); continue; }
          done.add(u); ns[u] = "current"; order.push(u);
          push(`Pop the smallest (${d}, ${u}). dist[${u}] = ${d} is now final.`, side(u));
          for (const { v, w } of adj[u]) {
            if (done.has(v)) continue;
            const k = ekey(u, v), old = es[k];
            es[k] = "consider";
            if (d + w < dist[v]) {
              const was = dist[v];
              dist[v] = d + w; prev[v] = u; pq.push([dist[v], v]); ns[v] = "frontier";
              push(`Relax ${u}→${v}: ${d} + ${w} = ${d + w} < ${fmt(was)}. Update dist[${v}] and push (${dist[v]}, ${v}).`, side(v));
            } else push(`Relax ${u}→${v}: ${d} + ${w} = ${d + w} ≥ ${dist[v]}. No improvement.`, side(v));
            es[k] = old;
            markTree();
          }
          ns[u] = "done";
        }
        push(`Dijkstra finished. The highlighted edges form the shortest-path tree from ${start}.`, distTable());
      } else {
        const dedges = [];
        G.edges.forEach((e) => { dedges.push([e.u, e.v, e.w]); if (!G.directed) dedges.push([e.v, e.u, e.w]); });
        ns[start] = "current";
        push(`dist[${start}] = 0. Relax all ${dedges.length} directed edges, up to V - 1 = ${ids.length - 1} rounds.`, distTable(start));
        let round = 0;
        for (round = 1; round < ids.length; round++) {
          let changed = false;
          for (const [u, v, w] of dedges) {
            const k = ekey(u, v), old = es[k];
            es[k] = "consider";
            if (dist[u] !== Infinity && dist[u] + w < dist[v]) {
              const was = dist[v];
              dist[v] = dist[u] + w; prev[v] = u; changed = true; ns[v] = "frontier";
              markTree(); es[k] = "consider";
              push(`Round ${round}: ${u}→${v}: ${dist[u]} + ${w} = ${dist[v]} < ${fmt(was)}. Update.`, distTable(v));
            } else push(`Round ${round}: ${u}→${v}: ${dist[u] === Infinity ? `dist[${u}] is ∞, nothing to relax` : `${dist[u]} + ${w} ≥ ${fmt(dist[v])}, no change`}.`, distTable(v));
            es[k] = old; markTree();
          }
          if (!changed) { push(`Round ${round} changed nothing, so the distances are final. Stop early.`, distTable()); break; }
          push(`End of round ${round}: shortest paths using up to ${round} edges are known.`, distTable());
        }
        const neg = dedges.some(([u, v, w]) => dist[u] !== Infinity && dist[u] + w < dist[v]);
        ids.forEach((i) => { if (dist[i] !== Infinity) ns[i] = "done"; });
        push(neg ? "One more pass still improves a distance: there is a negative cycle." : "A final check pass finds no improvement: no negative cycles. Bellman-Ford also works with negative weights, at O(V·E).", distTable());
      }
    } else if (algo === "topo") {
      if (!G.directed) { push("Topological order only exists for a directed acyclic graph. Choose the dag preset.", ""); return F; }
      const indeg = Object.fromEntries(ids.map((i) => [i, 0]));
      G.edges.forEach((e) => indeg[e.v]++);
      const q = ids.filter((i) => indeg[i] === 0);
      q.forEach((i) => { ns[i] = "frontier"; });
      const side = (hl) => sideBox("queue (in-degree 0)", q.map((x) => chip(x, soft(COL.key, 50))).join("") || "empty") + sideBox("order", order.map((x) => chip(x, COL.done)).join("") || "–") + sideBox("in-degree", miniTable(["node", "in"], ids.map((i) => ({ cells: [i, ns[i] === "done" ? "✓" : indeg[i]], hl: i === hl }))));
      push(`Count incoming edges. Nodes with in-degree 0 (${q.join(", ")}) have no prerequisites: queue them.`, side());
      while (q.length) {
        const u = q.shift();
        order.push(u); ns[u] = "current";
        push(`Take ${u} and append it to the order.`, side(u));
        for (const { v } of adj[u]) {
          const k = ekey(u, v);
          indeg[v]--; es[k] = "tree";
          if (indeg[v] === 0) { q.push(v); ns[v] = "frontier"; push(`Remove edge ${u}→${v}: in-degree of ${v} drops to 0, enqueue it.`, side(v)); }
          else push(`Remove edge ${u}→${v}: in-degree of ${v} is now ${indeg[v]}.`, side(v));
        }
        ns[u] = "done";
      }
      push(order.length === ids.length ? `Topological order: ${order.join(" → ")}. Every edge points forward in this order.` : `Only ${order.length} of ${ids.length} nodes were output: the graph has a cycle.`, side());
    } else if (algo === "prim" || algo === "kruskal") {
      if (G.directed) { push("Minimum spanning trees are defined for undirected graphs. Choose small, weighted, or grid.", ""); return F; }
      let total = 0;
      const mst = [];
      const mstBox = () => sideBox(`MST edges (total weight ${total})`, mst.map((x) => chip(x, soft(COL.path, 45))).join("") || "–");
      if (algo === "prim") {
        const inTree = new Set([start]);
        const pq = adj[start].map(({ v, w }) => [w, start, v]);
        ns[start] = "done";
        const side = () => sideBox("priority queue (w, u, v)", pq.slice().sort((x, y) => x[0] - y[0] || (x[1] + x[2]).localeCompare(y[1] + y[2])).map(([w, u, v]) => chip(`(${w}, ${u}${v})`, soft(COL.key, 50))).join("") || "empty") + mstBox();
        push(`Start the tree at ${start}; push its edges into the priority queue.`, side());
        while (pq.length && inTree.size < ids.length) {
          pq.sort((x, y) => x[0] - y[0] || (x[1] + x[2]).localeCompare(y[1] + y[2]));
          const [w, u, v] = pq.shift();
          const k = ekey(u, v);
          if (inTree.has(v)) { es[k] = "rejected"; push(`Pop (${w}, ${u}${v}): ${v} is already in the tree, so this edge would make a cycle. Skip.`, side()); continue; }
          inTree.add(v); es[k] = "tree"; ns[v] = "done"; total += w; mst.push(`${u}${v}:${w}`);
          adj[v].forEach((e) => { if (!inTree.has(e.v)) pq.push([e.w, v, e.v]); });
          push(`Pop the cheapest crossing edge (${w}, ${u}${v}): add ${v} to the tree and push its edges.`, side());
        }
        push(`Prim finished: MST weight ${total}.`, side());
      } else {
        const parent = Object.fromEntries(ids.map((i) => [i, i]));
        const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
        const sets = () => { const g = {}; ids.forEach((i) => { (g[find(i)] ||= []).push(i); }); return Object.values(g).map((x) => `{${x.join("")}}`); };
        const sorted = [...G.edges].sort((x, y) => x.w - y.w || (x.u + x.v).localeCompare(y.u + y.v));
        let at = 0;
        const side = () => sideBox("union-find sets", sets().map((x) => chip(x, soft(COL.teal, 35))).join("")) + sideBox("edges by weight", sorted.map((e, i) => chip(`${e.u}${e.v}:${e.w}`, i < at ? COL.sunk : i === at ? COL.cmp : COL.node)).join("")) + mstBox();
        push("Sort the edges by weight. Every node starts in its own set.", side());
        for (; at < sorted.length; at++) {
          const e = sorted[at], k = ekey(e.u, e.v);
          es[k] = "consider";
          const ru = find(e.u), rv = find(e.v);
          push(`Edge ${e.u}${e.v} (w=${e.w}): find(${e.u}) = ${ru}, find(${e.v}) = ${rv}.`, side());
          if (ru === rv) { es[k] = "rejected"; push(`Same set: adding ${e.u}${e.v} would close a cycle. Reject it.`, side()); }
          else { parent[ru] = rv; es[k] = "tree"; ns[e.u] = ns[e.v] = "done"; total += e.w; mst.push(`${e.u}${e.v}:${e.w}`); push(`Different sets: accept ${e.u}${e.v} and union the sets.`, side()); }
          if (mst.length === ids.length - 1) { at++; push(`${mst.length} edges = V - 1: the MST is complete, weight ${total}.`, side()); break; }
        }
      }
    }
    return F;
  }

  registerViz("graph", (el, config, a) => {
    let preset = GRAPH_PRESETS[config.preset] ? config.preset : "small";
    const algos = Array.isArray(config.algorithms) ? config.algorithms.filter((x) => GRAPH_ALGOS[x]) : Object.keys(GRAPH_ALGOS);
    if (!algos.length) algos.push("bfs");
    let algo = algos.includes(config.default) ? config.default : algos[0];
    if (!config.preset) preset = algo === "topo" ? "dag" : ["dijkstra", "bellman-ford", "prim", "kruskal"].includes(algo) ? "weighted" : "small";
    let start = config.start || "A";
    const init = { preset, algo, start };
    const ui = a.shell(el, { title: config.title || "Graph algorithms" });
    const { main, side } = split(ui.stage, "230px");
    const holder = h("div");
    main.append(holder);
    ui.setLegend([["current", COL.cmp], ["frontier / queued", soft(COL.key, 55)], ["finished", COL.done], ["tree / chosen edge", COL.path], ["edge being checked", COL.key], ["rejected", COL.swap]]);
    const inputs = inputRow(ui);
    const presetSel = a.select(Object.keys(GRAPH_PRESETS).map((k) => [k, k]), preset, (v) => { preset = v; fillStart(); build(); });
    const algoSel = a.select(algos.map((k) => [k, GRAPH_ALGOS[k]]), algo, (v) => { algo = v; build(); });
    const startSel = h("select", { "aria-label": "Start node" });
    startSel.addEventListener("change", () => { start = startSel.value; build(); });
    function fillStart() {
      const ids = GRAPH_PRESETS[preset].nodes.map((n) => n.id);
      if (!ids.includes(start)) start = ids[0];
      startSel.replaceChildren(...ids.map((i) => h("option", { value: i, text: i })));
      startSel.value = start;
    }
    inputs.append(a.label("graph", presetSel), a.label("algorithm", algoSel), a.label("start", startSel),
      a.button("Reset", () => { ({ preset, algo, start } = init); presetSel.value = preset; algoSel.value = algo; fillStart(); build(); }));
    const render = (f) => {
      const G = GRAPH_PRESETS[preset];
      const W = 660, H = 370;
      const svg = svgBox(W, H);
      const at = Object.fromEntries(G.nodes.map((n) => [n.id, n]));
      const ekey = (u, v) => (G.directed ? `${u}>${v}` : [u, v].sort().join("-"));
      G.edges.forEach((e) => {
        const p = at[e.u], q = at[e.v];
        const st = f.es[ekey(e.u, e.v)];
        const color = st === "tree" ? COL.path : st === "consider" ? COL.key : st === "rejected" ? COL.swap : COL.edge;
        const sw = st ? 3.5 : 1.6;
        const dx = q.x - p.x, dy = q.y - p.y, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
        const x2 = q.x - ux * 21, y2 = q.y - uy * 21;
        svg.append(line(p.x + ux * 19, p.y + uy * 19, x2, y2, color, sw, st === "rejected" ? "stroke-dasharray:6 4" : ""));
        if (G.directed) svg.append(s("polygon", { points: `${x2},${y2} ${x2 - ux * 11 - uy * 6},${y2 - uy * 11 + ux * 6} ${x2 - ux * 11 + uy * 6},${y2 - uy * 11 - ux * 6}`, style: `fill:${color}` }));
        if (G.weighted) {
          const mx = (p.x + q.x) / 2 - uy * 11, my = (p.y + q.y) / 2 + ux * 11;
          svg.append(rect(mx - 10, my - 9, 20, 18, "var(--bg-elev)", { stroke: "none", rx: 4, opacity: 0.9 }));
          svg.append(txt(mx, my, e.w, { size: 11, weight: 700, fill: st ? color : COL.muted }));
        }
      });
      G.nodes.forEach((n) => {
        const st = f.ns[n.id];
        const fill = st === "current" ? COL.cmp : st === "frontier" ? soft(COL.key, 55) : st === "done" ? COL.done : COL.node;
        svg.append(circle(n.x, n.y, 19, fill, n.id === start ? COL.pivot : COL.border, n.id === start ? 3 : 1.5));
        svg.append(txt(n.x, n.y, n.id, { size: 14, weight: 700 }));
        if (f.dist) svg.append(txt(n.x, n.y - 29, fmt(f.dist[n.id]), { size: 11, weight: 700, fill: COL.pivot }));
      });
      holder.replaceChildren(svg);
      side.innerHTML = f.side || "";
      ui.setLog(esc(f.msg));
    };
    const player = a.player(ui.controls, render);
    function build() { player.load(graphFrames(GRAPH_PRESETS[preset], algo, start)); }
    fillStart();
    build();
  });

  /* =====================================================================
   * grid-path
   * ===================================================================== */
  const GRID_ALGOS = { bfs: "BFS", dfs: "DFS", dijkstra: "Dijkstra", greedy: "Greedy best-first", astar: "A* (Manhattan)" };
  const MUD = 5;

  function gridSearch(grid, R, C, src, dst, algo) {
    const N = R * C;
    const cost = (i) => (grid[i] === 2 ? MUD : 1);
    const hman = (i) => Math.abs(Math.floor(i / C) - Math.floor(dst / C)) + Math.abs((i % C) - (dst % C));
    const nbrs = (i) => {
      const r = Math.floor(i / C), c = i % C, out = [];
      if (r > 0) out.push(i - C);
      if (c < C - 1) out.push(i + 1);
      if (r < R - 1) out.push(i + C);
      if (c > 0) out.push(i - 1);
      return out.filter((j) => grid[j] !== 1);
    };
    const parent = new Int32Array(N).fill(-1);
    const order = [], fronts = [];
    const closed = new Uint8Array(N);
    let found = false;
    if (algo === "bfs") {
      const seen = new Uint8Array(N);
      seen[src] = 1;
      const q = [src];
      while (q.length) {
        const u = q.shift();
        order.push(u); closed[u] = 1;
        if (u === dst) { found = true; fronts.push([...q]); break; }
        for (const v of nbrs(u)) if (!seen[v]) { seen[v] = 1; parent[v] = u; q.push(v); }
        fronts.push([...q]);
      }
    } else if (algo === "dfs") {
      const st = [[src, -1]];
      while (st.length) {
        const [u, p] = st.pop();
        if (closed[u]) continue;
        closed[u] = 1; parent[u] = p; order.push(u);
        if (u === dst) { found = true; fronts.push([...new Set(st.map((x) => x[0]))].filter((x) => !closed[x])); break; }
        nbrs(u).reverse().forEach((v) => { if (!closed[v]) st.push([v, u]); });
        fronts.push([...new Set(st.map((x) => x[0]))].filter((x) => !closed[x]));
      }
    } else {
      const g = new Float64Array(N).fill(Infinity);
      g[src] = 0;
      let seq = 0;
      const open = [[algo === "dijkstra" ? 0 : hman(src), 0, seq++, src]];
      while (open.length) {
        let bi = 0;
        for (let k = 1; k < open.length; k++) {
          const x = open[k], y = open[bi];
          if (x[0] < y[0] || (x[0] === y[0] && (x[1] < y[1] || (x[1] === y[1] && x[2] < y[2])))) bi = k;
        }
        const [, , , u] = open.splice(bi, 1)[0];
        if (closed[u]) continue;
        closed[u] = 1; order.push(u);
        if (u === dst) { found = true; fronts.push(open.map((x) => x[3]).filter((x) => !closed[x])); break; }
        for (const v of nbrs(u)) {
          if (closed[v]) continue;
          if (algo === "greedy") {
            if (parent[v] === -1 && v !== src) { parent[v] = u; open.push([hman(v), 0, seq++, v]); }
          } else {
            const ng = g[u] + cost(v);
            if (ng < g[v]) { g[v] = ng; parent[v] = u; open.push([algo === "astar" ? ng + hman(v) : ng, algo === "astar" ? hman(v) : 0, seq++, v]); }
          }
        }
        fronts.push([...new Set(open.map((x) => x[3]))].filter((x) => !closed[x]));
      }
    }
    const path = [];
    if (found) { for (let v = dst; v !== -1; v = parent[v]) { path.push(v); if (v === src) break; } path.reverse(); }
    const pcost = path.slice(1).reduce((t, i) => t + cost(i), 0);
    return { order, fronts, path, found, cost: pcost };
  }

  registerViz("grid-path", (el, config, a) => {
    const R = clamp(Number(config.rows) || 12, 4, 30), C = clamp(Number(config.cols) || 22, 4, 40);
    const algos = Array.isArray(config.algorithms) ? config.algorithms.filter((x) => GRID_ALGOS[x]) : Object.keys(GRID_ALGOS);
    if (!algos.length) algos.push("bfs");
    let algo = algos.includes(config.default) ? config.default : algos.includes("astar") ? "astar" : algos[0];
    const N = R * C;
    let grid = new Uint8Array(N);
    let src = Math.floor(R / 2) * C + 2, dst = Math.floor(R / 2) * C + C - 3;
    const defaultWalls = () => {
      const g = new Uint8Array(N);
      const wc = Math.floor(C / 2);
      for (let r = 1; r < R - 1; r++) g[r * C + wc] = 1;
      for (let r = Math.floor(R / 2) - 1; r <= Math.floor(R / 2) + 1; r++) for (let c = wc + 2; c < Math.min(C - 4, wc + 5); c++) g[r * C + c] = 2;
      return g;
    };
    grid = Array.isArray(config.walls) ? (() => { const g = new Uint8Array(N); config.walls.forEach(([r, c]) => { if (r < R && c < C) g[r * C + c] = 1; }); return g; })() : defaultWalls();
    const initGrid = grid.slice();
    const ui = a.shell(el, { title: config.title || "Grid path finding" });
    const { main, side } = split(ui.stage, "230px");
    const stats = statsBar();
    const cs = 26, W = C * cs, H = R * cs;
    const svg = svgBox(W, H, { minScale: 0.8 });
    svg.style.touchAction = "none";
    svg.style.cursor = "crosshair";
    const cells = range(N).map((i) => {
      const r = rect((i % C) * cs + 1, Math.floor(i / C) * cs + 1, cs - 2, cs - 2, COL.node, { rx: 3, stroke: "var(--border)" });
      svg.append(r);
      return r;
    });
    const marks = s("g");
    svg.append(marks);
    main.append(stats.el, svg);
    ui.setLegend([["start", COL.pivot], ["goal", COL.swap], ["wall", "var(--fg-muted)"], [`mud (cost ${MUD})`, soft(COL.key, 60)], ["frontier", COL.cmp], ["visited", soft(COL.base, 40)], ["path", COL.path]]);
    const inputs = inputRow(ui);
    let tool = "wall";
    const algoSel = a.select(algos.map((k) => [k, GRID_ALGOS[k]]), algo, (v) => { algo = v; build(); });
    const toolSel = a.select([["wall", "draw walls"], ["mud", "draw mud"], ["erase", "erase"], ["start", "move start"], ["goal", "move goal"]], tool, (v) => { tool = v; });
    inputs.append(a.label("algorithm", algoSel), a.label("tool", toolSel),
      a.button("Random walls", () => { grid = new Uint8Array(N).map(() => { const r = Math.random(); return r < 0.25 ? 1 : r < 0.33 ? 2 : 0; }); grid[src] = grid[dst] = 0; build(); }),
      a.button("Clear", () => { grid = new Uint8Array(N); build(); }),
      a.button("Reset", () => { grid = initGrid.slice(); src = Math.floor(R / 2) * C + 2; dst = Math.floor(R / 2) * C + C - 3; build(); }));
    const baseFill = (i) => (i === src ? COL.pivot : i === dst ? COL.swap : grid[i] === 1 ? "var(--fg-muted)" : grid[i] === 2 ? soft(COL.key, 60) : COL.node);
    let result = null;
    const render = (f) => {
      const vis = new Set(result.order.slice(0, f.k));
      const fr = new Set(f.front || []);
      const onPath = new Set(result.path.slice(0, f.p));
      for (let i = 0; i < N; i++) {
        let fill = baseFill(i);
        if (i !== src && i !== dst) {
          if (onPath.has(i)) fill = COL.path;
          else if (fr.has(i)) fill = COL.cmp;
          else if (vis.has(i)) fill = grid[i] === 2 ? `color-mix(in srgb, var(--viz-1) 40%, var(--viz-2))` : soft(COL.base, 40);
        }
        cells[i].style.fill = fill;
      }
      marks.replaceChildren(txt((src % C) * cs + cs / 2, Math.floor(src / C) * cs + cs / 2, "S", { size: 12, weight: 700, fill: "var(--viz-node)" }), txt((dst % C) * cs + cs / 2, Math.floor(dst / C) * cs + cs / 2, "G", { size: 12, weight: 700, fill: "var(--viz-node)" }));
      stats.set([["algorithm", GRID_ALGOS[algo]], ["visited", Math.min(f.k, result.order.length)], ["path steps", f.p ? Math.max(0, result.path.length - 1) : "–"], ["path cost", f.p ? result.cost : "–"]]);
      ui.setLog(esc(f.msg));
    };
    const player = a.player(ui.controls, render, { speed: 120 });
    const explain = {
      bfs: "BFS expands cells in rings of equal step count. Shortest in steps, but it ignores mud cost.",
      dfs: "DFS dives along one direction as far as it can. It finds a path, usually not a short one.",
      dijkstra: `Dijkstra expands the cheapest-so-far cell first, so it routes around mud (cost ${MUD}) when that is cheaper.`,
      greedy: "Greedy best-first always expands the cell that looks closest to the goal (Manhattan distance). Fast, but not optimal.",
      astar: "A* orders cells by f = g (cost so far) + h (Manhattan distance to goal). Optimal like Dijkstra, with far fewer visits.",
    };
    function compare() {
      const rows = algos.map((k) => {
        const r = gridSearch(grid, R, C, src, dst, k);
        return { cells: [GRID_ALGOS[k].replace(" (Manhattan)", ""), r.order.length, r.found ? r.path.length - 1 : "–", r.found ? r.cost : "none"], hl: k === algo };
      });
      side.innerHTML = sideBox("comparison", miniTable(["algorithm", "visited", "steps", "cost"], rows)) +
        `<p style="color:var(--fg-muted);margin:6px 0 0">Click or drag on the grid to edit, then press Play. Mud cells cost ${MUD} to enter.</p>`;
    }
    function build() {
      result = gridSearch(grid, R, C, src, dst, algo);
      const frames = [{ k: 0, p: 0, front: [src], msg: `${explain[algo]} Press Play.` }];
      const stepEvery = Math.max(1, Math.ceil(result.order.length / 220));
      for (let k = 1; k <= result.order.length; k += stepEvery) {
        const u = result.order[k - 1];
        frames.push({ k, p: 0, front: result.fronts[k - 1], msg: `Expand cell (${Math.floor(u / C)}, ${u % C}). Visited ${k} cell${k === 1 ? "" : "s"} so far.` });
      }
      const K = result.order.length;
      if (result.found) {
        const L = result.path.length;
        const ps = Math.max(1, Math.ceil(L / 12));
        for (let p = ps; p < L + ps; p += ps) frames.push({ k: K, p: Math.min(p, L), front: [], msg: `Reached the goal after visiting ${K} cells. Follow parent pointers back to trace the path.` });
        frames.push({ k: K, p: L, front: [], msg: `${GRID_ALGOS[algo]}: ${K} cells visited, path of ${L - 1} steps with cost ${result.cost}.` });
      } else frames.push({ k: K, p: 0, front: [], msg: `The goal is unreachable: ${K} cells visited and the frontier is empty.` });
      player.load(frames);
      compare();
    }
    let painting = false, paintVal = 1;
    const cellAt = (e) => {
      const b = svg.getBoundingClientRect();
      const c = Math.floor(((e.clientX - b.left) / b.width) * C), r = Math.floor(((e.clientY - b.top) / b.height) * R);
      return r >= 0 && r < R && c >= 0 && c < C ? r * C + c : -1;
    };
    const paint = (i) => {
      if (i < 0) return;
      if (tool === "start" || tool === "goal") {
        if (grid[i] === 1 || i === (tool === "start" ? dst : src)) return;
        if (tool === "start") src = i; else dst = i;
        player.stop(); render({ k: 0, p: 0, front: [], msg: "Editing…" });
        cells.forEach((r, k) => { r.style.fill = baseFill(k); });
        return;
      }
      if (i === src || i === dst) return;
      grid[i] = paintVal;
      cells[i].style.fill = baseFill(i);
    };
    svg.addEventListener("pointerdown", (e) => {
      const i = cellAt(e);
      if (i < 0) return;
      player.stop();
      painting = true;
      paintVal = tool === "erase" ? 0 : tool === "mud" ? (grid[i] === 2 ? 0 : 2) : tool === "wall" ? (grid[i] === 1 ? 0 : 1) : 0;
      cells.forEach((r, k) => { r.style.fill = baseFill(k); });
      try { svg.setPointerCapture(e.pointerId); } catch (err) { /* pointer capture is optional */ void err; }
      paint(i);
      e.preventDefault();
    });
    svg.addEventListener("pointermove", (e) => { if (painting) paint(cellAt(e)); });
    const end = () => { if (painting) { painting = false; build(); } };
    svg.addEventListener("pointerup", end);
    svg.addEventListener("pointercancel", end);
    build();
  });

  /* =====================================================================
   * dp-table
   * ===================================================================== */
  const DP = {
    lcs: {
      name: "Longest common subsequence",
      code: [
        "dp = [[0] * (n + 1) for _ in range(m + 1)]",
        "for i in range(1, m + 1):",
        "    for j in range(1, n + 1):",
        "        if a[i - 1] == b[j - 1]:",
        "            dp[i][j] = dp[i - 1][j - 1] + 1",
        "        else:",
        "            dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])",
      ],
    },
    "edit-distance": {
      name: "Edit distance (Levenshtein)",
      code: [
        "dp[i][0] = i; dp[0][j] = j     # delete / insert everything",
        "for i in range(1, m + 1):",
        "    for j in range(1, n + 1):",
        "        if a[i - 1] == b[j - 1]:",
        "            dp[i][j] = dp[i - 1][j - 1]",
        "        else:",
        "            dp[i][j] = 1 + min(dp[i - 1][j],      # delete",
        "                               dp[i][j - 1],      # insert",
        "                               dp[i - 1][j - 1])  # replace",
      ],
    },
    knapsack: {
      name: "0/1 knapsack",
      code: [
        "dp = [[0] * (C + 1) for _ in range(n + 1)]",
        "for i, (w, v) in enumerate(items, 1):",
        "    for c in range(C + 1):",
        "        dp[i][c] = dp[i - 1][c]                  # skip item i",
        "        if w <= c:",
        "            dp[i][c] = max(dp[i][c], v + dp[i - 1][c - w])  # take it",
      ],
    },
    "coin-change": {
      name: "Coin change (fewest coins)",
      code: [
        "dp = [0] + [inf] * amount",
        "for x in range(1, amount + 1):",
        "    for c in coins:",
        "        if c <= x and dp[x - c] + 1 < dp[x]:",
        "            dp[x] = dp[x - c] + 1",
        "return dp[amount] if dp[amount] < inf else -1",
      ],
    },
    lis: {
      name: "Longest increasing subsequence",
      code: [
        "dp = [1] * n          # LIS ending at i",
        "for i in range(n):",
        "    for j in range(i):",
        "        if a[j] < a[i]:",
        "            dp[i] = max(dp[i], dp[j] + 1)",
        "return max(dp)",
      ],
    },
    "grid-paths": {
      name: "Grid paths (right/down moves)",
      code: [
        "dp[0][0] = 1",
        "for r in range(R):",
        "    for c in range(C):",
        "        if blocked(r, c): dp[r][c] = 0; continue",
        "        up = dp[r - 1][c] if r else 0",
        "        left = dp[r][c - 1] if c else 0",
        "        dp[r][c] += up + left",
      ],
    },
  };

  function dpFrames(problem, P) {
    const F = [];
    let rowH, colH, vals;
    const push = (line, msg, { cur = null, deps = [], rec = "", path = [] } = {}) =>
      F.push({ vals: vals.map((r) => [...r]), cur, deps, rec, path: new Set(path.map(([r, c]) => `${r},${c}`)), line, msg });
    const grid = (R, C, fill = null) => range(R).map(() => new Array(C).fill(fill));
    let answer = "";
    if (problem === "lcs" || problem === "edit-distance") {
      const a = [...P.a], b = [...P.b], m = a.length, n = b.length;
      rowH = ["ε", ...a]; colH = ["ε", ...b];
      vals = grid(m + 1, n + 1);
      const dp = grid(m + 1, n + 1, 0);
      const ed = problem === "edit-distance";
      for (let i = 0; i <= m; i++) { dp[i][0] = ed ? i : 0; vals[i][0] = dp[i][0]; }
      for (let j = 0; j <= n; j++) { dp[0][j] = ed ? j : 0; vals[0][j] = dp[0][j]; }
      push(0, ed ? `Base cases: turning a prefix of length i into "" takes i deletions; "" into b[:j] takes j insertions.` : "Row 0 and column 0 are 0: an empty string has no common subsequence with anything.");
      for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) {
        const eq = a[i - 1] === b[j - 1];
        if (!ed) {
          if (eq) { dp[i][j] = dp[i - 1][j - 1] + 1; vals[i][j] = dp[i][j]; push(4, `a[${i - 1}] = b[${j - 1}] = '${a[i - 1]}': extend the diagonal.`, { cur: [i, j], deps: [[i - 1, j - 1]], rec: `dp[${i}][${j}] = dp[${i - 1}][${j - 1}] + 1 = ${dp[i - 1][j - 1]} + 1 = ${dp[i][j]}` }); }
          else { dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]); vals[i][j] = dp[i][j]; push(6, `'${a[i - 1]}' ≠ '${b[j - 1]}': drop one character from either string and keep the better.`, { cur: [i, j], deps: [[i - 1, j], [i, j - 1]], rec: `dp[${i}][${j}] = max(dp[${i - 1}][${j}], dp[${i}][${j - 1}]) = max(${dp[i - 1][j]}, ${dp[i][j - 1]}) = ${dp[i][j]}` }); }
        } else if (eq) { dp[i][j] = dp[i - 1][j - 1]; vals[i][j] = dp[i][j]; push(4, `'${a[i - 1]}' matches: no edit needed, copy the diagonal.`, { cur: [i, j], deps: [[i - 1, j - 1]], rec: `dp[${i}][${j}] = dp[${i - 1}][${j - 1}] = ${dp[i][j]}` }); }
        else {
          dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]); vals[i][j] = dp[i][j];
          push(6, `'${a[i - 1]}' ≠ '${b[j - 1]}': 1 + the cheapest of delete (up), insert (left), replace (diagonal).`, { cur: [i, j], deps: [[i - 1, j], [i, j - 1], [i - 1, j - 1]], rec: `dp[${i}][${j}] = 1 + min(${dp[i - 1][j]}, ${dp[i][j - 1]}, ${dp[i - 1][j - 1]}) = ${dp[i][j]}` });
        }
      }
      const path = [];
      let i = m, j = n;
      const out = [];
      while (i > 0 || j > 0) {
        path.push([i, j]);
        if (!ed) {
          if (i === 0 || j === 0) break;
          if (a[i - 1] === b[j - 1]) { out.unshift(a[i - 1]); i--; j--; }
          else if (dp[i - 1][j] >= dp[i][j - 1]) i--; else j--;
        } else if (i > 0 && j > 0 && a[i - 1] === b[j - 1] && dp[i][j] === dp[i - 1][j - 1]) { i--; j--; }
        else if (i > 0 && j > 0 && dp[i][j] === dp[i - 1][j - 1] + 1) { out.unshift(`replace ${a[i - 1]}→${b[j - 1]}`); i--; j--; }
        else if (i > 0 && dp[i][j] === dp[i - 1][j] + 1) { out.unshift(`delete ${a[i - 1]}`); i--; }
        else { out.unshift(`insert ${b[j - 1]}`); j--; }
        push(-1, "Traceback: follow the choice that produced each value back to the start.", { path, cur: [i, j] });
      }
      path.push([i, j]);
      answer = ed ? `Edit distance = ${dp[m][n]}: ${out.join(", ") || "strings are equal"}.` : `LCS length = ${dp[m][n]}: "${out.join("")}".`;
      push(-1, answer, { path });
    } else if (problem === "knapsack") {
      const items = P.items, C = P.capacity, n = items.length;
      rowH = ["–", ...items.map(([w, v], k) => `#${k + 1} w${w} v${v}`)]; colH = range(C + 1).map(String);
      vals = grid(n + 1, C + 1);
      const dp = grid(n + 1, C + 1, 0);
      vals[0] = new Array(C + 1).fill(0);
      push(0, "Row 0: with no items, every capacity holds value 0.");
      items.forEach(([w, v], k) => {
        const i = k + 1;
        for (let c = 0; c <= C; c++) {
          dp[i][c] = dp[i - 1][c];
          if (w <= c && v + dp[i - 1][c - w] > dp[i][c]) {
            dp[i][c] = v + dp[i - 1][c - w]; vals[i][c] = dp[i][c];
            push(5, `Item ${i} (w=${w}, v=${v}) fits in capacity ${c}: taking it beats skipping.`, { cur: [i, c], deps: [[i - 1, c], [i - 1, c - w]], rec: `dp[${i}][${c}] = max(${dp[i - 1][c]}, ${v} + dp[${i - 1}][${c - w}]) = max(${dp[i - 1][c]}, ${v + dp[i - 1][c - w]}) = ${dp[i][c]}` });
          } else {
            vals[i][c] = dp[i][c];
            push(w <= c ? 5 : 3, w <= c ? `Item ${i} fits, but skipping it is at least as good.` : `Item ${i} (w=${w}) does not fit in capacity ${c}: copy from above.`, { cur: [i, c], deps: w <= c ? [[i - 1, c], [i - 1, c - w]] : [[i - 1, c]], rec: w <= c ? `dp[${i}][${c}] = max(${dp[i - 1][c]}, ${v} + ${dp[i - 1][c - w]}) = ${dp[i][c]}` : `dp[${i}][${c}] = dp[${i - 1}][${c}] = ${dp[i][c]}` });
          }
        }
      });
      const path = [];
      const chosen = [];
      let c = C;
      for (let i = n; i > 0; i--) {
        path.push([i, c]);
        if (dp[i][c] !== dp[i - 1][c]) { chosen.unshift(i); c -= items[i - 1][0]; push(-1, `dp[${i}][${c + items[i - 1][0]}] differs from the row above, so item ${i} was taken.`, { path }); }
        else push(-1, `dp[${i}][${c}] equals the row above, so item ${i} was skipped.`, { path });
      }
      path.push([0, c]);
      answer = `Best value ${dp[n][C]} using items ${chosen.length ? chosen.join(", ") : "none"} (total weight ${chosen.reduce((t, i) => t + items[i - 1][0], 0)} ≤ ${C}).`;
      push(-1, answer, { path });
    } else if (problem === "coin-change") {
      const coins = P.coins, A = P.amount;
      rowH = ["dp"]; colH = range(A + 1).map(String);
      vals = [new Array(A + 1).fill(null)];
      const dp = new Array(A + 1).fill(Infinity), choice = new Array(A + 1).fill(0);
      dp[0] = 0; vals[0][0] = 0;
      push(0, "dp[x] = fewest coins that sum to x. dp[0] = 0; everything else starts at ∞.");
      for (let x = 1; x <= A; x++) {
        const deps = coins.filter((c) => c <= x).map((c) => [0, x - c]);
        coins.forEach((c) => { if (c <= x && dp[x - c] + 1 < dp[x]) { dp[x] = dp[x - c] + 1; choice[x] = c; } });
        vals[0][x] = fmt(dp[x]);
        const parts = coins.filter((c) => c <= x).map((c) => `dp[${x - c}]+1=${fmt(dp[x - c] + 1)}`);
        push(4, dp[x] === Infinity ? `No coin combination makes ${x}.` : `Best last coin for ${x} is ${choice[x]}.`, { cur: [0, x], deps, rec: `dp[${x}] = min(${parts.join(", ") || "∞"}) = ${fmt(dp[x])}` });
      }
      const path = [];
      const used = [];
      if (dp[A] !== Infinity) {
        for (let x = A; x > 0; x -= choice[x]) { path.push([0, x]); used.push(choice[x]); push(-1, `At ${x}, the last coin was ${choice[x]}; step back to ${x - choice[x]}.`, { path }); }
        path.push([0, 0]);
        answer = `${A} = ${used.join(" + ")}: ${dp[A]} coins.`;
      } else answer = `Amount ${A} cannot be made from coins ${coins.join(", ")} (answer -1).`;
      push(5, answer, { path });
    } else if (problem === "lis") {
      const a = P.array, n = a.length;
      rowH = ["dp"]; colH = a.map(String);
      vals = [new Array(n).fill(null)];
      const dp = new Array(n).fill(1), prev = new Array(n).fill(-1);
      push(0, "dp[i] = length of the longest increasing subsequence that ends at a[i]. The column headers are the values a[i].");
      for (let i = 0; i < n; i++) {
        const deps = [];
        for (let j = 0; j < i; j++) if (a[j] < a[i]) { deps.push([0, j]); if (dp[j] + 1 > dp[i]) { dp[i] = dp[j] + 1; prev[i] = j; } }
        vals[0][i] = dp[i];
        push(4, deps.length ? `a[${i}]=${a[i]} can extend any earlier smaller value; the best is index ${prev[i]}.` : `No earlier value is smaller than ${a[i]}, so dp[${i}] = 1.`, { cur: [0, i], deps, rec: deps.length ? `dp[${i}] = 1 + max(${deps.map(([, j]) => `dp[${j}]=${dp[j]}`).join(", ")}) = ${dp[i]}` : `dp[${i}] = 1` });
      }
      let best = 0;
      dp.forEach((v, i) => { if (v > dp[best]) best = i; });
      const path = [], seq = [];
      for (let i = best; i !== -1; i = prev[i]) { path.push([0, i]); seq.unshift(a[i]); push(-1, `Traceback through prev pointers: ${a[i]} at index ${i}.`, { path }); }
      answer = `LIS length ${dp[best]}: ${seq.join(" < ")}. This is O(n²); patience sorting with bisect gives O(n log n).`;
      push(5, answer, { path });
    } else {
      const R = P.rows, C = P.cols;
      const blocked = new Set((P.blocked || []).map(([r, c]) => `${r},${c}`));
      rowH = range(R).map(String); colH = range(C).map(String);
      vals = grid(R, C);
      const dp = grid(R, C, 0);
      push(0, `Count the paths from the top-left to the bottom-right moving only right or down.${blocked.size ? " Blocked cells (✕) hold 0." : ""}`);
      for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
        if (blocked.has(`${r},${c}`)) { dp[r][c] = 0; vals[r][c] = "✕"; push(3, `(${r}, ${c}) is blocked: 0 paths go through it.`, { cur: [r, c] }); continue; }
        if (r === 0 && c === 0) { dp[0][0] = 1; vals[0][0] = 1; push(0, "There is exactly one way to stand at the start.", { cur: [0, 0] }); continue; }
        const up = r ? dp[r - 1][c] : 0, left = c ? dp[r][c - 1] : 0;
        dp[r][c] = up + left; vals[r][c] = dp[r][c];
        const deps = [];
        if (r) deps.push([r - 1, c]);
        if (c) deps.push([r, c - 1]);
        push(6, `Every path into (${r}, ${c}) arrives from above or from the left.`, { cur: [r, c], deps, rec: `dp[${r}][${c}] = up + left = ${up} + ${left} = ${dp[r][c]}` });
      }
      const path = [];
      if (dp[R - 1][C - 1] > 0) {
        let r = R - 1, c = C - 1;
        while (r > 0 || c > 0) { path.push([r, c]); if (r && dp[r - 1][c] > 0) r--; else c--; }
        path.push([0, 0]);
        push(-1, "Highlighted: one of those paths, found by stepping back to any predecessor with a non-zero count.", { path });
      }
      answer = `${dp[R - 1][C - 1]} distinct paths${blocked.size ? "" : ` = C(${R + C - 2}, ${R - 1})`}.`;
      push(-1, answer, { path });
    }
    return { frames: F, rowH, colH };
  }

  registerViz("dp-table", (el, config, a) => {
    let problem = DP[config.problem] ? config.problem : "lcs";
    const defaults = {
      a: { lcs: "ABCBDAB", "edit-distance": "kitten" }, b: { lcs: "BDCABA", "edit-distance": "sitting" },
      items: [[1, 1], [3, 4], [4, 5], [5, 7]], capacity: 7, coins: [1, 3, 4], amount: 6, array: [10, 9, 2, 5, 3, 7, 101, 18], rows: 4, cols: 6, blocked: [],
    };
    const fresh = () => ({
      a: config.a ?? defaults.a[problem] ?? "ABCBDAB", b: config.b ?? defaults.b[problem] ?? "BDCABA",
      items: Array.isArray(config.items) ? config.items : defaults.items, capacity: Number(config.capacity ?? defaults.capacity),
      coins: Array.isArray(config.coins) ? config.coins : defaults.coins, amount: Number(config.amount ?? defaults.amount),
      array: Array.isArray(config.array) ? config.array : defaults.array, rows: Number(config.rows ?? defaults.rows), cols: Number(config.cols ?? defaults.cols),
      blocked: Array.isArray(config.blocked) ? config.blocked : defaults.blocked,
    });
    const initProblem = problem;
    let P = fresh();
    const ui = a.shell(el, { title: config.title || "Dynamic programming table" });
    const { main, side } = split(ui.stage, "280px");
    const holder = h("div");
    const recEl = h("div", { style: "font:0.82rem var(--font-mono);padding:6px 8px;margin-top:6px;border-radius:6px;background:var(--bg-sunk);min-height:1.6em;color:var(--fg)" });
    main.append(holder, recEl);
    const code = codePanel(DP[problem].code);
    side.append(code.el);
    ui.setLegend([["current cell", COL.cmp], ["depends on", soft(COL.base, 45)], ["traceback", COL.path], ["empty", COL.sunk]]);
    const inputs = inputRow(ui);
    const probSel = a.select(Object.entries(DP).map(([k, v]) => [k, v.name]), problem, (v) => {
      problem = v;
      if (config.a === undefined) P.a = defaults.a[v] ?? P.a;
      if (config.b === undefined) P.b = defaults.b[v] ?? P.b;
      sync(); build();
    });
    const aIn = textInput("", "8em", { "aria-label": "String a" }), bIn = textInput("", "8em", { "aria-label": "String b" });
    const itemsIn = textInput("", "12em", { "aria-label": "Items", title: "weight:value pairs" }), capIn = numInput(0, { min: 1, max: 15, "aria-label": "Capacity" });
    const coinsIn = textInput("", "7em", { "aria-label": "Coins" }), amtIn = numInput(0, { min: 1, max: 30, "aria-label": "Amount" });
    const arrIn = textInput("", "13em", { "aria-label": "Array" });
    const rIn = numInput(0, { min: 1, max: 8, "aria-label": "Rows" }), cIn = numInput(0, { min: 1, max: 10, "aria-label": "Columns" });
    const groups = {
      ab: [a.label("a", aIn), a.label("b", bIn)], ks: [a.label("items w:v", itemsIn), a.label("capacity", capIn)],
      cc: [a.label("coins", coinsIn), a.label("amount", amtIn)], lis: [a.label("array", arrIn)], gp: [a.label("rows", rIn), a.label("cols", cIn)],
    };
    const groupOf = { lcs: "ab", "edit-distance": "ab", knapsack: "ks", "coin-change": "cc", lis: "lis", "grid-paths": "gp" };
    function sync() {
      aIn.value = P.a; bIn.value = P.b; itemsIn.value = P.items.map(([w, v]) => `${w}:${v}`).join(", "); capIn.value = P.capacity;
      coinsIn.value = P.coins.join(", "); amtIn.value = P.amount; arrIn.value = P.array.join(", "); rIn.value = P.rows; cIn.value = P.cols;
      Object.entries(groups).forEach(([k, els]) => els.forEach((x) => { x.style.display = k === groupOf[problem] ? "inline-flex" : "none"; }));
    }
    function read() {
      P.a = aIn.value.slice(0, 12) || "A"; P.b = bIn.value.slice(0, 12) || "B";
      const items = itemsIn.value.split(/[,;\s]+/).map((t) => t.split(":").map(Number)).filter((p) => p.length === 2 && p.every((x) => Number.isFinite(x) && x > 0));
      if (items.length) P.items = items.slice(0, 7).map(([w, v]) => [Math.round(w), Math.round(v)]);
      P.capacity = clamp(Math.round(Number(capIn.value)) || 1, 1, 15);
      const coins = a.parseList(coinsIn.value).map(Math.round).filter((x) => x > 0);
      if (coins.length) P.coins = [...new Set(coins)].sort((x, y) => x - y);
      P.amount = clamp(Math.round(Number(amtIn.value)) || 1, 1, 30);
      const arr = a.parseList(arrIn.value);
      if (arr.length) P.array = arr.slice(0, 14);
      P.rows = clamp(Math.round(Number(rIn.value)) || 1, 1, 8); P.cols = clamp(Math.round(Number(cIn.value)) || 1, 1, 10);
    }
    const rs = (n, al = "ABCD") => range(n).map(() => al[a.randInt(0, al.length - 1)]).join("");
    inputs.append(a.label("problem", probSel), ...Object.values(groups).flat(),
      a.button("Apply", () => { read(); sync(); build(); }),
      a.button("Random", () => {
        if (problem === "lcs") { P.a = rs(a.randInt(5, 8)); P.b = rs(a.randInt(5, 8)); }
        else if (problem === "edit-distance") { P.a = rs(a.randInt(4, 7), "abcdeh"); P.b = rs(a.randInt(4, 7), "abcdeh"); }
        else if (problem === "knapsack") { P.items = range(a.randInt(3, 5)).map(() => [a.randInt(1, 6), a.randInt(1, 10)]); P.capacity = a.randInt(5, 10); }
        else if (problem === "coin-change") { P.coins = [...new Set([1, a.randInt(2, 6), a.randInt(4, 9)])].sort((x, y) => x - y); P.amount = a.randInt(8, 16); }
        else if (problem === "lis") P.array = range(a.randInt(7, 11)).map(() => a.randInt(1, 30));
        else { P.rows = a.randInt(3, 6); P.cols = a.randInt(3, 7); P.blocked = range(a.randInt(0, 3)).map(() => [a.randInt(0, P.rows - 1), a.randInt(1, P.cols - 1)]).filter(([r, c]) => !(r === P.rows - 1 && c === P.cols - 1)); }
        sync(); build();
      }),
      a.button("Reset", () => { problem = initProblem; probSel.value = problem; P = fresh(); sync(); build(); }));
    let built = null;
    const render = (f) => {
      const { rowH, colH } = built;
      const R = f.vals.length, Cn = f.vals[0].length;
      const longRow = Math.max(...rowH.map((x) => String(x).length));
      const hw = Math.max(30, longRow * 7 + 10);
      const cs = clamp(Math.floor(560 / (Cn + 1)), 28, 40);
      const W = hw + Cn * cs + 4, H = 24 + R * cs + 4;
      const svg = svgBox(W, H, { minScale: 0.7 });
      const deps = new Set(f.deps.map(([r, c]) => `${r},${c}`));
      colH.forEach((t, c) => svg.append(txt(hw + c * cs + cs / 2, 12, t, { size: 11, weight: 700, fill: COL.muted })));
      rowH.forEach((t, r) => svg.append(txt(hw - 6, 24 + r * cs + cs / 2, t, { size: 11, weight: 700, fill: COL.muted, anchor: "end" })));
      for (let r = 0; r < R; r++) for (let c = 0; c < Cn; c++) {
        const k = `${r},${c}`, v = f.vals[r][c];
        const isCur = f.cur && f.cur[0] === r && f.cur[1] === c;
        const fill = isCur && !f.path.size ? COL.cmp : f.path.has(k) ? COL.path : deps.has(k) ? soft(COL.base, 45) : v === null ? COL.sunk : COL.node;
        svg.append(rect(hw + c * cs + 1, 24 + r * cs + 1, cs - 2, cs - 2, fill, { rx: 3, stroke: isCur ? COL.key : "var(--border)", sw: isCur ? 2.5 : 1 }));
        if (v !== null) svg.append(txt(hw + c * cs + cs / 2, 24 + r * cs + cs / 2, v, { size: 12, weight: f.path.has(k) ? 700 : 400 }));
      }
      holder.replaceChildren(svg);
      recEl.textContent = f.rec || " ";
      code.set(f.line);
      ui.setLog(esc(f.msg));
    };
    const player = a.player(ui.controls, render, { speed: 350 });
    function build() { code.setLines(DP[problem].code); built = dpFrames(problem, P); player.load(built.frames); }
    sync();
    build();
  });

  /* =====================================================================
   * n-queens
   * ===================================================================== */
  const NQ_CODE = [
    "def solve(row):",
    "    if row == n:",
    "        solutions.append(board[:]); return",
    "    for col in range(n):",
    "        if is_safe(row, col):      # no queen in same column or diagonal",
    "            board[row] = col",
    "            solve(row + 1)",
    "            board[row] = -1        # backtrack",
  ];
  function nqFrames(n, all) {
    const F = [], board = new Array(n).fill(-1), sols = [];
    let tried = 0, nodes = 0, capped = false;
    const CAP = 6000;
    const push = (line, msg, extra = {}) => { if (F.length >= CAP) { capped = true; return; } F.push({ board: [...board], line, msg, tried, nodes, sols: sols.length, ...extra }); };
    const conflict = (r, c) => { for (let q = 0; q < r; q++) { const qc = board[q]; if (qc === c || Math.abs(qc - c) === r - q) return q; } return -1; };
    push(0, `Place ${n} queens so no two share a row, column, or diagonal. One queen per row; try columns left to right.`);
    const solve = (r) => {
      if (capped) return true;
      if (r === n) { sols.push([...board]); push(2, `Solution #${sols.length}: columns ${board.join(", ")}.`, { solved: true }); return !all; }
      for (let c = 0; c < n; c++) {
        tried++;
        const q = conflict(r, c);
        if (q >= 0) { push(4, `Row ${r}, col ${c}: attacked by the queen at (${q}, ${board[q]}). Prune.`, { tryAt: [r, c], hit: q }); continue; }
        board[r] = c; nodes++;
        push(5, `Row ${r}, col ${c} is safe: place a queen and move to row ${r + 1}.`, { tryAt: [r, c] });
        if (solve(r + 1)) return true;
        board[r] = -1;
        push(7, `Backtrack: remove the queen from (${r}, ${c}) and try the next column.`, { tryAt: [r, c], back: true });
      }
      return false;
    };
    solve(0);
    F.push({ ...F[F.length - 1], line: -1, tryAt: null, hit: undefined, msg: `${capped ? `Animation capped at ${CAP} steps. ` : ""}${sols.length} solution${sols.length === 1 ? "" : "s"} found${all ? "" : " (stopping at the first)"}; ${nodes} placements and ${tried} squares tested, versus ${n ** n} boards for brute force over one-queen-per-row.`, sols: sols.length });
    return { frames: F, sols };
  }

  registerViz("n-queens", (el, config, a) => {
    let n = clamp(Number(config.n) || 6, 4, 10);
    let all = !!config.all;
    const initN = n, initAll = all;
    const ui = a.shell(el, { title: config.title || "N-Queens backtracking" });
    const { main, side } = split(ui.stage, "260px");
    const holder = h("div"), stats = statsBar();
    main.append(stats.el, holder);
    const code = codePanel(NQ_CODE);
    const solBox = h("div", { style: "margin-top:8px" });
    side.append(code.el, solBox);
    ui.setLegend([["queen", COL.base], ["square being tried", COL.cmp], ["attacking queen", COL.swap], ["attacked squares", soft(COL.swap, 22)], ["solution", COL.done]]);
    const inputs = inputRow(ui);
    const nIn = numInput(n, { min: 4, max: 10, "aria-label": "n" });
    const allBox = h("input", { type: "checkbox", "aria-label": "Find all solutions" });
    allBox.checked = all;
    allBox.addEventListener("change", () => { all = allBox.checked; build(); });
    inputs.append(a.label("n", nIn), a.label("find all", allBox),
      a.button("Apply", () => { n = clamp(Math.round(Number(nIn.value)) || 6, 4, 10); nIn.value = n; build(); }),
      a.button("Reset", () => { n = initN; all = initAll; nIn.value = n; allBox.checked = all; build(); }));
    let res = null;
    const render = (f) => {
      const cs = Math.floor(400 / n), W = cs * n;
      const svg = svgBox(W, W, { minScale: 0.6 });
      const attacked = new Set();
      f.board.forEach((c, r) => {
        if (c < 0) return;
        for (let k = 0; k < n; k++) { attacked.add(`${k},${c}`); attacked.add(`${r},${k}`); }
        for (let d = -n; d <= n; d++) { attacked.add(`${r + d},${c + d}`); attacked.add(`${r + d},${c - d}`); }
      });
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
        const t = f.tryAt && f.tryAt[0] === r && f.tryAt[1] === c;
        let fill = (r + c) % 2 ? COL.sunk : COL.node;
        if (f.board[r] !== c && attacked.has(`${r},${c}`)) fill = soft(COL.swap, 22);
        if (f.solved) fill = (r + c) % 2 ? soft(COL.done, 70) : COL.done;
        svg.append(rect(c * cs, r * cs, cs, cs, fill, { rx: 0, stroke: t ? COL.key : "var(--border)", sw: t ? 3 : 0.5 }));
        if (t && f.board[r] !== c) svg.append(rect(c * cs + 3, r * cs + 3, cs - 6, cs - 6, f.back ? "none" : soft(COL.cmp, 80), { rx: 4, stroke: COL.key, sw: 2 }));
      }
      f.board.forEach((c, r) => {
        if (c < 0) return;
        svg.append(circle(c * cs + cs / 2, r * cs + cs / 2, cs * 0.34, f.hit === r ? COL.swap : COL.base, "var(--viz-node)", 2));
        svg.append(txt(c * cs + cs / 2, r * cs + cs / 2 + 1, "♛", { size: cs * 0.42, fill: "var(--viz-node)", mono: false }));
      });
      holder.replaceChildren(svg);
      stats.set([["n", n], ["placements (nodes)", f.nodes], ["squares tested", f.tried], ["solutions", f.sols]]);
      code.set(f.line);
      ui.setLog(esc(f.msg));
      const shown = res.sols.slice(0, f.sols);
      solBox.innerHTML = sideBox(`solutions (${f.sols})`, shown.slice(0, 12).map((s2) => chip(`(${s2.join(",")})`, soft(COL.done, 60))).join("") + (shown.length > 12 ? " …" : "") || "–");
    };
    const player = a.player(ui.controls, render, { speed: 200 });
    function build() { res = nqFrames(n, all); player.load(res.frames); }
    build();
  });

  /* =====================================================================
   * bits
   * ===================================================================== */
  function parseBig(text) {
    let t = String(text).trim().toLowerCase().replace(/_/g, "");
    let neg = false;
    if (t.startsWith("-")) { neg = true; t = t.slice(1); }
    if (!/^(0x[0-9a-f]+|0b[01]+|0o[0-7]+|\d+)$/.test(t)) return null;
    const v = BigInt(t);
    return neg ? -v : v;
  }
  function pyRepr(x) {
    if (Number.isNaN(x)) return "nan";
    if (x === Infinity) return "inf";
    if (x === -Infinity) return "-inf";
    if (x === 0) return Object.is(x, -0) ? "-0.0" : "0.0";
    const [mant, e] = Math.abs(x).toExponential().split("e");
    const exp = Number(e), digits = mant.replace(".", "");
    const sign = x < 0 ? "-" : "";
    if (exp >= -5 && exp < 16) {
      let out;
      if (exp >= 0) out = digits.length > exp + 1 ? `${digits.slice(0, exp + 1)}.${digits.slice(exp + 1)}` : `${digits.padEnd(exp + 1, "0")}.0`;
      else out = `0.${"0".repeat(-exp - 1)}${digits}`;
      return sign + out;
    }
    return `${sign}${digits[0]}${digits.length > 1 ? `.${digits.slice(1)}` : ""}e${exp < 0 ? "-" : "+"}${String(Math.abs(exp)).padStart(2, "0")}`;
  }
  const f64bits = (x) => { const dv = new DataView(new ArrayBuffer(8)); dv.setFloat64(0, x); return dv.getBigUint64(0); };
  const bitsF64 = (b) => { const dv = new DataView(new ArrayBuffer(8)); dv.setBigUint64(0, b); return dv.getFloat64(0); };
  function exactDecimal(x) {
    if (!Number.isFinite(x)) return pyRepr(x);
    const b = f64bits(x);
    const sign = b >> 63n ? "-" : "";
    const e = Number((b >> 52n) & 0x7ffn), frac = b & ((1n << 52n) - 1n);
    if (e === 0 && frac === 0n) return `${sign}0`;
    const m = e === 0 ? frac : frac | (1n << 52n);
    const e2 = (e === 0 ? -1022 : e - 1023) - 52;
    if (e2 >= 0) return sign + (m << BigInt(e2)).toString();
    const digits = (m * 5n ** BigInt(-e2)).toString().padStart(-e2 + 1, "0");
    const ip = digits.slice(0, digits.length + e2), fp = digits.slice(digits.length + e2).replace(/0+$/, "");
    return `${sign}${ip || "0"}${fp ? `.${fp}` : ""}`;
  }
  function evalFloat(text) {
    const num = String.raw`\s*([-+]?(?:inf|nan|(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?))\s*`;
    const t = String(text).trim().toLowerCase();
    const one = new RegExp(`^${num}$`).exec(t);
    const conv = (s2) => (s2.replace(/^[-+]/, "") === "inf" ? (s2.startsWith("-") ? -Infinity : Infinity) : s2.replace(/^[-+]/, "") === "nan" ? NaN : Number(s2));
    if (one) return { x: conv(one[1]), expr: null };
    const two = new RegExp(`^${num}([-+*/])${num}$`).exec(t);
    if (!two) return null;
    const p = conv(two[1]), q = conv(two[3]);
    const x = two[2] === "+" ? p + q : two[2] === "-" ? p - q : two[2] === "*" ? p * q : q === 0 ? (p === 0 || Number.isNaN(p) ? NaN : p > 0 ? Infinity : -Infinity) : p / q;
    return { x, expr: [pyRepr(p), two[2], pyRepr(q)], raw: [two[1], two[2], two[3]], divZero: two[2] === "/" && q === 0 };
  }

  /** The double nearest to the exact decimal result of `p op q` (for + - * on finite decimal literals), else undefined. */
  function exactNearest(raw) {
    const dec = (s2) => {
      const m = /^([-+]?)(\d*)\.?(\d*)(?:e([-+]?\d+))?$/.exec(s2.trim());
      if (!m || !(m[2] + m[3])) return null;
      const v = BigInt(m[2] + m[3]) * (m[1] === "-" ? -1n : 1n);
      return { v, e: Number(m[4] || 0) - m[3].length };
    };
    const [ps, op, qs] = raw;
    const p = dec(ps), q = dec(qs);
    if (!p || !q || op === "/") return undefined;
    let v, e;
    if (op === "*") { v = p.v * q.v; e = p.e + q.e; }
    else {
      e = Math.min(p.e, q.e);
      const pv = p.v * 10n ** BigInt(p.e - e), qv = q.v * 10n ** BigInt(q.e - e);
      v = op === "+" ? pv + qv : pv - qv;
    }
    return Number(`${v}e${e}`);
  }

  registerViz("bits", (el, config, a) => {
    let mode = config.mode === "float" ? "float" : "int";
    let width = [8, 16, 32].includes(Number(config.width)) ? Number(config.width) : 8;
    const initVal = config.value ?? (mode === "float" ? "0.1 + 0.2" : 42);
    let A = 0n, B = 5n, op = config.op || "&";
    let ftext = mode === "float" ? String(initVal) : "0.1 + 0.2";
    const mask = () => (1n << BigInt(width)) - 1n;
    const setA = (v) => { A = BigInt.asUintN(width, v); };
    setA(mode === "int" ? parseBig(String(initVal)) ?? 42n : 42n);
    const ui = a.shell(el, { title: config.title || "Bits and bytes" });
    const holder = h("div"), info = h("div", { style: "font:0.8rem/1.6 var(--font-mono);padding:6px 4px;color:var(--fg)" });
    ui.stage.append(holder, info);
    const inputs = inputRow(ui);
    const modeSel = a.select([["int", "integer"], ["float", "float64 (IEEE-754)"]], mode, (v) => { mode = v; sync(); build(); });
    const widthSel = a.select([["8", "8-bit"], ["16", "16-bit"], ["32", "32-bit"]], String(width), (v) => { const sa = signed(A); width = Number(v); setA(sa); B = BigInt.asUintN(width, B); sync(); build(); });
    const aIn = textInput("", "7em", { "aria-label": "Value a" }), bIn = textInput("", "5em", { "aria-label": "Value b" });
    const opSel = a.select([["&", "a & b"], ["|", "a | b"], ["^", "a ^ b"], ["<<", "a << b"], [">>", "a >> b"], ["~", "~a"]], op, (v) => { op = v; build(); });
    const fIn = textInput(ftext, "11em", { "aria-label": "Float expression" });
    const presets = h("span", { style: "display:inline-flex;gap:4px;flex-wrap:wrap" }, ["0.1", "0.1 + 0.2", "0.3", "1 / 3", "-2.5", "1e308 * 10", "5e-324", "0 / 0"].map((p) => a.button(p, () => { ftext = p; fIn.value = p; build(); })));
    const intEls = [a.label("width", widthSel), a.label("a", aIn), a.label("op", opSel), a.label("b", bIn)];
    const floatEls = [a.label("value or a op b", fIn), presets];
    function signed(v) { return BigInt.asIntN(width, v); }
    function sync() {
      aIn.value = String(signed(A)); bIn.value = String(signed(B)); fIn.value = ftext;
      intEls.forEach((x) => { x.style.display = mode === "int" ? "inline-flex" : "none"; });
      floatEls.forEach((x) => { x.style.display = mode === "float" ? "inline-flex" : "none"; });
    }
    inputs.append(a.label("mode", modeSel), ...intEls, ...floatEls,
      a.button("Apply", () => {
        if (mode === "int") { const va = parseBig(aIn.value), vb = parseBig(bIn.value); if (va === null || vb === null) { ui.setLog("Enter integers like 42, -7, 0x2A or 0b101010."); return; } setA(va); B = BigInt.asUintN(width, vb); }
        else ftext = fIn.value;
        sync(); build();
      }),
      a.button("Random", () => { if (mode === "int") { setA(BigInt(a.randInt(0, 2 ** Math.min(width, 30) - 1))); B = BigInt(op === "<<" || op === ">>" ? a.randInt(1, 3) : a.randInt(0, 2 ** Math.min(width, 30) - 1)); } else ftext = String(Math.round(Math.random() * 1e4) / 100); sync(); build(); }),
      a.button("Reset", () => { mode = config.mode === "float" ? "float" : "int"; width = [8, 16, 32].includes(Number(config.width)) ? Number(config.width) : 8; widthSel.value = String(width); modeSel.value = mode; op = config.op || "&"; opSel.value = op; setA(mode === "int" ? parseBig(String(initVal)) ?? 42n : 42n); B = 5n; ftext = mode === "float" ? String(initVal) : "0.1 + 0.2"; sync(); build(); }));

    const bitOf = (v, k) => Number((v >> BigInt(k)) & 1n);
    function bitRow(svg, y, label, v, nbits, { onToggle, colorAt, reveal = null, hlCol = -1, x0 = 70, cw = 18, diff = null, lo = 0 } = {}) {
      svg.append(txt(x0 - 10, y + 12, label, { anchor: "end", size: 12, weight: 700, fill: COL.muted }));
      for (let k = nbits - 1; k >= lo; k--) {
        const col = nbits - 1 - k;
        const x = x0 + col * cw + Math.floor(col / 4) * 4;
        const hidden = reveal !== null && k > reveal;
        const bit = bitOf(v, k);
        const fill = hidden ? COL.sunk : k === hlCol ? COL.cmp : colorAt ? colorAt(k, bit) : bit ? soft(COL.base, 70) : COL.node;
        const r = rect(x, y, cw - 2, 24, fill, { rx: 3, stroke: diff && diff.has(k) ? COL.swap : COL.border, sw: diff && diff.has(k) ? 2.5 : 1 });
        if (onToggle) { r.style.cursor = "pointer"; r.addEventListener("click", () => onToggle(k)); }
        svg.append(r);
        if (!hidden) svg.append(txt(x + (cw - 2) / 2, y + 12, bit, { size: 12, weight: bit ? 700 : 400 }));
      }
    }
    let frames = [];
    const renderInt = (f) => {
      const cw = width === 32 ? 17 : 22, W = 70 + width * cw + (width / 4) * 4 + 150;
      const unary = op === "~", shift = op === "<<" || op === ">>";
      const rows = unary || shift ? 2 : 3;
      const svg = svgBox(W, 40 + rows * 46, { minScale: 0.7 });
      for (let k = width - 1; k >= 0; k--) {
        const col = width - 1 - k;
        if (width <= 16 || k % 4 === 3 || k === 0) svg.append(txt(70 + col * cw + Math.floor(col / 4) * 4 + (cw - 2) / 2, 10, k, { size: 9, fill: COL.faint }));
      }
      const xr = 70 + width * cw + (width / 4) * 4 + 8;
      const desc = (v) => `= ${v} (signed ${signed(v)}, 0x${v.toString(16).toUpperCase().padStart(width / 4, "0")})`;
      bitRow(svg, 22, "a", A, width, { cw, hlCol: f.col, onToggle: (k) => { A ^= 1n << BigInt(k); sync(); build(true); } });
      svg.append(txt(xr, 34, desc(A).split(" (")[0], { anchor: "start", size: 11, fill: COL.muted }));
      let y = 68;
      if (!unary && !shift) {
        bitRow(svg, y, "b", B, width, { cw, hlCol: f.col, onToggle: (k) => { B ^= 1n << BigInt(k); sync(); build(true); } });
        svg.append(txt(xr, y + 12, `= ${B}`, { anchor: "start", size: 11, fill: COL.muted }));
        y += 46;
      }
      bitRow(svg, y, unary ? "~a" : `a${op}b`, f.v, width, { cw, reveal: f.reveal, hlCol: f.col, colorAt: (k, bit) => (bit ? soft(COL.path, 65) : COL.node) });
      svg.append(txt(xr, y + 12, f.reveal === null || f.reveal >= width - 1 ? `= ${f.v}` : "…", { anchor: "start", size: 11, fill: COL.muted }));
      holder.replaceChildren(svg);
      const sa = signed(A), sb = signed(B), r = f.final;
      let note = "";
      if (op === "~") note = `~a flips every bit. Python ints act like infinitely sign-extended two's complement, so ~a == -a - 1: ~${sa} == ${-sa - 1n}. Masked to ${width} bits the pattern reads ${r} unsigned.`;
      else if (op === "<<") note = `a << ${B} multiplies by 2**${B}. Python ints never overflow (${sa} << ${B} == ${sa << B}); a ${width}-bit register keeps only the low ${width} bits, ${signed(r)} signed.`;
      else if (op === ">>") note = `a >> ${B} is an arithmetic shift in Python: it floor-divides by 2**${B} and copies the sign bit in from the left, so ${sa} >> ${B} == ${sa >> B}.`;
      else note = `${op === "&" ? "AND keeps a bit only where both are 1 (masking)" : op === "|" ? "OR sets a bit where either is 1 (setting flags)" : "XOR sets a bit where they differ (toggling; x ^ x == 0)"}. In Python: ${sa} ${op} ${sb} == ${op === "&" ? sa & sb : op === "|" ? sa | sb : sa ^ sb}.`;
      info.innerHTML = `a ${esc(desc(A))}<br>${unary ? "" : `b = ${esc(String(sb))}<br>`}result ${esc(desc(r))}<br><span style="color:var(--fg-muted)">${esc(note)}</span><br><span style="color:var(--fg-muted)">Two's complement: the top bit is worth -2**${width - 1}, so ${width}-bit signed values run from ${-(2n ** BigInt(width - 1))} to ${2n ** BigInt(width - 1) - 1n}. Click any bit of a or b to toggle it.</span>`;
      ui.setLog(esc(f.msg));
    };
    const renderFloat = (f) => {
      const cw = 18, x0 = 64, W = x0 + 32 * cw + 8 * 4 + 8;
      const rowsN = f.near !== undefined ? 2 : 1;
      const svg = svgBox(W, 24 + rowsN * 76, { minScale: 0.75 });
      const colorAt = (k, bit) => {
        const part = k === 63 ? "s" : k >= 52 ? "e" : "m";
        const on = f.stage === "all" || f.stage === part;
        const base = part === "s" ? COL.swap : part === "e" ? COL.key : COL.base;
        return soft(base, on ? (bit ? 75 : 30) : bit ? 30 : 10);
      };
      const bits = f64bits(f.x);
      const toggle = (k) => { const nb = bits ^ (1n << BigInt(k)); ftext = pyRepr(bitsF64(nb)); sync(); build(true); };
      const diff = f.near !== undefined ? new Set(range(64).filter((k) => bitOf(bits, k) !== bitOf(f64bits(f.near), k))) : null;
      svg.append(txt(x0, 10, "sign", { size: 10, fill: COL.swap, anchor: "start", weight: 700 }));
      svg.append(txt(x0 + 2 * cw + 4, 10, "exponent (11 bits)", { size: 10, fill: COL.key, anchor: "start", weight: 700 }));
      svg.append(txt(x0 + 12 * cw + 12, 10, "fraction (52 bits, continues below)", { size: 10, fill: COL.base, anchor: "start", weight: 700 }));
      const twoRows = (y, label, v, opts) => {
        bitRow(svg, y, label, v, 64, { cw, x0, colorAt, diff, lo: 32, ...opts });
        bitRow(svg, y + 30, "", v, 32, { cw, x0, colorAt: (k, bit) => colorAt(k, bit), diff: diff && new Set([...diff].filter((k) => k < 32)), ...opts });
      };
      twoRows(22, "x", bits, { onToggle: toggle });
      if (f.near !== undefined) twoRows(98, pyRepr(f.near).slice(0, 6), f64bits(f.near), {});
      holder.replaceChildren(svg);
      const e = Number((bits >> 52n) & 0x7ffn), frac = bits & ((1n << 52n) - 1n), sgn = Number(bits >> 63n);
      const kind = e === 2047 ? (frac ? "NaN (exponent all 1s, fraction ≠ 0)" : "infinity (exponent all 1s, fraction 0)") : e === 0 ? (frac ? "subnormal: 0.fraction × 2**-1022" : "zero") : "normal: 1.fraction × 2**(exponent - 1023)";
      const m = e === 0 ? Number(frac) / 2 ** 52 : 1 + Number(frac) / 2 ** 52;
      const lines = [
        `sign     = ${sgn} → ${sgn ? "negative" : "positive"}`,
        `exponent = ${e.toString(2).padStart(11, "0")}₂ = ${e}${e && e !== 2047 ? ` → 2**(${e} - 1023) = 2**${e - 1023}` : ""}`,
        `fraction = 0x${frac.toString(16).padStart(13, "0")} → mantissa ${e === 2047 ? "–" : m.toPrecision(17)}`,
        `kind     = ${kind}`,
        `repr(x)  = ${pyRepr(f.x)}`,
        `exact    = ${exactDecimal(f.x)}`,
      ];
      if (f.near !== undefined) lines.push(`${pyRepr(f.near)} is exactly ${exactDecimal(f.near)}`);
      info.innerHTML = lines.map((l, i) => `<div style="${(f.stage === "s" && i === 0) || (f.stage === "e" && i === 1) || (f.stage === "m" && i === 2) || (f.stage === "v" && i >= 4) ? "background:color-mix(in srgb, var(--viz-active) 35%, transparent)" : ""}">${esc(l)}</div>`).join("") +
        `<div style="color:var(--fg-muted);margin-top:4px">Click a bit to flip it. Python's float is this same 64-bit format.</div>`;
      ui.setLog(esc(f.msg));
    };
    const render = (f) => (mode === "int" ? renderInt(f) : renderFloat(f));
    const player = a.player(ui.controls, render);
    function build(toEnd = false) {
      frames = [];
      if (mode === "int") {
        const sa = signed(A);
        let r;
        if (op === "&") r = A & B; else if (op === "|") r = A | B; else if (op === "^") r = A ^ B;
        else if (op === "~") r = ~A & mask();
        else if (op === "<<") r = (A << (B & 63n)) & mask();
        else r = BigInt.asUintN(width, sa >> (B & 63n));
        if (op === "<<" || op === ">>") {
          const n = Number(B & 63n);
          frames.push({ v: A, reveal: null, col: -1, final: r, msg: `Start with a = ${sa}. Shift ${op === "<<" ? "left" : "right"} by ${n}, one position at a time.` });
          for (let t = 1; t <= Math.min(n, width); t++) {
            const v = op === "<<" ? (A << BigInt(t)) & mask() : BigInt.asUintN(width, sa >> BigInt(t));
            frames.push({ v, reveal: null, col: -1, final: r, msg: op === "<<" ? `After ${t} shift${t > 1 ? "s" : ""}: bits move left, a 0 enters on the right${t <= width && bitOf(A, width - t) ? ", and a 1 falls off the left end" : ""}.` : `After ${t} shift${t > 1 ? "s" : ""}: bits move right; the sign bit (${bitOf(A, width - 1)}) is copied in on the left.` });
          }
          if (n > width) frames.push({ v: r, reveal: null, col: -1, final: r, msg: `Shifting by ${n} ≥ ${width} pushes every original bit out.` });
        } else {
          frames.push({ v: r, reveal: -1, col: -1, final: r, msg: `Compute ${op === "~" ? "~a" : `a ${op} b`} one bit column at a time, from bit 0 (rightmost).` });
          for (let k = 0; k < width; k++) {
            const x = bitOf(A, k), y = bitOf(B, k), z = bitOf(r, k);
            frames.push({ v: r, reveal: k, col: k, final: r, msg: op === "~" ? `bit ${k}: ~${x} = ${z}` : `bit ${k}: ${x} ${op} ${y} = ${z}` });
          }
        }
        frames.push({ v: r, reveal: null, col: -1, final: r, msg: `Result: ${r} unsigned, ${signed(r)} as ${width}-bit signed.` });
      } else {
        const ev = evalFloat(ftext);
        if (!ev) { ui.setLog("Enter a number (0.1, -2.5e3, inf, nan) or a simple expression like 0.1 + 0.2."); return; }
        const x = ev.x;
        const near = ev.raw && Number.isFinite(x) ? exactNearest(ev.raw) : undefined;
        const nearDiff = near !== undefined && near !== x ? near : undefined;
        frames.push({ x, stage: "all", msg: `${ev.expr ? `${ev.expr.join(" ")} = ${pyRepr(x)}` : `x = ${pyRepr(x)}`}. A float64 has 1 sign bit, 11 exponent bits and 52 fraction bits.${ev.divZero ? " (Python raises ZeroDivisionError here; IEEE-754 itself gives inf or nan.)" : ""}` });
        frames.push({ x, stage: "s", msg: "Sign bit: 0 means positive, 1 negative. -0.0 exists and compares equal to 0.0." });
        frames.push({ x, stage: "e", msg: "Exponent: stored with a bias of 1023, so the scale is 2**(e - 1023). All 0s means zero/subnormal; all 1s means inf or nan." });
        frames.push({ x, stage: "m", msg: "Fraction: the bits after an implicit leading 1, so normal values are 1.fraction × 2**exponent. 52 bits ≈ 15–17 significant decimal digits." });
        frames.push({ x, stage: "v", msg: `The stored value is a binary fraction. Decimal ${pyRepr(x)} is only the shortest string that round-trips to these bits; the exact value is shown below.` });
        if (nearDiff !== undefined) {
          const ulps = Number(f64bits(x) - f64bits(nearDiff));
          frames.push({ x, near: nearDiff, stage: "all", msg: `${ev.expr.join(" ")} == ${pyRepr(nearDiff)} is False: each operand was already rounded to binary, and the result lands ${Math.abs(ulps)} ulp${Math.abs(ulps) === 1 ? "" : "s"} away from the double nearest ${pyRepr(nearDiff)} (differing bits outlined). Compare with math.isclose().` });
        }
      }
      player.load(frames, toEnd ? frames.length - 1 : 0);
    }
    sync();
    build();
  });

  /* =====================================================================
   * kmp
   * ===================================================================== */
  const KMP_CODE = [
    "# 1) fail[i] = length of the longest proper prefix",
    "#    of p[:i+1] that is also its suffix",
    "fail, k = [0] * m, 0",
    "for i in range(1, m):",
    "    while k > 0 and p[i] != p[k]: k = fail[k - 1]",
    "    if p[i] == p[k]: k += 1",
    "    fail[i] = k",
    "# 2) matching",
    "j = 0",
    "for i, ch in enumerate(text):",
    "    while j > 0 and ch != p[j]: j = fail[j - 1]   # shift pattern",
    "    if ch == p[j]: j += 1",
    "    if j == m: found(i - m + 1); j = fail[j - 1]",
  ];
  function kmpFrames(text, p) {
    const m = p.length, F = [], fail = new Array(m).fill(null);
    fail[0] = 0;
    let cmp = 0;
    const found = [];
    F.push({ phase: 1, fail: [...fail], line: 2, i: 0, k: 0, cmp, found: [], msg: "fail[0] = 0: a single character has no proper prefix that is also a suffix." });
    let k = 0;
    for (let i = 1; i < m; i++) {
      for (;;) {
        cmp++;
        const eq = p[i] === p[k];
        if (!eq && k > 0) { F.push({ phase: 1, fail: [...fail], line: 4, i, k, cmp, cmpPair: [i, k], eq, found: [], msg: `p[${i}]='${p[i]}' ≠ p[${k}]='${p[k]}': fall back k = fail[${k - 1}] = ${fail[k - 1]}.` }); k = fail[k - 1]; continue; }
        if (eq) { F.push({ phase: 1, fail: [...fail], line: 5, i, k, cmp, cmpPair: [i, k], eq, found: [], msg: `p[${i}]='${p[i]}' = p[${k}]: the border grows to ${k + 1}.` }); k++; }
        else F.push({ phase: 1, fail: [...fail], line: 5, i, k, cmp, cmpPair: [i, k], eq, found: [], msg: `p[${i}]='${p[i]}' ≠ p[0]: no border.` });
        break;
      }
      fail[i] = k;
      F.push({ phase: 1, fail: [...fail], line: 6, i, k, cmp, found: [], msg: `fail[${i}] = ${k}${k ? `: "${p.slice(0, k)}" is both a prefix and a suffix of "${p.slice(0, i + 1)}"` : ""}.` });
    }
    const buildCmp = cmp;
    let j = 0;
    F.push({ phase: 2, fail: [...fail], line: 8, i: 0, j: 0, cmp, found: [], msg: `Failure table ready (${buildCmp} comparisons). Now scan the text once; i never moves backwards.` });
    for (let i = 0; i < text.length; i++) {
      for (;;) {
        cmp++;
        const eq = text[i] === p[j];
        if (!eq && j > 0) {
          F.push({ phase: 2, fail: [...fail], line: 10, i, j, cmp, eq, found: [...found], msg: `text[${i}]='${text[i]}' ≠ p[${j}]='${p[j]}'. Keep the ${fail[j - 1]} characters we know still match: j = fail[${j - 1}] = ${fail[j - 1]} (pattern shifts by ${j - fail[j - 1]}).` });
          j = fail[j - 1];
          continue;
        }
        F.push({ phase: 2, fail: [...fail], line: 11, i, j, cmp, eq, found: [...found], msg: eq ? `text[${i}]='${text[i]}' = p[${j}]: advance j to ${j + 1}.` : `text[${i}]='${text[i]}' ≠ p[0]: move on to the next text character.` });
        if (eq) j++;
        break;
      }
      if (j === m) {
        found.push(i - m + 1);
        F.push({ phase: 2, fail: [...fail], line: 12, i, j: m, cmp, found: [...found], match: i - m + 1, msg: `Match at index ${i - m + 1}! Continue with j = fail[${m - 1}] = ${fail[m - 1]} to catch overlapping matches.` });
        j = fail[m - 1];
      }
    }
    let naive = 0;
    for (let s0 = 0; s0 + m <= text.length; s0++) for (let t = 0; t < m; t++) { naive++; if (text[s0 + t] !== p[t]) break; }
    F.push({ ...F[F.length - 1], line: -1, msg: `Done: ${found.length} match${found.length === 1 ? "" : "es"} at [${found.join(", ")}]. KMP used ${cmp} comparisons (${buildCmp} for the table); the naive scan needs ${naive}. KMP is O(n + m).`, end: true });
    return F;
  }

  registerViz("kmp", (el, config, a) => {
    const init = { text: String(config.text ?? "ABABDABACDABABCABABABC"), pattern: String(config.pattern ?? "ABABCABAB") };
    let text = init.text.slice(0, 48), pat = init.pattern.slice(0, 16) || "A";
    const ui = a.shell(el, { title: config.title || "Knuth–Morris–Pratt string matching" });
    const { main, side } = split(ui.stage, "300px");
    const holder = h("div"), stats = statsBar();
    main.append(stats.el, holder);
    const code = codePanel(KMP_CODE);
    side.append(code.el);
    ui.setLegend([["match", COL.done], ["mismatch", soft(COL.swap, 60)], ["comparing", COL.cmp], ["found occurrence", soft(COL.path, 45)]]);
    const inputs = inputRow(ui);
    const tIn = textInput(text, "16em", { "aria-label": "Text" }), pIn = textInput(pat, "8em", { "aria-label": "Pattern" });
    inputs.append(a.label("text", tIn), a.label("pattern", pIn),
      a.button("Apply", () => { text = tIn.value.slice(0, 48); pat = pIn.value.slice(0, 16) || "A"; build(); }),
      a.button("Random", () => { const al = "AB"; pat = range(a.randInt(3, 5)).map(() => al[a.randInt(0, 1)]).join(""); text = range(30).map(() => al[a.randInt(0, 1)]).join(""); build(); }),
      a.button("Reset", () => { text = init.text; pat = init.pattern; build(); }));
    const render = (f) => {
      const n = text.length, m = pat.length;
      const x0 = 60, cw = f.phase === 1 ? Math.min(34, 560 / Math.max(m, 1)) : Math.min(30, 600 / Math.max(n, m, 1));
      const W = f.phase === 1 ? x0 + m * cw + 20 : Math.max(400, x0 + (n + m) * cw + 10);
      const svg = svgBox(W, f.phase === 1 ? 120 : 170, { minScale: f.phase === 1 ? 0.4 : 0.7 });
      const lab = (y, t2) => svg.append(txt(x0 - 8, y + 13, t2, { anchor: "end", size: 11, weight: 700, fill: COL.muted }));
      if (f.phase === 1) {
        lab(22, "p"); lab(70, "fail");
        cellRow(svg, x0, 22, [...pat].map((c, i) => ({ v: c, fill: f.cmpPair && i === f.cmpPair[0] ? (f.eq ? COL.done : soft(COL.swap, 60)) : f.cmpPair && i === f.cmpPair[1] ? COL.cmp : i < f.i - f.k + 0 || i > f.i ? COL.node : COL.node, bottom: i === f.i ? "i" : i === f.k && f.cmpPair ? "k" : "" })), cw, 26);
        cellRow(svg, x0, 78, f.fail.map((v, i) => ({ v: v ?? "", fill: v === null ? COL.sunk : i === f.i && f.line === 6 ? COL.cmp : COL.node })), cw, 26, { idx: false });
        if (f.k > 0 && f.line === 6) svg.append(rect(x0 + 1, 18, f.k * cw - 2, 4, COL.key, { stroke: "none", rx: 2 }));
      } else {
        lab(22, "text"); lab(84, "p"); lab(124, "fail");
        const shift = f.line === 12 ? f.match : f.i - f.j;
        const inFound = (i) => f.found.some((st) => i >= st && i < st + m);
        cellRow(svg, x0, 22, [...text].map((c, i) => ({ v: c, fill: i === f.i && f.line !== 12 ? (f.eq ? COL.done : soft(COL.swap, 60)) : f.match !== undefined && i >= f.match && i <= f.i ? COL.done : inFound(i) ? soft(COL.path, 45) : i < f.i ? COL.sunk : COL.node, bottom: i === f.i ? "i" : "" })), cw, 26);
        const px = x0 + Math.max(0, shift) * cw;
        cellRow(svg, px, 84, [...pat].map((c, k) => ({ v: c, fill: k === f.j && f.line !== 12 ? COL.cmp : k < f.j ? soft(COL.done, 60) : COL.node, bottom: k === f.j && f.line !== 12 ? "j" : "" })), cw, 26, { idx: false });
        cellRow(svg, px, 128, f.fail.map((v) => ({ v })), cw, 22, { idx: false, size: 10 });
      }
      holder.replaceChildren(svg);
      stats.set([["phase", f.phase === 1 ? "build failure table" : "match"], ["comparisons", f.cmp], ["matches", f.found.length]]);
      code.set(f.line);
      ui.setLog(esc(f.msg));
    };
    const player = a.player(ui.controls, render, { speed: 400 });
    function build() { tIn.value = text; pIn.value = pat; player.load(kmpFrames(text, pat)); }
    build();
  });

  /* =====================================================================
   * huffman
   * ===================================================================== */
  const HUFF_CODE = [
    "freq = Counter(text)",
    "heap = [(f, i, Leaf(ch)) for i, (ch, f) in enumerate(freq.items())]",
    "heapify(heap)",
    "while len(heap) > 1:",
    "    f1, _, a = heappop(heap)       # two smallest",
    "    f2, _, b = heappop(heap)",
    "    heappush(heap, (f1 + f2, next(ids), Node(a, b)))",
    "codes = assign(heap[0], '')       # left edge 0, right edge 1",
  ];
  const showCh = (c) => (c === " " ? "␣" : c === "\n" ? "⏎" : c);
  function huffFrames(text) {
    const F = [];
    const freq = new Map();
    for (const ch of text) freq.set(ch, (freq.get(ch) || 0) + 1);
    const table = (hl) => sideBox("frequencies", miniTable(["char", "count"], [...freq.entries()].map(([c, f]) => ({ cells: [showCh(c), f], hl: c === hl }))));
    F.push({ forest: [], line: 0, side: table(), msg: `Count each character of the ${[...text].length}-character text.` });
    let seq = 0;
    let heap = [...freq.entries()].map(([ch, f]) => ({ f, id: seq++, ch, children: [] }));
    const sortH = () => heap.sort((x, y) => x.f - y.f || x.id - y.id);
    sortH();
    const pq = (hl = []) => sideBox("priority queue (freq, id)", heap.map((n) => chip(`${n.f}${n.ch !== undefined ? `:${showCh(n.ch)}` : ""}`, hl.includes(n) ? COL.cmp : COL.node)).join("")) + table();
    F.push({ forest: [...heap], line: 2, side: pq(), msg: `Make a leaf per character and heapify by frequency (ties broken by insertion id). ${heap.length} trees.` });
    while (heap.length > 1) {
      const x = heap[0], y = heap[1];
      F.push({ forest: [...heap], hl: [x, y], line: 4, side: pq([x, y]), msg: `Pop the two lightest trees: ${x.f} and ${y.f}.` });
      heap = heap.slice(2);
      const node = { f: x.f + y.f, id: seq++, children: [x, y] };
      heap.push(node);
      sortH();
      F.push({ forest: [...heap], hl: [node], line: 6, side: pq([node]), msg: `Merge them under a new node of weight ${node.f} and push it back. ${heap.length} tree${heap.length === 1 ? "" : "s"} left.` });
    }
    const root = heap[0];
    const codes = new Map();
    const walk = (n, c) => { if (!n.children.length) { codes.set(n.ch, c || "0"); return; } walk(n.children[0], `${c}0`); walk(n.children[1], `${c}1`); };
    if (root) walk(root, "");
    const N = [...text].length;
    const bits = [...freq.entries()].reduce((t, [c, f]) => t + f * codes.get(c).length, 0);
    const codeTable = sideBox("codes", miniTable(["char", "freq", "code", "bits"], [...freq.entries()].sort((p, q) => q[1] - p[1]).map(([c, f]) => ({ cells: [showCh(c), f, codes.get(c), f * codes.get(c).length] }))));
    F.push({ forest: root ? [root] : [], codes: true, line: 7, side: codeTable, msg: "Read each code from the root: left edge = 0, right edge = 1. Frequent characters sit near the root and get short codes. No code is a prefix of another." });
    const encoded = [...text].map((c) => codes.get(c)).join("");
    F.push({ forest: root ? [root] : [], codes: true, line: -1, side: codeTable + sideBox("encoded bits", esc(encoded.length > 160 ? `${encoded.slice(0, 160)}…` : encoded)), msg: `Encoded length ${bits} bits vs ${N * 8} bits as 8-bit ASCII: ${N ? Math.round((100 * bits) / (N * 8)) : 0}% of the size (${N ? (bits / N).toFixed(2) : 0} bits per character).` });
    return F;
  }

  registerViz("huffman", (el, config, a) => {
    const initText = String(config.text ?? "abracadabra alakazam");
    let text = initText.slice(0, 80) || "a";
    const ui = a.shell(el, { title: config.title || "Huffman coding" });
    const { main, side } = split(ui.stage, "240px");
    const holder = h("div");
    main.append(holder);
    const code = codePanel(HUFF_CODE);
    const sideInfo = h("div", { style: "margin-top:8px" });
    side.append(code.el, sideInfo);
    ui.setLegend([["just popped / merged", COL.cmp], ["leaf (character)", soft(COL.key, 50)], ["internal node", COL.node]]);
    const inputs = inputRow(ui);
    const tIn = textInput(text, "18em", { "aria-label": "Text" });
    const samples = ["abracadabra alakazam", "mississippi river", "aaaaaaaabbbbccd", "the quick brown fox jumps over the lazy dog"];
    inputs.append(a.label("text", tIn),
      a.button("Apply", () => { text = tIn.value.slice(0, 80) || "a"; build(); }),
      a.button("Random", () => { text = samples[a.randInt(0, samples.length - 1)]; build(); }),
      a.button("Reset", () => { text = initText; build(); }));
    const render = (f) => {
      const trees = f.forest.map((t) => ({ t, L: api.layoutTree(t, (n) => n.children) }));
      const cell = 38, levelH = 52;
      const totalLeaves = trees.reduce((s2, x) => s2 + x.L.width, 0) || 1;
      const depth = Math.max(1, ...trees.map((x) => x.L.depth));
      const W = Math.max(totalLeaves * cell + (trees.length - 1) * 14, 200), H = depth * levelH + 30;
      const svg = svgBox(W, H, { minScale: W > 900 ? 0.9 : 0.6 });
      const hl = new Set(f.hl || []);
      let off = 0;
      trees.forEach(({ t, L }) => {
        const P = (n) => ({ x: off + L.pos.get(n).x * cell + cell / 2, y: L.pos.get(n).y * levelH + 22 });
        const edges = (n) => n.children.forEach((c, k) => {
          const p = P(n), q = P(c);
          svg.append(line(p.x, p.y, q.x, q.y, COL.edge, 1.5));
          if (f.codes) svg.append(txt((p.x + q.x) / 2 + (k ? 7 : -7), (p.y + q.y) / 2 - 2, k, { size: 11, weight: 700, fill: COL.pivot }));
          edges(c);
        });
        edges(t);
        const nodes = (n) => {
          const { x, y } = P(n);
          const leaf = !n.children.length;
          svg.append(circle(x, y, 14, hl.has(n) ? COL.cmp : leaf ? soft(COL.key, 50) : COL.node));
          svg.append(txt(x, y, n.f, { size: 11, weight: 700 }));
          if (leaf) svg.append(txt(x, y + 24, `'${showCh(n.ch)}'`, { size: 11, fill: COL.muted }));
          n.children.forEach(nodes);
        };
        nodes(t);
        off += L.width * cell + 14;
      });
      holder.replaceChildren(svg);
      sideInfo.innerHTML = f.side;
      code.set(f.line);
      ui.setLog(esc(f.msg));
    };
    const player = a.player(ui.controls, render, { speed: 700 });
    function build() { tIn.value = text; player.load(huffFrames(text)); }
    build();
  });
})();
