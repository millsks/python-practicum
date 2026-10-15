/* Data-structure visualizers: references, bigo, dynamic-array, linked-list, stack-queue, hash-table, bst, heap,
   trie, union-find, lru-cache, bloom-filter, matrix. Registered with the core in viz.js. */
(() => {
  "use strict";
  if (!window.PPViz) return;
  const { registerViz, api } = window.PPViz;
  const { h, s, esc, button, select, input, label, player, shell, parseList, shuffle, randInt, layoutBinaryTree, layoutTree } = api;

  /* ---------- shared helpers ---------- */
  let uid = 0;
  const V = (n) => `var(--${n})`;
  const PALETTE = [1, 2, 3, 4, 5, 6].map((i) => V(`viz-${i}`));
  const MONO = "var(--font-mono)";
  const ACT = V("viz-active");
  const DONE = V("viz-done");
  const NEW = "color-mix(in srgb, var(--viz-3) 35%, var(--viz-node))";
  const DEL = "color-mix(in srgb, var(--viz-4) 35%, var(--viz-node))";
  const SOFT = (n) => `color-mix(in srgb, var(--viz-${n}) 25%, var(--viz-node))`;
  const deep = (o) => structuredClone(o);
  const fmtNum = (v) => (Number.isInteger(v) ? String(v) : String(Math.round(v * 100) / 100));

  function svgBox(w, hh) {
    return s("svg", { viewBox: `0 0 ${w} ${hh}`, width: "100%", style: `max-width:${w}px;height:auto;font-family:${MONO}`, role: "img" });
  }
  function R(x, y, w, hh, fill = V("viz-node"), stroke = V("border-strong"), o = {}) {
    let st = `fill:${fill};stroke:${stroke};stroke-width:${o.sw ?? 1.3}`;
    if (o.dash) st += `;stroke-dasharray:${o.dash}`;
    if (o.op != null) st += `;opacity:${o.op}`;
    return s("rect", { x, y, width: w, height: hh, rx: o.rx ?? 5, style: st });
  }
  function T(x, y, t, o = {}) {
    let st = `fill:${o.fill || V("fg")};font-size:${o.size || 13}px;font-weight:${o.weight || 500};font-family:${o.font || MONO}`;
    if (o.op != null) st += `;opacity:${o.op}`;
    return s("text", { x, y, "text-anchor": o.anchor || "middle", "dominant-baseline": "central", style: st, text: String(t) });
  }
  function L(x1, y1, x2, y2, stroke = V("viz-edge"), sw = 1.5, dash) {
    return s("line", { x1, y1, x2, y2, style: `stroke:${stroke};stroke-width:${sw}${dash ? `;stroke-dasharray:${dash}` : ""}` });
  }
  function Ci(cx, cy, r, fill = V("viz-node"), stroke = V("border-strong"), sw = 1.5) {
    return s("circle", { cx, cy, r, style: `fill:${fill};stroke:${stroke};stroke-width:${sw}` });
  }
  function arrow(x1, y1, x2, y2, color = V("fg-muted"), o = {}) {
    const g = s("g");
    const bend = o.bend || 0;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const cx = (x1 + x2) / 2 - (dy / len) * bend;
    const cy = (y1 + y2) / 2 + (dx / len) * bend;
    const d = bend ? `M${x1},${y1} Q${cx},${cy} ${x2},${y2}` : `M${x1},${y1} L${x2},${y2}`;
    const tx = bend ? x2 - cx : dx;
    const ty = bend ? y2 - cy : dy;
    const tl = Math.hypot(tx, ty) || 1;
    const ux = tx / tl;
    const uy = ty / tl;
    const hs = o.head || 7;
    const bx = x2 - ux * hs;
    const by = y2 - uy * hs;
    let st = `fill:none;stroke:${color};stroke-width:${o.sw || 1.6}`;
    if (o.dash) st += `;stroke-dasharray:${o.dash}`;
    g.append(
      s("path", { d, style: st }),
      s("polygon", { points: `${x2},${y2} ${bx - uy * hs * 0.55},${by + ux * hs * 0.55} ${bx + uy * hs * 0.55},${by - ux * hs * 0.55}`, style: `fill:${color}` }),
    );
    return g;
  }
  function toolbar(ui) {
    const b = h("div", { class: "viz-controls" });
    ui.controls.before(b);
    return b;
  }
  function field(value = "", width = 90, ph = "") {
    return input({ value, placeholder: ph, style: `width:${width}px`, "aria-label": ph || "value" });
  }
  function onEnter(inp, fn) {
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); fn(); } });
  }
  function checkbox(text, checked, onChange) {
    const cb = h("input", { type: "checkbox" });
    cb.checked = !!checked;
    cb.addEventListener("change", () => onChange(cb.checked));
    return label(text, cb);
  }
  /** Frame history: each operation appends frames; the player can step back through everything. */
  function timeline(ui, draw) {
    let frames = [];
    const P = player(ui.controls, (f, i) => { draw(f, i); ui.setLog(esc(f.log || "")); });
    return {
      P,
      reset(f) { frames = [f]; P.load(frames, 0); },
      add(list) {
        if (!list.length) return;
        let start = frames.length;
        frames = frames.concat(list);
        const extra = frames.length - 800;
        if (extra > 0) { frames = frames.slice(extra); start = Math.max(0, start - extra); }
        P.load(frames, start);
        if (list.length > 1) P.toggle();
      },
    };
  }
  const parseKey = (t) => (/^-?\d+$/.test(t) ? Number(t) : t);
  const showKey = (k) => (typeof k === "number" ? String(k) : `'${k}'`);
  function fnv1a(str) {
    let x = 0x811c9dc5;
    for (const ch of String(str)) { x ^= ch.codePointAt(0); x = Math.imul(x, 0x01000193); }
    return x >>> 0;
  }
  function djb2(str) {
    let x = 5381;
    for (const ch of String(str)) x = (Math.imul(x, 33) + ch.codePointAt(0)) >>> 0;
    return x >>> 0;
  }
  const WORDS = ["apple", "banana", "cherry", "date", "fig", "grape", "kiwi", "lemon", "mango", "melon", "olive", "peach", "pear", "plum", "lime", "guava"];

  /* ---------- references ---------- */
  const rf = (id) => ({ ref: id });
  const lst = (col, ...c) => ({ t: "list", col, c });
  const tup = (col, ...c) => ({ t: "tuple", col, c });
  const val = (col, t, v) => ({ t, col, v });
  const G = (...vars) => [["Global", vars]];
  const REF_SCENARIOS = {
    alias: {
      title: "Aliasing: b = a shares one list",
      code: ["a = [1, 2, 3]", "b = a", "b.append(4)", "print(a)", "print(a is b)"],
      steps: [
        { line: -1, log: "Before running: the global frame has no names yet.", f: G(), o: {} },
        { line: 0, log: "The list display builds a new list object, then binds the name a to it. A name is just a label pointing at an object.", f: G(["a", rf("o1")]), o: { o1: lst(0, 1, 2, 3) }, hl: ["a", "o1"] },
        { line: 1, log: "b = a copies the reference, not the list. Both names now point at the very same object.", f: G(["a", rf("o1")], ["b", rf("o1")]), o: { o1: lst(0, 1, 2, 3) }, hl: ["b"] },
        { line: 2, log: "b.append(4) mutates the one shared list in place, so the change is visible through a too.", f: G(["a", rf("o1")], ["b", rf("o1")]), o: { o1: lst(0, 1, 2, 3, 4) }, hl: ["o1"] },
        { line: 3, log: "print(a) shows the mutated list: a and b are two names for one object.", f: G(["a", rf("o1")], ["b", rf("o1")]), o: { o1: lst(0, 1, 2, 3, 4) }, out: "[1, 2, 3, 4]" },
        { line: 4, log: "a is b compares identity (id(a) == id(b)), not contents. Same object, so True.", f: G(["a", rf("o1")], ["b", rf("o1")]), o: { o1: lst(0, 1, 2, 3, 4) }, out: "[1, 2, 3, 4]\nTrue" },
      ],
    },
    rebind: {
      title: "Rebinding a name never changes the old object",
      code: ["a = [1, 2, 3]", "b = a", "b = [9, 9]", "print(a)", "x = 10", "y = x", "y += 1", "print(x, y)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "a is bound to a new list object.", f: G(["a", rf("o1")]), o: { o1: lst(0, 1, 2, 3) }, hl: ["a", "o1"] },
        { line: 1, log: "b = a: b now refers to the same list as a.", f: G(["a", rf("o1")], ["b", rf("o1")]), o: { o1: lst(0, 1, 2, 3) }, hl: ["b"] },
        { line: 2, log: "Assignment rebinds b to a brand-new list. It does not touch the object b used to name, so a is unaffected.", f: G(["a", rf("o1")], ["b", rf("o2")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9) }, hl: ["b", "o2"] },
        { line: 3, log: "a still names the original list.", f: G(["a", rf("o1")], ["b", rf("o2")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9) }, out: "[1, 2, 3]" },
        { line: 4, log: "Ints are objects too: x names an int object 10.", f: G(["a", rf("o1")], ["b", rf("o2")], ["x", rf("o3")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9), o3: val(1, "int", "10") }, hl: ["x", "o3"], out: "[1, 2, 3]" },
        { line: 5, log: "y = x: both names refer to the same int object.", f: G(["a", rf("o1")], ["b", rf("o2")], ["x", rf("o3")], ["y", rf("o3")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9), o3: val(1, "int", "10") }, hl: ["y"], out: "[1, 2, 3]" },
        { line: 6, log: "Ints are immutable, so y += 1 cannot change the object. It computes a new int 11 and rebinds y; x still names 10.", f: G(["a", rf("o1")], ["b", rf("o2")], ["x", rf("o3")], ["y", rf("o4")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9), o3: val(1, "int", "10"), o4: val(1, "int", "11") }, hl: ["y", "o4"], out: "[1, 2, 3]" },
        { line: 7, log: "For immutable objects, aliasing can never surprise you: any 'change' makes a new object.", f: G(["a", rf("o1")], ["b", rf("o2")], ["x", rf("o3")], ["y", rf("o4")]), o: { o1: lst(0, 1, 2, 3), o2: lst(0, 9, 9), o3: val(1, "int", "10"), o4: val(1, "int", "11") }, out: "[1, 2, 3]\n10 11" },
      ],
    },
    copy: {
      title: "Shallow copy: new outer list, shared inner lists",
      code: ["a = [[1, 2], [3, 4]]", "b = a.copy()      # same as list(a) or a[:]", "b.append([5, 6])", "b[0].append(99)", "print(a)", "print(b)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "The outer list holds references to two separate inner list objects.", f: G(["a", rf("o1")]), o: { o1: lst(0, rf("o2"), rf("o3")), o2: lst(1, 1, 2), o3: lst(1, 3, 4) }, hl: ["a", "o1"] },
        { line: 1, log: "A shallow copy makes a NEW outer list but copies only the references inside it: both outer lists point at the same inner lists.", f: G(["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o2"), rf("o3")), o2: lst(1, 1, 2), o3: lst(1, 3, 4) }, hl: ["b", "o4"] },
        { line: 2, log: "Appending to b changes only b's outer list; a still has two items.", f: G(["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o2"), rf("o3"), rf("o5")), o2: lst(1, 1, 2), o3: lst(1, 3, 4), o5: lst(1, 5, 6) }, hl: ["o4", "o5"] },
        { line: 3, log: "b[0] is the same inner list as a[0], so this mutation shows up through a as well.", f: G(["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o2"), rf("o3"), rf("o5")), o2: lst(1, 1, 2, 99), o3: lst(1, 3, 4), o5: lst(1, 5, 6) }, hl: ["o2"] },
        { line: 4, log: "a sees 99 (shared inner list) but not [5, 6] (b's own outer list).", f: G(["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o2"), rf("o3"), rf("o5")), o2: lst(1, 1, 2, 99), o3: lst(1, 3, 4), o5: lst(1, 5, 6) }, out: "[[1, 2, 99], [3, 4]]" },
        { line: 5, log: "Use copy.deepcopy when nested mutable objects must be independent.", f: G(["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o2"), rf("o3"), rf("o5")), o2: lst(1, 1, 2, 99), o3: lst(1, 3, 4), o5: lst(1, 5, 6) }, out: "[[1, 2, 99], [3, 4]]\n[[1, 2, 99], [3, 4], [5, 6]]" },
      ],
    },
    deepcopy: {
      title: "copy.deepcopy: nothing mutable is shared",
      code: ["import copy", "a = [[1, 2], [3, 4]]", "b = copy.deepcopy(a)", "b[0].append(99)", "print(a)", "print(b)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "import binds the name copy to the module object.", f: G(["copy", rf("m")]), o: { m: val(1, "module", "copy") }, hl: ["copy"] },
        { line: 1, log: "a names an outer list holding two inner lists.", f: G(["copy", rf("m")], ["a", rf("o1")]), o: { o1: lst(0, rf("o2"), rf("o3")), m: val(1, "module", "copy"), o2: lst(1, 1, 2), o3: lst(1, 3, 4) }, hl: ["a", "o1"] },
        { line: 2, log: "deepcopy recursively copies every nested object, so b's inner lists are new objects too.", f: G(["copy", rf("m")], ["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o5"), rf("o6")), m: val(1, "module", "copy"), o2: lst(1, 1, 2), o3: lst(1, 3, 4), o5: lst(1, 1, 2), o6: lst(1, 3, 4) }, hl: ["b", "o4", "o5", "o6"] },
        { line: 3, log: "Mutating b[0] changes only b's private inner list.", f: G(["copy", rf("m")], ["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o5"), rf("o6")), m: val(1, "module", "copy"), o2: lst(1, 1, 2), o3: lst(1, 3, 4), o5: lst(1, 1, 2, 99), o6: lst(1, 3, 4) }, hl: ["o5"] },
        { line: 4, log: "a is untouched.", f: G(["copy", rf("m")], ["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o5"), rf("o6")), m: val(1, "module", "copy"), o2: lst(1, 1, 2), o3: lst(1, 3, 4), o5: lst(1, 1, 2, 99), o6: lst(1, 3, 4) }, out: "[[1, 2], [3, 4]]" },
        { line: 5, log: "deepcopy costs time and memory proportional to everything reachable, so use it only when you need independence.", f: G(["copy", rf("m")], ["a", rf("o1")], ["b", rf("o4")]), o: { o1: lst(0, rf("o2"), rf("o3")), o4: lst(0, rf("o5"), rf("o6")), m: val(1, "module", "copy"), o2: lst(1, 1, 2), o3: lst(1, 3, 4), o5: lst(1, 1, 2, 99), o6: lst(1, 3, 4) }, out: "[[1, 2], [3, 4]]\n[[1, 2, 99], [3, 4]]" },
      ],
    },
    immutable: {
      title: "Immutable objects (and why tuple immutability is shallow)",
      code: ['s = "hi"', "t = s", 't += "!"', "print(s, t)", "n = (1, [2])", "n[1].append(3)", "print(n)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "s names a str object.", f: G(["s", rf("o1")]), o: { o1: val(0, "str", '"hi"') }, hl: ["s", "o1"] },
        { line: 1, log: "t = s: two names, one string object.", f: G(["s", rf("o1")], ["t", rf("o1")]), o: { o1: val(0, "str", '"hi"') }, hl: ["t"] },
        { line: 2, log: "Strings are immutable: += builds a new string and rebinds t. s still names the original.", f: G(["s", rf("o1")], ["t", rf("o2")]), o: { o1: val(0, "str", '"hi"'), o2: val(0, "str", '"hi!"') }, hl: ["t", "o2"] },
        { line: 3, log: "Two different objects now.", f: G(["s", rf("o1")], ["t", rf("o2")]), o: { o1: val(0, "str", '"hi"'), o2: val(0, "str", '"hi!"') }, out: "hi hi!" },
        { line: 4, log: "A tuple's slots cannot be reassigned, but a slot can hold a reference to a mutable list.", f: G(["s", rf("o1")], ["t", rf("o2")], ["n", rf("o3")]), o: { o1: val(0, "str", '"hi"'), o2: val(0, "str", '"hi!"'), o3: tup(0, 1, rf("o4")), o4: lst(1, 2) }, hl: ["n", "o3"], out: "hi hi!" },
        { line: 5, log: "The tuple still holds the same list (same identity), and that list was mutated in place. Immutability is shallow; hash(n) would now raise TypeError because the tuple contains a list.", f: G(["s", rf("o1")], ["t", rf("o2")], ["n", rf("o3")]), o: { o1: val(0, "str", '"hi"'), o2: val(0, "str", '"hi!"'), o3: tup(0, 1, rf("o4")), o4: lst(1, 2, 3) }, hl: ["o4"], out: "hi hi!" },
        { line: 6, log: "The tuple's contents look different even though the tuple itself never changed.", f: G(["s", rf("o1")], ["t", rf("o2")], ["n", rf("o3")]), o: { o1: val(0, "str", '"hi"'), o2: val(0, "str", '"hi!"'), o3: tup(0, 1, rf("o4")), o4: lst(1, 2, 3) }, out: "hi hi!\n(1, [2, 3])" },
      ],
    },
    "default-arg": {
      title: "The mutable default argument trap",
      code: ["def add(item, bucket=[]):", "    bucket.append(item)", "    return bucket", "r1 = add(1)", "r2 = add(2)", "print(r1, r2, r1 is r2)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "def runs ONCE: it creates the function object and evaluates the default [] right now, storing that single list in add.__defaults__.", f: G(["add", rf("fn")]), o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1) }, hl: ["add", "fn", "o1"] },
        { line: 3, log: "Calling add(1) without bucket: a new frame is created and bucket is bound to the stored default list.", f: [["Global", [["add", rf("fn")]]], ["add", [["item", 1], ["bucket", rf("o1")]]]], o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1) }, hl: ["bucket"] },
        { line: 1, log: "append mutates the default list itself.", f: [["Global", [["add", rf("fn")]]], ["add", [["item", 1], ["bucket", rf("o1")]]]], o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1) }, hl: ["o1"] },
        { line: 2, log: "return hands back a reference to that same default list.", f: [["Global", [["add", rf("fn")]]], ["add", [["item", 1], ["bucket", rf("o1")]]]], o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1) } },
        { line: 3, log: "The frame is gone; r1 now names the default list.", f: G(["add", rf("fn")], ["r1", rf("o1")]), o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1) }, hl: ["r1"] },
        { line: 4, log: "The second call gets the SAME default list, not a fresh one, because defaults are evaluated at def time.", f: [["Global", [["add", rf("fn")], ["r1", rf("o1")]]], ["add", [["item", 2], ["bucket", rf("o1")]]]], o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1) }, hl: ["bucket"] },
        { line: 1, log: "append adds 2 to the shared list, so r1 'changes' too.", f: [["Global", [["add", rf("fn")], ["r1", rf("o1")]]], ["add", [["item", 2], ["bucket", rf("o1")]]]], o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1, 2) }, hl: ["o1"] },
        { line: 4, log: "r2 names the same list as r1.", f: G(["add", rf("fn")], ["r1", rf("o1")], ["r2", rf("o1")]), o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1, 2) }, hl: ["r2"] },
        { line: 5, log: "Fix: write bucket=None and inside the function: if bucket is None: bucket = []. Then every call makes its own list.", f: G(["add", rf("fn")], ["r1", rf("o1")], ["r2", rf("o1")]), o: { fn: { t: "function", col: 0, title: "add(item, bucket=[])", c: [rf("o1")] }, o1: lst(1, 1, 2) }, out: "[1, 2] [1, 2] True" },
      ],
    },
    nested: {
      title: "Nested lists: [row] * 3 repeats one reference",
      code: ["row = [0] * 3", "grid = [row] * 3", "grid[0][0] = 1", "print(grid)", "grid = [[0] * 3 for _ in range(3)]", "grid[0][0] = 1", "print(grid)"],
      steps: [
        { line: -1, log: "Before running: no names yet.", f: G(), o: {} },
        { line: 0, log: "[0] * 3 makes one list with three slots.", f: G(["row", rf("o1")]), o: { o2: lst(0), o1: lst(1, 0, 0, 0) }, hl: ["row", "o1"], hide: ["o2"] },
        { line: 1, log: "* 3 repeats the REFERENCE: all three slots of grid point at the same row object.", f: G(["row", rf("o1")], ["grid", rf("o2")]), o: { o2: lst(0, rf("o1"), rf("o1"), rf("o1")), o1: lst(1, 0, 0, 0) }, hl: ["grid", "o2"] },
        { line: 2, log: "Writing through grid[0] mutates the one shared row, so every 'row' of grid shows the change.", f: G(["row", rf("o1")], ["grid", rf("o2")]), o: { o2: lst(0, rf("o1"), rf("o1"), rf("o1")), o1: lst(1, 1, 0, 0) }, hl: ["o1"] },
        { line: 3, log: "The classic surprise.", f: G(["row", rf("o1")], ["grid", rf("o2")]), o: { o2: lst(0, rf("o1"), rf("o1"), rf("o1")), o1: lst(1, 1, 0, 0) }, out: "[[1, 0, 0], [1, 0, 0], [1, 0, 0]]" },
        { line: 4, log: "The comprehension evaluates [0] * 3 once per iteration, creating three independent rows. The old grid list has no references left, so CPython frees it.", f: G(["row", rf("o1")], ["grid", rf("o3")]), o: { o2: { ...lst(0, rf("o1"), rf("o1"), rf("o1")), gc: true }, o3: lst(0, rf("o4"), rf("o5"), rf("o6")), o1: lst(1, 1, 0, 0), o4: lst(1, 0, 0, 0), o5: lst(1, 0, 0, 0), o6: lst(1, 0, 0, 0) }, hl: ["grid", "o3"], out: "[[1, 0, 0], [1, 0, 0], [1, 0, 0]]" },
        { line: 5, log: "Only the first row changes now.", f: G(["row", rf("o1")], ["grid", rf("o3")]), o: { o3: lst(0, rf("o4"), rf("o5"), rf("o6")), o1: lst(1, 1, 0, 0), o4: lst(1, 1, 0, 0), o5: lst(1, 0, 0, 0), o6: lst(1, 0, 0, 0) }, hl: ["o4"], out: "[[1, 0, 0], [1, 0, 0], [1, 0, 0]]" },
        { line: 6, log: "Each row is its own object.", f: G(["row", rf("o1")], ["grid", rf("o3")]), o: { o3: lst(0, rf("o4"), rf("o5"), rf("o6")), o1: lst(1, 1, 0, 0), o4: lst(1, 1, 0, 0), o5: lst(1, 0, 0, 0), o6: lst(1, 0, 0, 0) }, out: "[[1, 0, 0], [1, 0, 0], [1, 0, 0]]\n[[1, 0, 0], [0, 0, 0], [0, 0, 0]]" },
      ],
    },
  };

  function drawRefs(st) {
    const W = 680;
    const FX = 8;
    const FW = 178;
    const COLX = [236, 470];
    const g = s("g");
    const arrows = [];
    const hl = new Set(st.hl || []);
    let y = 8;
    st.f.forEach(([fname, vars], fi) => {
      const top = y;
      const hh = 30 + Math.max(1, vars.length) * 34;
      g.append(R(FX, top, FW, hh, fi ? V("bg-sunk") : V("bg-elev"), V("border-strong"), { rx: 6 }));
      g.append(T(FX + 10, top + 14, fi ? `${fname}() frame` : "Global frame", { anchor: "start", size: 11, fill: V("fg-muted"), weight: 700 }));
      vars.forEach(([name, tgt], vi) => {
        const cy = top + 42 + vi * 34;
        const on = hl.has(name);
        g.append(T(FX + FW - 54, cy, name, { anchor: "end", weight: 700 }));
        g.append(R(FX + FW - 44, cy - 13, 36, 26, V("bg-elev"), on ? ACT : V("border-strong"), { sw: on ? 3 : 1.3, rx: 3 }));
        if (tgt && tgt.ref) {
          g.append(Ci(FX + FW - 26, cy, 3.5, V("fg"), V("fg"), 1));
          arrows.push({ x: FX + FW - 26, y: cy, ref: tgt.ref });
        } else g.append(T(FX + FW - 26, cy, tgt));
      });
      y += hh + 10;
    });
    const colY = [8, 8];
    const pos = {};
    Object.keys(st.o).forEach((id, k) => {
      const o = st.o[id];
      if ((st.hide || []).includes(id)) return;
      const col = o.col || 0;
      const x = COLX[col];
      const top = colY[col];
      const on = hl.has(id);
      const stroke = on ? ACT : V("border-strong");
      const sw = on ? 3 : 1.3;
      const og = s("g", { style: o.gc ? "opacity:0.45" : "" });
      if (o.t === "list" || o.t === "tuple") {
        if (!o.c.length) og.append(R(x, top + 14, 40, 30, V("bg-elev"), stroke, { sw, dash: "4 3", rx: 0 }), T(x + 20, top + 29, "empty", { size: 9, fill: V("fg-faint") }));
        o.c.forEach((c, i) => {
          const cx = x + i * 36;
          og.append(R(cx, top + 14, 36, 30, V("bg-elev"), stroke, { sw, rx: 0 }));
          og.append(T(cx + 18, top + 52, i, { size: 9, fill: V("fg-faint") }));
          if (c && c.ref) { og.append(Ci(cx + 18, top + 29, 3.5, V("fg"), V("fg"), 1)); arrows.push({ x: cx + 18, y: top + 29, ref: c.ref, gc: o.gc }); } else og.append(T(cx + 18, top + 29, c));
        });
      } else if (o.t === "function") {
        const w = 200;
        og.append(R(x, top + 14, w, 30, V("bg-elev"), stroke, { sw }), T(x + 8, top + 29, o.title, { anchor: "start", size: 11 }));
        og.append(R(x + w - 30, top + 18, 24, 22, V("bg-sunk"), V("border-strong"), { rx: 3 }), T(x + w - 18, top + 52, "__defaults__", { size: 9, fill: V("fg-faint") }));
        og.append(Ci(x + w - 18, top + 29, 3.5, V("fg"), V("fg"), 1));
        arrows.push({ x: x + w - 18, y: top + 29, ref: o.c[0].ref });
      } else {
        const w = Math.max(46, String(o.v).length * 8.5 + 18);
        og.append(R(x, top + 14, w, 30, V("bg-elev"), stroke, { sw }), T(x + w / 2, top + 29, o.v));
      }
      og.append(T(x, top + 5, o.t + (o.gc ? "  (no references left → freed)" : ""), { anchor: "start", size: 10, fill: o.gc ? V("bad") : V("fg-muted") }));
      g.append(og);
      pos[id] = { x, y: top + 29, color: PALETTE[k % 6] };
      colY[col] = top + 72;
    });
    for (const a of arrows) {
      const t = pos[a.ref];
      if (!t) continue;
      const ex = t.x - 2;
      const back = ex < a.x + 24;
      g.append(arrow(a.x, a.y, back ? t.x + 8 : ex, back ? t.y - 15 : t.y, t.color, { bend: back ? -30 : 0, dash: a.gc ? "4 3" : null }));
    }
    const H = Math.max(y, colY[0], colY[1]) + 4;
    const svg = svgBox(W, H);
    svg.append(g);
    return svg;
  }

  registerViz("references", (el, cfg) => {
    let key = REF_SCENARIOS[cfg.scenario] ? cfg.scenario : "alias";
    const ui = shell(el, { title: REF_SCENARIOS[key].title, kind: "Names → objects" });
    const tb = toolbar(ui);
    const box = "font:0.82rem/1.55 var(--font-mono);background:var(--bg-code);border:1px solid var(--border);border-radius:6px;padding:6px 0;margin:0 auto 10px;max-width:680px;overflow-x:auto";
    const draw = (st) => {
      const sc = REF_SCENARIOS[key];
      const code = h("div", { style: box, "aria-label": "Code" });
      sc.code.forEach((ln, i) => {
        const cur = i === st.line;
        code.append(h("div", { style: `padding:0 10px;white-space:pre;${cur ? "background:color-mix(in srgb, var(--viz-active) 40%, transparent);font-weight:700" : ""}` },
          h("span", { style: "color:var(--fg-faint);display:inline-block;width:2.6em", text: `${cur ? "→" : " "}${i + 1}` }), ln));
      });
      const parts = [code, drawRefs(st)];
      if (st.out) parts.push(h("div", { style: `${box};margin-top:10px;padding:6px 10px;white-space:pre-wrap` }, h("span", { style: "color:var(--fg-faint)", text: "Output\n" }), st.out));
      ui.stage.replaceChildren(...parts);
    };
    const P = player(ui.controls, (f) => { draw(f); ui.setLog(esc(f.log)); }, { speed: 1200 });
    const load = () => { ui.head.querySelector(".w-title").textContent = REF_SCENARIOS[key].title; P.load(REF_SCENARIOS[key].steps, 0); };
    tb.append(label("scenario", select(Object.keys(REF_SCENARIOS).map((k) => [k, k]), key, (v) => { key = v; load(); })), button("Restart", () => { P.stop(); P.go(0); }));
    ui.setLegend([["highlight = just changed", ACT], ["arrow = reference", V("viz-1")]]);
    load();
  });

  /* ---------- bigo ---------- */
  registerViz("bigo", (el, cfg) => {
    const ALL = ["1", "log n", "n", "n log n", "n^2", "n^3", "2^n", "n!"];
    const FN = {
      "1": () => 1, "log n": (n) => Math.log2(n), n: (n) => n, "n log n": (n) => n * Math.log2(n),
      "n^2": (n) => n * n, "n^3": (n) => n ** 3, "2^n": (n) => 2 ** n,
      "n!": (n) => { let r = 1; for (let i = 2; i <= n; i++) r *= i; return r; },
    };
    const COLOR = Object.fromEntries(ALL.map((f, i) => [f, i < 6 ? PALETTE[i] : i === 6 ? V("note") : V("fg-muted")]));
    const POLY = new Set(["1", "log n", "n", "n log n", "n^2", "n^3"]);
    const active = new Set((Array.isArray(cfg.functions) ? cfg.functions : ALL).filter((f) => FN[f]));
    if (!active.size) ALL.forEach((f) => active.add(f));
    const maxN = Math.max(4, Math.min(500, Math.round(Number(cfg.maxN) || 32)));
    let logScale = false;
    let curN = Math.min(maxN, 16);
    const clipId = `bigo-clip-${++uid}`;
    const ui = shell(el, { title: "How running time grows with n", kind: "Big-O" });
    const tb = toolbar(ui);
    const fmt = (v) => (!Number.isFinite(v) ? "> 1e308" : v < 1e6 ?(Number.isInteger(v) ? v.toLocaleString("en-US") : v.toFixed(1)) : v.toExponential(2).replace("e+", "e"));
    const human = (sec) => {
      if (sec < 1e-3) return `${fmtNum(sec * 1e6)} µs`;
      if (sec < 1) return `${fmtNum(sec * 1e3)} ms`;
      if (sec < 60) return `${fmtNum(sec)} s`;
      if (sec < 3600) return `${fmtNum(sec / 60)} min`;
      if (sec < 86400) return `${fmtNum(sec / 3600)} h`;
      if (sec < 3.156e7) return `${fmtNum(sec / 86400)} days`;
      const y = sec / 3.156e7;
      return y < 1e6 ? `${fmtNum(y)} years` : `${y.toExponential(1).replace("e+", "e")} years`;
    };
    function draw(n) {
      const W = 640;
      const H = 300;
      const x0 = 64;
      const x1 = 620;
      const y0 = 16;
      const y1 = 262;
      const fns = ALL.filter((f) => active.has(f));
      const svg = svgBox(W, H);
      const X = (v) => x0 + ((v - 1) / (maxN - 1)) * (x1 - x0);
      let yMax;
      let Y;
      const ticks = [];
      if (logScale) {
        const top = Math.min(1e300, Math.max(1, ...fns.map((f) => FN[f](maxN))));
        const dec = Math.max(1, Math.ceil(Math.log10(top)));
        yMax = dec;
        Y = (v) => y1 - (Math.log10(Math.max(v, 1)) / yMax) * (y1 - y0);
        const step = Math.max(1, Math.ceil(dec / 8));
        for (let d = 0; d <= dec; d += step) ticks.push([10 ** d, d < 6 ? (10 ** d).toLocaleString("en-US") : `1e${d}`]);
      } else {
        const poly = fns.filter((f) => POLY.has(f));
        yMax = Math.max(1, ...(poly.length ? poly : fns).map((f) => FN[f](maxN))) * 1.05;
        if (!poly.length) yMax = Math.min(yMax, 1e6);
        Y = (v) => y1 - (v / yMax) * (y1 - y0);
        for (let i = 0; i <= 5; i++) { const v = (yMax / 5) * i; ticks.push([v, fmt(Math.round(v))]); }
      }
      svg.append(s("defs", {}, s("clipPath", { id: clipId }, s("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0 }))));
      for (const [v, t] of ticks) { const yy = Y(v); svg.append(L(x0, yy, x1, yy, V("border"), 1), T(x0 - 6, yy, t, { anchor: "end", size: 10, fill: V("fg-muted") })); }
      for (let i = 0; i <= 4; i++) { const v = Math.round(1 + ((maxN - 1) * i) / 4); svg.append(T(X(v), y1 + 14, v, { size: 10, fill: V("fg-muted") })); }
      svg.append(L(x0, y0, x0, y1, V("fg-faint"), 1.2), L(x0, y1, x1, y1, V("fg-faint"), 1.2));
      svg.append(T((x0 + x1) / 2, y1 + 30, "n (input size)", { size: 11, fill: V("fg-muted") }));
      svg.append(T(14, (y0 + y1) / 2, logScale ? "operations (log scale)" : "operations", { size: 11, fill: V("fg-muted") }));
      svg.lastChild.setAttribute("transform", `rotate(-90 14 ${(y0 + y1) / 2})`);
      const plot = s("g", { "clip-path": `url(#${clipId})` });
      for (const f of fns) {
        const pts = [];
        for (let v = 1; v <= maxN; v += Math.max(1, Math.floor(maxN / 200))) pts.push(`${X(v).toFixed(1)},${Math.max(-1e4, Y(FN[f](v))).toFixed(1)}`);
        pts.push(`${X(maxN).toFixed(1)},${Math.max(-1e4, Y(FN[f](maxN))).toFixed(1)}`);
        plot.append(s("polyline", { points: pts.join(" "), style: `fill:none;stroke:${COLOR[f]};stroke-width:2.2` }));
      }
      plot.append(L(X(n), y0, X(n), y1, V("fg-faint"), 1.2, "4 3"));
      for (const f of fns) { const yy = Y(FN[f](n)); if (yy >= y0 - 2) plot.append(Ci(X(n), yy, 4, COLOR[f], V("bg-elev"), 1.5)); }
      svg.append(plot, T(Math.min(X(n) + 4, x1 - 30), y0 + 8, `n = ${n}`, { anchor: "start", size: 11, weight: 700 }));
      const rows = fns.map((f) => h("tr", {},
        h("td", { style: `padding:2px 10px;color:${COLOR[f]};font-weight:700` }, `O(${f})`),
        h("td", { style: "padding:2px 10px;text-align:right" }, fmt(FN[f](n))),
        h("td", { style: "padding:2px 10px;text-align:right;color:var(--fg-muted)" }, human(FN[f](n) * 1e-6))));
      const table = h("table", { style: "margin:10px auto 0;font:0.8rem var(--font-mono);border-collapse:collapse" },
        h("thead", {}, h("tr", {}, ...["growth", `operations at n = ${n}`, "time at 1 µs per operation"].map((t) => h("th", { style: "padding:2px 10px;color:var(--fg-muted);font-weight:600;text-align:right" }, t)))),
        h("tbody", {}, rows));
      ui.stage.replaceChildren(svg, table);
      if (fns.length) {
        const vals = fns.map((f) => [f, FN[f](n)]).sort((a, b) => a[1] - b[1]);
        const [lo, hi] = [vals[0], vals[vals.length - 1]];
        const offChart = !logScale && fns.some((f) => !POLY.has(f) && FN[f](n) > yMax);
        ui.setLog(esc(`n = ${n}: the cheapest curve O(${lo[0]}) costs ${fmt(lo[1])} operations, the costliest O(${hi[0]}) costs ${fmt(hi[1])}${lo[1] > 0 ? ` (${fmt(Math.round(hi[1] / Math.max(lo[1], 1e-9)))}× more)` : ""}.${offChart ? " Exponential curves leave the linear chart: switch to log scale to see them." : ""}`));
      } else ui.setLog("Tick at least one growth function.");
    }
    const slider = h("input", { type: "range", min: 1, max: maxN, value: curN, "aria-label": "n" });
    const P = player(ui.controls, (f) => { curN = f.n; slider.value = f.n; draw(f.n); }, { speed: 300 });
    slider.addEventListener("input", () => { P.stop(); P.go(Number(slider.value) - 1); });
    tb.append(label("n", slider), label("y-axis", select([["linear", "linear"], ["log", "log"]], "linear", (v) => { logScale = v === "log"; draw(curN); })));
    const tb2 = toolbar(ui);
    for (const f of ALL) {
      const lab = checkbox("", active.has(f), (on) => { if (on) active.add(f); else active.delete(f); draw(curN); });
      lab.append(h("span", { style: `color:${COLOR[f]};font-weight:700;font-family:var(--font-mono)` }, `O(${f})`));
      tb2.append(lab);
    }
    P.load(Array.from({ length: maxN }, (_, i) => ({ n: i + 1 })), curN - 1);
  });

  /* ---------- dynamic-array ---------- */
  registerViz("dynamic-array", (el, cfg) => {
    let growth = Number(cfg.growth) > 1 ? Number(cfg.growth) : 1.125;
    const isCPy = () => Math.abs(growth - 1.125) < 1e-9;
    const MAX = 96;
    const ui = shell(el, { title: "list.append and capacity growth", kind: "Dynamic array" });
    const tb = toolbar(ui);
    let M;
    const reset = () => { M = { items: [], cap: 0, copies: 0, writes: 0, appends: 0, costs: [], resizes: [] }; };
    function grow(size, cap) {
      const ns = size + 1;
      if (isCPy()) {
        const raw = ns + (ns >> 3) + 6;
        let na = raw & ~3;
        if (ns - size > na - ns) na = (ns + 3) & ~3;
        return { cap: na, why: `list_resize: new_allocated = ${ns} + (${ns} >> 3) + 6 = ${raw}, rounded down to a multiple of 4 → ${na}` };
      }
      const nc = Math.max(cap + 1, Math.floor(cap * growth));
      return { cap: nc, why: `new capacity = max(${cap} + 1, ⌊${cap} × ${growth}⌋) = ${nc}` };
    }
    const snap = (log, extra = {}) => ({ ...deep(M), old: null, hl: {}, ...extra, log });
    function append(v) {
      const F = [];
      if (M.appends >= MAX) return [snap(`Stopping at ${MAX} appends to keep the picture readable. Press Reset to start over.`)];
      const n = M.items.length;
      M.appends++;
      if (n < M.cap) {
        M.items.push(v);
        M.writes++;
        M.costs.push(1);
        F.push(snap(`append(${v}): length ${n} < capacity ${M.cap}, so write into free slot ${n}. Cost 1, no copying.`, { hl: { [n]: NEW } }));
        return F;
      }
      const old = { items: [...M.items], cap: M.cap };
      const g = grow(n, M.cap);
      F.push(snap(`append(${v}): the buffer is full (length ${n} == capacity ${M.cap}). Allocate a bigger buffer. ${g.why}.`, { old, cap: g.cap, items: [] }));
      M.cap = g.cap;
      M.resizes.push(M.appends - 1);
      if (n) {
        M.copies += n;
        F.push(snap(`Copy the ${n} existing references into the new buffer (cost ${n}). Total copies so far: ${M.copies}. The old buffer is then freed.`, { old, hl: Object.fromEntries(M.items.map((_, i) => [i, SOFT(2)])) }));
      }
      M.items.push(v);
      M.writes++;
      M.costs.push(1 + n);
      const avg = (M.writes + M.copies) / M.appends;
      F.push(snap(`Write ${v} into slot ${n}. This append cost ${1 + n}, but averaged over all ${M.appends} appends the cost is ${avg.toFixed(2)} per append: amortized O(1).`, { hl: { [n]: NEW } }));
      return F;
    }
    function drawBuf(g, items, cap, y, hl, title, faded) {
      const per = 16;
      g.append(T(20, y + 6, title, { anchor: "start", size: 11, fill: faded ? V("fg-faint") : V("fg-muted"), weight: 700 }));
      const rows = Math.max(1, Math.ceil(cap / per));
      if (!cap) g.append(T(20, y + 30, "(no buffer allocated)", { anchor: "start", size: 11, fill: V("fg-faint") }));
      for (let i = 0; i < cap; i++) {
        const x = 20 + (i % per) * 37;
        const yy = y + 16 + Math.floor(i / per) * 40;
        const has = i < items.length;
        g.append(R(x, yy, 34, 28, hl[i] || (has ? V("viz-node") : V("bg-sunk")), has ? V("border-strong") : V("border"), { dash: has ? null : "3 3", op: faded ? 0.5 : null, rx: 3 }));
        if (has) g.append(T(x + 17, yy + 14, items[i], { size: 11, op: faded ? 0.5 : null }));
        g.append(T(x + 17, yy + 34, i, { size: 7.5, fill: V("fg-faint") }));
      }
      return 16 + rows * 40 + 8;
    }
    function draw(f) {
      const W = 640;
      const g = s("g");
      g.append(T(20, 12, `len = ${f.items.length}   capacity = ${f.cap}   appends = ${f.appends}   element copies = ${f.copies}   amortized cost = ${f.appends ? ((f.writes + f.copies) / f.appends).toFixed(2) : "0"}`, { anchor: "start", size: 11.5, weight: 700 }));
      let y = 28;
      if (f.old) y += drawBuf(g, f.old.items, f.old.cap, y, {}, `old buffer (capacity ${f.old.cap})`, true);
      y += drawBuf(g, f.items, f.cap, y, f.hl, f.old ? `new buffer (capacity ${f.cap})` : `buffer (capacity ${f.cap})`, false);
      const ch = 80;
      const top = y + 14;
      g.append(T(20, top - 4, "cost of each append (bars) and running average (line)", { anchor: "start", size: 10.5, fill: V("fg-muted") }));
      g.append(L(20, top + ch, 620, top + ch, V("fg-faint"), 1));
      if (f.costs.length) {
        const maxC = Math.max(...f.costs, 2);
        const bw = Math.min(12, 600 / f.costs.length);
        let run = 0;
        const pts = [];
        f.costs.forEach((c, i) => {
          const bh = (c / maxC) * (ch - 6);
          g.append(R(20 + i * bw, top + ch - bh, Math.max(1, bw - 1), bh, c > 1 ? V("viz-2") : V("viz-1"), "none", { rx: 0, sw: 0 }));
          run += c;
          pts.push(`${20 + i * bw + bw / 2},${top + ch - (run / (i + 1) / maxC) * (ch - 6)}`);
        });
        g.append(s("polyline", { points: pts.join(" "), style: `fill:none;stroke:${V("viz-4")};stroke-width:2` }));
        g.append(T(620, top + 6, `max cost ${maxC}`, { anchor: "end", size: 10, fill: V("fg-faint") }));
      }
      const svg = svgBox(W, top + ch + 10);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const inp = field("", 70, "value");
    const doAppend = (vals) => { const F = []; vals.forEach((v) => F.push(...append(v))); TL.add(F); };
    const appendOne = () => { const v = inp.value.trim() || String(randInt(0, 99)); inp.value = ""; doAppend([v.slice(0, 4)]); };
    onEnter(inp, appendOne);
    const growSel = select([["1.125", "CPython (≈1.125× + 6)"], ["2", "doubling (2×)"], ...(![1.125, 2].includes(growth) ? [[String(growth), `${growth}×`]] : [])], String(growth), (v) => { growth = Number(v); start(); });
    const start = () => { reset(); TL.reset(snap(isCPy() ? "Empty list: length 0, capacity 0. CPython allocates no element buffer until the first append. Over-allocation: about 1/8 extra plus 6, rounded to a multiple of 4." : `Empty list. Growth policy: multiply capacity by ${growth} when full.`)); };
    tb.append(inp, button("Append", appendOne, "btn small primary"), button("Append ×8", () => doAppend(Array.from({ length: 8 }, () => String(randInt(0, 99))))), button("Append ×32", () => doAppend(Array.from({ length: 32 }, () => String(randInt(0, 99))))), label("growth", growSel), button("Reset", start));
    ui.setLegend([["new write", NEW], ["copied on resize", SOFT(2)], ["cheap append", V("viz-1")], ["append that resized", V("viz-2")], ["running average", V("viz-4")]]);
    start();
  });

  /* ---------- linked-list ---------- */
  registerViz("linked-list", (el, cfg) => {
    let doubly = !!cfg.doubly;
    const init = (Array.isArray(cfg.values) ? cfg.values : [3, 7, 1, 9]).slice(0, 9).map(String);
    const MAXN = 9;
    const ui = shell(el, { title: "", kind: "Linked list" });
    const setTitle = () => { ui.head.querySelector(".w-title").textContent = doubly ? "Doubly linked list" : "Singly linked list"; };
    const tb = toolbar(ui);
    const tb2 = toolbar(ui);
    let M;
    let F = [];
    const PTR_COLOR = { head: V("accent"), cur: V("viz-2"), prev: V("viz-5"), nxt: V("viz-6"), new: V("viz-3") };
    function build(vals) {
      M = { nodes: {}, head: null, order: [], nid: 0 };
      let prev = null;
      vals.forEach((v) => {
        const id = `n${M.nid++}`;
        M.nodes[id] = { v, next: null, prev };
        if (prev) M.nodes[prev].next = id; else M.head = id;
        M.order.push(id);
        prev = id;
      });
    }
    const snap = (log, x = {}) => F.push({ ...deep({ nodes: M.nodes, head: M.head, order: M.order }), ptrs: x.ptrs || {}, hl: x.hl || {}, raised: x.raised || null, log });
    const val = (id) => M.nodes[id].v;
    const reorder = () => { const o = []; let c = M.head; const seen = new Set(); while (c && !seen.has(c)) { seen.add(c); o.push(c); c = M.nodes[c].next; } M.order = o; };
    const mk = (v) => { const id = `n${M.nid++}`; M.nodes[id] = { v, next: null, prev: null }; return id; };
    function insertAt(index, v) {
      F = [];
      if (M.order.length >= MAXN) { snap(`The demo holds at most ${MAXN} nodes.`); return F; }
      const n = M.order.length;
      if (index < 0 || index > n) { snap(`Index ${index} is out of range for a list of length ${n}.`); return F; }
      if (index === 0) {
        const id = mk(v);
        M.order.unshift(id);
        snap(`Create node(${v}). Inserting at the head needs no walking: O(1).`, { raised: id, hl: { [id]: NEW }, ptrs: { new: id, head: M.head } });
        M.nodes[id].next = M.head;
        snap(`new.next = head → node(${v}) now points at the old first node${M.head ? ` (${val(M.head)})` : " (None)"}.`, { raised: id, hl: { [id]: NEW }, ptrs: { new: id, head: M.head } });
        if (doubly && M.head) { M.nodes[M.head].prev = id; snap(`head.prev = new: the old first node points back at node(${v}).`, { raised: id, hl: { [id]: NEW }, ptrs: { new: id, head: M.head } }); }
        M.head = id;
        snap(`head = new. Done: ${v} is the first element.`, { hl: { [id]: NEW }, ptrs: { head: id } });
        return F;
      }
      let cur = M.head;
      snap(`Insert ${v} at index ${index}: walk to the node at index ${index - 1}. Start with cur = head.`, { ptrs: { head: M.head, cur }, hl: { [cur]: ACT } });
      for (let i = 0; i < index - 1; i++) {
        cur = M.nodes[cur].next;
        snap(`cur = cur.next → index ${i + 1} (value ${val(cur)}).`, { ptrs: { head: M.head, cur }, hl: { [cur]: ACT } });
      }
      const id = mk(v);
      M.order.splice(index, 0, id);
      snap(`Create node(${v}). Each step so far cost one pointer hop, so reaching index ${index} is O(n).`, { raised: id, ptrs: { head: M.head, cur, new: id }, hl: { [cur]: ACT, [id]: NEW } });
      const after = M.nodes[cur].next;
      M.nodes[id].next = after;
      snap(`new.next = cur.next (${after ? `node(${val(after)})` : "None"}). Link the new node first so nothing is lost.`, { raised: id, ptrs: { head: M.head, cur, new: id }, hl: { [cur]: ACT, [id]: NEW } });
      if (doubly) { M.nodes[id].prev = cur; if (after) M.nodes[after].prev = id; snap(`Doubly linked: new.prev = cur${after ? " and the next node's prev = new" : ""}.`, { raised: id, ptrs: { head: M.head, cur, new: id }, hl: { [cur]: ACT, [id]: NEW } }); }
      M.nodes[cur].next = id;
      snap(`cur.next = new. ${v} is now at index ${index}.`, { ptrs: { head: M.head }, hl: { [id]: NEW } });
      return F;
    }
    function remove(v) {
      F = [];
      if (!M.head) { snap("The list is empty: nothing to delete."); return F; }
      let prev = null;
      let cur = M.head;
      snap(`Delete the first ${v}: prev = None, cur = head.`, { ptrs: { head: M.head, cur }, hl: { [cur]: ACT } });
      while (cur) {
        if (val(cur) === v) {
          snap(`cur.value ${val(cur)} == ${v} → found it.`, { ptrs: { head: M.head, prev, cur }, hl: { [cur]: DEL } });
          const nx = M.nodes[cur].next;
          if (!prev) { M.head = nx; snap(`It is the head, so head = cur.next${nx ? ` (node(${val(nx)}))` : " (None)"}.`, { ptrs: { head: M.head, cur }, hl: { [cur]: DEL }, raised: cur }); } else { M.nodes[prev].next = nx; snap(`prev.next = cur.next: node(${val(prev)}) now skips over node(${v}).`, { ptrs: { head: M.head, prev, cur }, hl: { [cur]: DEL }, raised: cur }); }
          if (doubly && nx) { M.nodes[nx].prev = prev; snap(`Doubly linked: the next node's prev = ${prev ? `node(${val(prev)})` : "None"}.`, { ptrs: { head: M.head, prev, cur }, hl: { [cur]: DEL }, raised: cur }); }
          delete M.nodes[cur];
          M.order = M.order.filter((x) => x !== cur);
          snap(`Nothing refers to node(${v}) any more, so Python frees it. Deletion itself is O(1); finding the node was O(n).`, { ptrs: { head: M.head } });
          return F;
        }
        snap(`cur.value ${val(cur)} != ${v} → advance: prev = cur, cur = cur.next.`, { ptrs: { head: M.head, prev, cur }, hl: { [cur]: ACT } });
        prev = cur;
        cur = M.nodes[cur].next;
        if (cur) snap(`cur is now node(${val(cur)}).`, { ptrs: { head: M.head, prev, cur }, hl: { [cur]: ACT } });
      }
      snap(`cur is None: reached the end, ${v} is not in the list.`, { ptrs: { head: M.head, prev } });
      return F;
    }
    function search(v) {
      F = [];
      let cur = M.head;
      let i = 0;
      snap(`Search for ${v}: start at head. Linked lists have no indexing shortcut, so search is O(n).`, { ptrs: { head: M.head, cur }, hl: cur ? { [cur]: ACT } : {} });
      while (cur) {
        if (val(cur) === v) { snap(`cur.value == ${v} → found at index ${i} after ${i + 1} comparison${i ? "s" : ""}.`, { ptrs: { head: M.head, cur }, hl: { [cur]: DONE } }); return F; }
        snap(`${val(cur)} != ${v} → cur = cur.next.`, { ptrs: { head: M.head, cur }, hl: { [cur]: ACT } });
        cur = M.nodes[cur].next;
        i++;
      }
      snap(`cur is None → ${v} not found after ${i} comparisons.`, { ptrs: { head: M.head } });
      return F;
    }
    function reverse() {
      F = [];
      let prev = null;
      let cur = M.head;
      snap("Reverse in place: prev = None, cur = head. Each step flips one arrow.", { ptrs: { head: M.head, cur }, hl: cur ? { [cur]: ACT } : {} });
      while (cur) {
        const nxt = M.nodes[cur].next;
        snap(`nxt = cur.next (${nxt ? `node(${val(nxt)})` : "None"}): remember the rest of the list before breaking the link.`, { ptrs: { prev, cur, nxt }, hl: { [cur]: ACT } });
        M.nodes[cur].next = prev;
        if (doubly) M.nodes[cur].prev = nxt;
        snap(`cur.next = prev: node(${val(cur)}) now points ${prev ? `back at node(${val(prev)})` : "to None (it will be the new tail)"}${doubly ? "; its prev pointer is swapped too" : ""}.`, { ptrs: { prev, cur, nxt }, hl: { [cur]: ACT } });
        prev = cur;
        cur = nxt;
        snap("prev = cur, cur = nxt: move both pointers one step right.", { ptrs: { prev, cur, nxt }, hl: prev ? { [prev]: DONE } : {} });
      }
      M.head = prev;
      reorder();
      snap("cur is None, so prev is the old tail: head = prev. Reversed in O(n) time with O(1) extra memory.", { ptrs: { head: M.head } });
      return F;
    }
    function draw(f) {
      const n = f.order.length;
      const step = 96;
      const W = Math.max(640, 60 + n * step);
      const nw = doubly ? 76 : 66;
      const baseY = 128;
      const pos = {};
      f.order.forEach((id, i) => { pos[id] = { x: 30 + i * step, y: id === f.raised ? 58 : baseY }; });
      const g = s("g");
      const labels = {};
      const nulls = [];
      for (const [name, id] of Object.entries(f.ptrs)) { if (id && pos[id]) (labels[id] ||= []).push(name); else if (name !== "head" || !f.head) nulls.push(name); }
      if (!f.head && !n) g.append(T(30, baseY + 18, "head → None (empty list)", { anchor: "start", fill: V("fg-muted") }));
      for (const id of f.order) {
        const { x, y } = pos[id];
        const nd = f.nodes[id];
        const fill = f.hl[id] || V("viz-node");
        if (doubly) {
          g.append(R(x, y, nw, 36, fill, V("border-strong"), { rx: 4 }), L(x + 18, y, x + 18, y + 36, V("border-strong"), 1), L(x + 58, y, x + 58, y + 36, V("border-strong"), 1));
          g.append(T(x + 38, y + 18, nd.v, { weight: 700 }));
        } else {
          g.append(R(x, y, nw, 36, fill, V("border-strong"), { rx: 4 }), L(x + 44, y, x + 44, y + 36, V("border-strong"), 1));
          g.append(T(x + 22, y + 18, nd.v, { weight: 700 }));
        }
        const nx = x + nw - 11;
        if (!nd.next) g.append(L(nx - 7, y + 29, nx + 7, y + 7, V("fg-faint"), 1.3));
        if (doubly && !nd.prev) g.append(L(x + 2, y + 29, x + 16, y + 7, V("fg-faint"), 1.3));
        (labels[id] || []).forEach((name, k) => {
          const ly = y - 14 - k * 15;
          g.append(T(x + nw / 2, ly, name, { size: 11, weight: 700, fill: PTR_COLOR[name] || V("fg") }));
        });
        if (labels[id]) g.append(arrow(x + nw / 2, y - 7, x + nw / 2, y - 1, V("fg-faint"), { head: 5, sw: 1 }));
      }
      for (const id of f.order) {
        const nd = f.nodes[id];
        const { x, y } = pos[id];
        if (nd.next && pos[nd.next]) {
          const t = pos[nd.next];
          const sx = x + nw - 11;
          const sy = y + (doubly ? 12 : 18);
          if (t.x > x) {
            const adj = t.x - x === step && t.y === y;
            g.append(arrow(sx, sy, t.x, t.y + (doubly ? 12 : 18), V("viz-1"), { bend: adj ? 0 : -24 }));
          } else g.append(arrow(sx, y + 36, t.x + nw - 20, t.y + 36, V("viz-4"), { bend: -34 }));
        }
        if (doubly && nd.prev && pos[nd.prev]) {
          const t = pos[nd.prev];
          if (t.x < x) g.append(arrow(x + 9, y + 26, t.x + nw, t.y + 26, V("viz-5"), { bend: t.x === x - step && t.y === y ? 0 : 20 }));
          else g.append(arrow(x + 9, y + 36, t.x + 30, t.y + 36, V("viz-5"), { bend: 30 }));
        }
      }
      const seq = [];
      let c = f.head;
      for (let k = 0; c && k <= n; k++) { seq.push(f.nodes[c].v); c = f.nodes[c].next; }
      g.append(T(20, 214, `from head: ${seq.join(" → ")}${seq.length ? " → " : ""}None`, { anchor: "start", size: 12, fill: V("fg-muted") }));
      if (nulls.length) g.append(T(20, 236, nulls.map((p) => `${p} = None`).join("   "), { anchor: "start", size: 11, fill: V("fg-faint") }));
      const svg = svgBox(W, 248);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const vIn = field("", 60, "value");
    const iIn = field("1", 40, "index");
    const v = () => { const t = vIn.value.trim() || String(randInt(1, 99)); vIn.value = ""; return t.slice(0, 4); };
    const start = (vals) => { build(vals); setTitle(); F = []; snap(`${doubly ? "Doubly" : "Singly"} linked list. Each node stores a value and a next pointer${doubly ? " plus a prev pointer" : ""}; a slash means None.`, { ptrs: { head: M.head } }); TL.reset(F[0]); };
    onEnter(vIn, () => TL.add(insertAt(M.order.length, v())));
    tb.append(vIn, button("Insert head", () => TL.add(insertAt(0, v()))), button("Insert tail", () => TL.add(insertAt(M.order.length, v())), "btn small primary"), iIn, button("Insert at index", () => TL.add(insertAt(Number(iIn.value) || 0, v()))));
    tb2.append(button("Delete value", () => { const t = vIn.value.trim() || (M.order.length ? val(M.order[randInt(0, M.order.length - 1)]) : "1"); vIn.value = ""; TL.add(remove(t)); }),
      button("Search", () => { const t = vIn.value.trim() || (M.order.length ? val(M.order[randInt(0, M.order.length - 1)]) : "1"); vIn.value = ""; TL.add(search(t)); }),
      button("Reverse", () => TL.add(reverse())),
      button("Random list", () => start(Array.from({ length: randInt(3, 6) }, () => String(randInt(1, 99))))),
      button("Reset", () => start(init)),
      checkbox("doubly linked", doubly, (on) => { doubly = on; start(M.order.map((id) => val(id))); }));
    ui.setLegend([["next pointer", V("viz-1")], ["reversed next", V("viz-4")], ...(doubly ? [["prev pointer", V("viz-5")]] : []), ["comparing / cur", ACT], ["new node", NEW], ["removed", DEL]]);
    start(init);
  });

  /* ---------- stack-queue ---------- */
  registerViz("stack-queue", (el, cfg) => {
    let mode = ["stack", "queue", "deque"].includes(cfg.mode) ? cfg.mode : "stack";
    const init = (Array.isArray(cfg.values) ? cfg.values : [3, 8, 5]).slice(0, 10).map(String);
    const MAXN = 10;
    const ui = shell(el, { title: "", kind: "Stack · Queue · Deque" });
    const tb = toolbar(ui);
    const opsBar = toolbar(ui);
    let items = [];
    const vIn = field("", 60, "value");
    const NAME = { stack: "stack", queue: "q", deque: "d" };
    const repr = (a) => (mode === "stack" ? `[${a.join(", ")}]` : `deque([${a.join(", ")}])`);
    function draw(f) {
      const g = s("g");
      let H;
      const W = 640;
      if (f.mode === "stack") {
        const n = f.items.length;
        H = Math.max(220, 70 + MAXN * 30);
        const base = H - 30;
        g.append(L(210, base, 350, base, V("fg-muted"), 2), L(210, base, 210, base - MAXN * 30 - 6, V("fg-faint"), 1.2), L(350, base, 350, base - MAXN * 30 - 6, V("fg-faint"), 1.2));
        f.items.forEach((v, i) => {
          const y = base - (i + 1) * 30;
          g.append(R(216, y + 2, 128, 26, f.hl[i] || V("viz-node"), V("border-strong"), { rx: 4 }), T(280, y + 15, v, { weight: 700 }), T(200, y + 15, i, { anchor: "end", size: 10, fill: V("fg-faint") }));
        });
        if (n) { const y = base - n * 30 + 15; g.append(arrow(430, y, 352, y, V("accent")), T(436, y, "top  (stack[-1])", { anchor: "start", size: 11, fill: V("accent"), weight: 700 })); }
        g.append(T(280, base + 16, "bottom", { size: 10, fill: V("fg-faint") }));
        g.append(T(436, 30, `stack = ${repr(f.items)}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      } else {
        H = 200;
        const x0 = 40;
        const y = 80;
        f.items.forEach((v, i) => {
          const x = x0 + i * 56;
          g.append(R(x, y, 52, 40, f.hl[i] || V("viz-node"), V("border-strong"), { rx: 4 }), T(x + 26, y + 20, v, { weight: 700 }), T(x + 26, y + 50, i, { size: 9, fill: V("fg-faint") }));
        });
        const n = f.items.length;
        if (n) {
          g.append(T(x0 + 26, y - 26, "front", { size: 11, weight: 700, fill: V("viz-3") }), arrow(x0 + 26, y - 18, x0 + 26, y - 3, V("viz-3"), { head: 6 }));
          g.append(T(x0 + (n - 1) * 56 + 26, y + 76, "back", { size: 11, weight: 700, fill: V("viz-2") }), arrow(x0 + (n - 1) * 56 + 26, y + 66, x0 + (n - 1) * 56 + 26, y + 58, V("viz-2"), { head: 6 }));
        } else g.append(T(x0, y + 20, "(empty)", { anchor: "start", fill: V("fg-faint") }));
        g.append(T(x0, 24, `${NAME[f.mode]} = ${repr(f.items)}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      }
      const svg = svgBox(W, H);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const fr = (log, hl = {}, arr = items) => ({ mode, items: [...arr], hl, log });
    const val = () => { const t = vIn.value.trim() || String(randInt(1, 99)); vIn.value = ""; return t.slice(0, 4); };
    function add(where) {
      if (items.length >= MAXN) return TL.add([fr(`Full for this demo (${MAXN} items). Pop something first.`)]);
      const v = val();
      const call = mode === "stack" ? `stack.append(${v})` : where === "left" ? `d.appendleft(${v})` : `${NAME[mode]}.append(${v})`;
      const why = mode === "stack" ? "push onto the top. Appending at the end of a list is amortized O(1)."
        : where === "left" ? "add at the front. O(1) for a deque; list.insert(0, x) would shift every element (O(n))."
          : "join at the back. O(1).";
      const before = fr(`${call}: ${why}`);
      if (where === "left") items.unshift(v); else items.push(v);
      const idx = where === "left" ? 0 : items.length - 1;
      TL.add([before, fr(`${call} done → ${repr(items)}`, { [idx]: NEW })]);
    }
    function take(where) {
      if (!items.length) return TL.add([fr(`${mode === "stack" ? "stack.pop()" : "popleft()"} on an empty ${mode} raises IndexError.`)]);
      const front = where === "left";
      const idx = front ? 0 : items.length - 1;
      const call = mode === "stack" ? "stack.pop()" : front ? `${NAME[mode]}.popleft()` : `${NAME[mode]}.pop()`;
      const why = mode === "stack" ? "remove from the top: last in, first out (LIFO)."
        : mode === "queue" ? "remove from the front: first in, first out (FIFO). O(1) with collections.deque; list.pop(0) is O(n) because every remaining element shifts left."
          : front ? "remove from the left end in O(1)." : "remove from the right end in O(1).";
      const v = items[idx];
      const F = [fr(`${call}: ${why}`, { [idx]: DEL })];
      items.splice(idx, 1);
      F.push(fr(`${call} returned ${v} → ${repr(items)}`));
      TL.add(F);
    }
    function peek(where) {
      if (!items.length) return TL.add([fr("Nothing to peek at: the container is empty.")]);
      const idx = where === "left" ? 0 : items.length - 1;
      TL.add([fr(`${mode === "stack" ? "stack[-1]" : where === "left" ? `${NAME[mode]}[0]` : `${NAME[mode]}[-1]`} = ${items[idx]}: look without removing.`, { [idx]: ACT })]);
    }
    function buildOps() {
      ui.head.querySelector(".w-title").textContent = { stack: "Stack (LIFO) with a list", queue: "Queue (FIFO) with collections.deque", deque: "Double-ended queue (collections.deque)" }[mode];
      const ops = mode === "stack" ? [["Push", () => add("right"), true], ["Pop", () => take("right")], ["Peek", () => peek("right")]]
        : mode === "queue" ? [["Enqueue", () => add("right"), true], ["Dequeue", () => take("left")], ["Peek front", () => peek("left")]]
          : [["append", () => add("right"), true], ["appendleft", () => add("left")], ["pop", () => take("right")], ["popleft", () => take("left")]];
      opsBar.replaceChildren(vIn, ...ops.map(([t, fn, p]) => button(t, fn, p ? "btn small primary" : "btn small")));
    }
    onEnter(vIn, () => add("right"));
    const start = () => { items = [...init]; buildOps(); TL.reset(fr(mode === "stack" ? "A Python list works as a stack: push with append, pop with pop(), both O(1) at the end." : mode === "queue" ? "from collections import deque: a queue adds at the back and removes from the front." : "A deque supports O(1) appends and pops at both ends.")); };
    tb.append(label("mode", select([["stack", "stack"], ["queue", "queue"], ["deque", "deque"]], mode, (m) => { mode = m; start(); })),
      button("Random fill", () => { items = Array.from({ length: randInt(3, 7) }, () => String(randInt(1, 99))); TL.add([fr(`Filled with random values → ${repr(items)}`)]); }),
      button("Reset", start));
    ui.setLegend([["added", NEW], ["removed", DEL], ["peeked", ACT]]);
    start();
  });

  /* ---------- hash-table ---------- */
  registerViz("hash-table", (el, cfg) => {
    const pow2 = (n) => 2 ** Math.round(Math.log2(Math.max(4, Math.min(32, n))));
    const size0 = pow2(Number(cfg.size) || 8);
    let strategy = ["chaining", "linear", "python"].includes(cfg.strategy) ? cfg.strategy : "python";
    const MAXSIZE = 64;
    const DUMMY = "<dummy>";
    const ui = shell(el, { title: "", kind: "Hash table" });
    const tb = toolbar(ui);
    let M;
    let F = [];
    const hashOf = (k) => (typeof k === "number" ? (k === -1 ? -2 : k) : fnv1a(k));
    const limit = (size) => (strategy === "chaining" ? Math.floor(size * 0.75) : Math.floor((2 * size) / 3));
    const fresh = (size) => ({ size, slots: Array(size).fill(null), chains: Array.from({ length: size }, () => []), count: 0, fill: 0 });
    const snap = (log, x = {}) => F.push({ ...deep(M), strategy, cur: x.cur ?? null, probe: x.probe || [], done: x.done ?? null, bad: x.bad ?? null, info: x.info || [], chainHl: x.chainHl || null, log });
    const disp = (e) => (e.v != null ? `${showKey(e.k)}: ${e.v}` : showKey(e.k));
    function* probes(hv, size) {
      const mask = size - 1;
      let i = hv & mask;
      yield [i, `index = hash % ${size} = ${i}`];
      if (strategy === "linear") { for (;;) { i = (i + 1) & mask; yield [i, `linear probing: i = (i + 1) % ${size} = ${i}`]; } }
      let perturb = hv >>> 0;
      for (;;) {
        perturb = Math.floor(perturb / 32);
        const ni = (5 * i + 1 + perturb) & mask;
        const txt = `perturb >>= 5 → ${perturb}; i = (5·${i} + 1 + perturb) % ${size} = ${ni}`;
        i = ni;
        yield [i, txt];
      }
    }
    function quietInsert(k, v) {
      const hv = hashOf(k);
      if (strategy === "chaining") { M.chains[hv & (M.size - 1)].push({ k, v, h: hv }); M.count++; return; }
      const it = probes(hv, M.size);
      for (let n = 0; n < 4 * M.size; n++) { const [i] = it.next().value; if (M.slots[i] === null) { M.slots[i] = { k, v, h: hv }; M.count++; M.fill++; return; } }
    }
    function resize() {
      const entries = strategy === "chaining" ? M.chains.flat() : M.slots.filter((e) => e && e !== DUMMY);
      const ns = M.size * 2;
      snap(`Load would exceed ${strategy === "chaining" ? "0.75" : "2/3"}: ${M[strategy === "chaining" ? "count" : "fill"] + 1}/${M.size} > ${limit(M.size)}/${M.size}. Resize to ${ns} slots and re-insert every key. Indices change because index = hash % size.${strategy === "python" ? " (CPython sizes the new table from the number of live keys; this demo simply doubles.)" : ""}`, { info: [`resizing ${M.size} → ${ns}`] });
      M = fresh(ns);
      entries.forEach((e) => quietInsert(e.k, e.v));
      snap(`Rehashed ${entries.length} key${entries.length === 1 ? "" : "s"} into ${ns} slots.${strategy !== "chaining" ? " Dummy markers are dropped during a resize." : ""}`, { info: [`size = ${ns}, load = ${(M.count / ns).toFixed(2)}`] });
    }
    function find(k) {
      const hv = hashOf(k);
      if (strategy === "chaining") { const b = hv & (M.size - 1); const j = M.chains[b].findIndex((e) => e.k === k); return j >= 0; }
      const it = probes(hv, M.size);
      for (let n = 0; n < 4 * M.size; n++) { const [i] = it.next().value; const e = M.slots[i]; if (e === null) return false; if (e !== DUMMY && e.k === k) return true; }
      return false;
    }
    function op(kind, k, v) {
      F = [];
      const hv = hashOf(k);
      const hinfo = `hash(${showKey(k)}) = ${hv}${typeof k === "number" ? "  (small ints hash to themselves)" : "  (toy hash; real str hashes are randomized per process)"}`;
      if (kind === "insert" && !find(k) && (strategy === "chaining" ? M.count : M.fill) + 1 > limit(M.size) && M.size < MAXSIZE) resize();
      if (strategy === "chaining") {
        const b = hv & (M.size - 1);
        const chain = M.chains[b];
        const info = [hinfo, `bucket = hash % ${M.size} = ${b}`, `load = ${M.count}/${M.size}`];
        snap(`${kind}(${showKey(k)}): compute the hash, then the bucket index ${hv} % ${M.size} = ${b}. Chain length here: ${chain.length}.`, { cur: b, info });
        for (let j = 0; j < chain.length; j++) {
          if (chain[j].k === k) {
            if (kind === "insert") { chain[j].v = v; snap(`Same key found in the chain → replace its value with ${v}.`, { cur: b, chainHl: [b, j, DONE], info }); }
            else if (kind === "lookup") snap(`Found ${disp(chain[j])} after ${j + 1} comparison${j ? "s" : ""} in bucket ${b}.`, { cur: b, chainHl: [b, j, DONE], info });
            else { snap(`Found ${showKey(k)} in bucket ${b} → unlink it from the chain.`, { cur: b, chainHl: [b, j, DEL], info }); chain.splice(j, 1); M.count--; snap(`Deleted. load = ${M.count}/${M.size}.`, { cur: b, info }); }
            return F;
          }
          snap(`Chain entry ${showKey(chain[j].k)} != ${showKey(k)} → collision, keep walking the chain.`, { cur: b, chainHl: [b, j, ACT], info });
        }
        if (kind === "insert") { chain.push({ k, v, h: hv }); M.count++; snap(`End of chain: append ${showKey(k)} to bucket ${b}. load = ${M.count}/${M.size} = ${(M.count / M.size).toFixed(2)}.`, { cur: b, chainHl: [b, chain.length - 1, NEW], info: [hinfo, `bucket = ${b}`, `load = ${M.count}/${M.size}`] }); }
        else snap(`Reached the end of bucket ${b}'s chain: ${showKey(k)} is not present${kind === "lookup" ? " (d[key] would raise KeyError)" : ""}.`, { cur: b, info });
        return F;
      }
      const it = probes(hv, M.size);
      const seq = [];
      let firstDummy = null;
      for (let n = 0; n < 4 * M.size; n++) {
        const [i, how] = it.next().value;
        seq.push(i);
        const info = [hinfo, how, `probe sequence: ${seq.join(" → ")}`, `used ${M.count}, dummies ${M.fill - M.count}, size ${M.size} (resize above ${limit(M.size)})`];
        const e = M.slots[i];
        const base = { cur: i, probe: [...seq], info };
        if (e === null) {
          if (kind === "insert") {
            const at = firstDummy ?? i;
            if (firstDummy === null) M.fill++;
            M.slots[at] = { k, v, h: hv };
            M.count++;
            snap(`Slot ${i} is empty → ${firstDummy !== null ? `the key is new, so reuse the first dummy slot ${at}` : `store ${showKey(k)} here`} after ${seq.length} probe${seq.length > 1 ? "s" : ""}.`, { ...base, done: at });
          } else snap(`Slot ${i} is empty → ${showKey(k)} is not in the table${kind === "lookup" ? " (d[key] would raise KeyError)" : ""}. An empty slot ends every probe sequence.`, { ...base, bad: i });
          return F;
        }
        if (e === DUMMY) {
          if (kind === "insert" && firstDummy === null) firstDummy = i;
          snap(`Slot ${i} holds a dummy (a deleted entry). Keep probing: the key might live further along this sequence.`, base);
        } else if (e.k === k) {
          if (kind === "insert") { e.v = v; snap(`Slot ${i} holds the same key → replace its value.`, { ...base, done: i }); }
          else if (kind === "lookup") snap(`Slot ${i} holds ${disp(e)}: hashes match and keys compare equal → found after ${seq.length} probe${seq.length > 1 ? "s" : ""}.`, { ...base, done: i });
          else {
            snap(`Found ${showKey(k)} in slot ${i}.`, { ...base, done: i });
            M.slots[i] = DUMMY;
            M.count--;
            snap(`Replace it with a dummy marker instead of emptying the slot: an empty slot would cut the probe chain and hide keys stored after it.`, { ...base, bad: i });
          }
          return F;
        } else snap(`Slot ${i} holds ${showKey(e.k)} (a different key) → collision. Compute the next probe.`, base);
      }
      snap("Probe limit reached (table too full).");
      return F;
    }
    function draw(f) {
      const g = s("g");
      const W = 640;
      let y = 6;
      f.info.forEach((line) => { g.append(T(16, y + 8, line, { anchor: "start", size: 11, fill: V("fg-muted") })); y += 17; });
      if (!f.info.length) { g.append(T(16, y + 8, `${f.count} key${f.count === 1 ? "" : "s"} in ${f.size} ${f.strategy === "chaining" ? "buckets" : "slots"}, load factor ${(f.count / f.size).toFixed(2)}`, { anchor: "start", size: 11, fill: V("fg-muted") })); y += 17; }
      y += 8;
      if (f.strategy === "chaining") {
        for (let b = 0; b < f.size; b++) {
          const yy = y + b * 32;
          g.append(R(16, yy, 40, 26, b === f.cur ? ACT : V("bg-sunk"), V("border-strong"), { rx: 3 }), T(36, yy + 13, b, { size: 11 }));
          let x = 76;
          f.chains[b].forEach((e, j) => {
            const w = Math.max(64, disp(e).length * 7.6 + 16);
            const hl = f.chainHl && f.chainHl[0] === b && f.chainHl[1] === j ? f.chainHl[2] : V("viz-node");
            g.append(arrow(x - 20, yy + 13, x - 2, yy + 13, V("viz-edge"), { head: 5 }), R(x, yy, w, 26, hl, V("border-strong"), { rx: 4 }), T(x + w / 2, yy + 13, disp(e), { size: 11 }));
            x += w + 22;
          });
          if (!f.chains[b].length) g.append(T(66, yy + 13, "—", { anchor: "start", size: 11, fill: V("fg-faint") }));
        }
        y += f.size * 32;
      } else {
        const per = 8;
        const cw = 74;
        for (let i = 0; i < f.size; i++) {
          const x = 16 + (i % per) * (cw + 3);
          const yy = y + Math.floor(i / per) * 62;
          const e = f.slots[i];
          const order = f.probe.indexOf(i);
          let fill = e ? V("viz-node") : V("bg-sunk");
          if (order >= 0) fill = SOFT(2);
          if (i === f.cur) fill = ACT;
          if (i === f.done) fill = DONE;
          if (i === f.bad) fill = DEL;
          g.append(T(x + cw / 2, yy + 7, i, { size: 9, fill: V("fg-faint") }));
          g.append(R(x, yy + 14, cw, 40, fill, V("border-strong"), { rx: 4, dash: e ? null : "3 3" }));
          if (e === DUMMY) g.append(T(x + cw / 2, yy + 34, DUMMY, { size: 10, fill: V("fg-faint") }));
          else if (e) {
            g.append(T(x + cw / 2, yy + 28, showKey(e.k).slice(0, 9), { size: 11.5, weight: 700 }));
            g.append(T(x + cw / 2, yy + 44, e.v != null ? `→ ${String(e.v).slice(0, 7)}` : `h…${String(e.h).slice(-4)}`, { size: 9, fill: V("fg-muted") }));
          }
          if (order >= 0) { g.append(Ci(x + cw - 6, yy + 16, 7, V("viz-2"), V("bg-elev"), 1), T(x + cw - 6, yy + 16, order + 1, { size: 8.5, fill: V("bg-elev"), weight: 700 })); }
        }
        y += Math.ceil(f.size / per) * 62;
      }
      const svg = svgBox(W, y + 8);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const kIn = field("", 110, "key or key=value");
    const read = () => {
      let t = kIn.value.trim();
      kIn.value = "";
      if (!t) t = Math.random() < 0.7 ? WORDS[randInt(0, WORDS.length - 1)] : String(randInt(0, 99));
      const [a, b] = t.split("=");
      return [parseKey(a.trim().slice(0, 10)), b != null && b.trim() ? b.trim().slice(0, 8) : null];
    };
    const setTitle = () => { ui.head.querySelector(".w-title").textContent = { python: "Open addressing with perturbation (like CPython dict)", linear: "Open addressing with linear probing", chaining: "Separate chaining" }[strategy]; };
    const start = () => {
      M = fresh(size0);
      ["apple", "banana", "cherry"].forEach((k) => quietInsert(k, null));
      setTitle();
      F = [];
      snap(strategy === "python" ? "CPython dicts use open addressing: on a collision the next slot comes from i = (5*i + 1 + perturb) % size, with perturb starting at the hash and shifted right 5 bits each probe, so all hash bits eventually matter. The table resizes before it gets 2/3 full. (Real dicts also keep a compact entries array in insertion order; this view shows the index table.)"
        : strategy === "linear" ? "Linear probing: on a collision try the next slot, i + 1. Simple and cache-friendly, but keys pile up into clusters."
          : "Separate chaining: each bucket holds a list of entries; collisions just extend the chain. Resize when load factor exceeds 0.75.");
      TL.reset(F[0]);
    };
    onEnter(kIn, () => { const [k, v] = read(); TL.add(op("insert", k, v)); });
    tb.append(kIn, button("Insert", () => { const [k, v] = read(); TL.add(op("insert", k, v)); }, "btn small primary"),
      button("Lookup", () => { const [k] = read(); TL.add(op("lookup", k)); }),
      button("Delete", () => { const [k] = read(); TL.add(op("delete", k)); }),
      button("Insert ×4 random", () => { const all = []; for (let i = 0; i < 4; i++) all.push(...op("insert", WORDS[randInt(0, WORDS.length - 1)], null)); TL.add(all); }),
      label("strategy", select([["python", "python (perturb)"], ["linear", "linear"], ["chaining", "chaining"]], strategy, (v) => { strategy = v; start(); })),
      button("Reset", start));
    ui.setLegend([["current probe", ACT], ["probed earlier", SOFT(2)], ["stored / found", DONE], ["missing / deleted", DEL]]);
    start();
  });

  /* ---------- binary tree drawing shared by bst and heap ---------- */
  function drawBinTree(g, root, top, { label, fill, badge, W = 640, r = 17 }) {
    if (!root) { g.append(T(W / 2, top + 24, "(empty tree)", { fill: V("fg-faint") })); return 56; }
    const { pos, width, depth } = layoutBinaryTree(root);
    const dx = Math.min(56, (W - 40) / Math.max(1, width));
    const X = (p) => W / 2 + (p.x - (width - 1) / 2) * dx;
    const Y = (p) => top + r + 4 + p.y * 62;
    for (const [n, p] of pos) for (const c of [n.left, n.right]) if (c) g.append(L(X(p), Y(p), X(pos.get(c)), Y(pos.get(c)), V("viz-edge"), 1.6));
    for (const [n, p] of pos) {
      g.append(Ci(X(p), Y(p), r, fill(n) || V("viz-node"), V("border-strong"), 1.5), T(X(p), Y(p), label(n), { size: 12, weight: 700 }));
      const b = badge && badge(n);
      if (b) g.append(T(X(p) + r + 2, Y(p) - r + 2, b.text, { anchor: "start", size: 9.5, fill: b.color, weight: 700 }));
    }
    return depth * 62 + 10;
  }
  const heightOf = (n) => (n ? 1 + Math.max(heightOf(n.left), heightOf(n.right)) : 0);

  /* ---------- bst ---------- */
  registerViz("bst", (el, cfg) => {
    let avl = !!cfg.avl;
    const init = (Array.isArray(cfg.values) ? cfg.values : [50, 30, 70, 20, 40, 60, 80]).map(Number).filter(Number.isFinite).slice(0, 25);
    const MAXN = 25;
    const ui = shell(el, { title: "", kind: "Binary search tree" });
    const tb = toolbar(ui);
    const tb2 = toolbar(ui);
    let root = null;
    let nid = 0;
    let F = [];
    const node = (key) => ({ id: nid++, key, left: null, right: null });
    const clone = (n) => (n ? { id: n.id, key: n.key, left: clone(n.left), right: clone(n.right) } : null);
    const bf = (n) => heightOf(n.left) - heightOf(n.right);
    const count = (n) => (n ? 1 + count(n.left) + count(n.right) : 0);
    const snap = (log, hl = {}, out = null) => F.push({ tree: clone(root), hl, out, avl, log });
    const rotR = (y) => { const x = y.left; y.left = x.right; x.right = y; return x; };
    const rotL = (x) => { const y = x.right; x.right = y.left; y.left = x; return y; };
    function attach(parent, oldN, newN) { if (!parent) root = newN; else if (parent.left === oldN) parent.left = newN; else parent.right = newN; }
    function rebalance(path) {
      let rotated = false;
      for (let i = path.length - 1; i >= 0; i--) {
        const n = path[i];
        const b = bf(n);
        if (Math.abs(b) <= 1) continue;
        rotated = true;
        const parent = path[i - 1] || null;
        let top;
        if (b > 1) {
          const c = bf(n.left);
          if (c >= 0) { snap(`AVL: node ${n.key} has balance factor +${b} (left-heavy) and its left child ${n.left.key} leans left or is even (${c}) → LL case: one right rotation at ${n.key}.`, { [n.id]: DEL, [n.left.id]: ACT }); top = rotR(n); }
          else {
            snap(`AVL: node ${n.key} has balance +${b} but its left child ${n.left.key} leans right (${c}) → LR case: rotate left at ${n.left.key}, then right at ${n.key}.`, { [n.id]: DEL, [n.left.id]: ACT });
            n.left = rotL(n.left);
            snap(`After the left rotation at the child, the shape is a straight LL line: ${n.key} → ${n.left.key} → ${n.left.left.key}.`, { [n.id]: DEL, [n.left.id]: ACT });
            top = rotR(n);
          }
        } else {
          const c = bf(n.right);
          if (c <= 0) { snap(`AVL: node ${n.key} has balance factor ${b} (right-heavy) and its right child ${n.right.key} leans right or is even (${c}) → RR case: one left rotation at ${n.key}.`, { [n.id]: DEL, [n.right.id]: ACT }); top = rotL(n); }
          else {
            snap(`AVL: node ${n.key} has balance ${b} but its right child ${n.right.key} leans left (+${c}) → RL case: rotate right at ${n.right.key}, then left at ${n.key}.`, { [n.id]: DEL, [n.right.id]: ACT });
            n.right = rotR(n.right);
            snap(`After the right rotation at the child, the shape is a straight RR line: ${n.key} → ${n.right.key} → ${n.right.right.key}.`, { [n.id]: DEL, [n.right.id]: ACT });
            top = rotL(n);
          }
        }
        attach(parent, n, top);
        snap(`Rotation done: ${top.key} is now this subtree's root. In-order (sorted) order is unchanged, and the subtree's height dropped by one.`, { [top.id]: DONE });
      }
      if (!rotated) snap("AVL: walking back up, every balance factor is between -1 and +1 → no rotation needed.");
    }
    function insert(key, quiet = false) {
      F = [];
      if (count(root) >= MAXN) { snap(`The demo holds at most ${MAXN} keys.`); return F; }
      if (!root) { root = node(key); snap(`The tree is empty → ${key} becomes the root.`, { [root.id]: NEW }); return F; }
      const path = [];
      let cur = root;
      for (;;) {
        path.push(cur);
        if (key === cur.key) { snap(`${key} == ${cur.key}: already present. This tree keeps keys unique, so nothing changes.`, { [cur.id]: ACT }); return F; }
        const dir = key < cur.key ? "left" : "right";
        snap(`Compare ${key} with ${cur.key}: ${key} ${dir === "left" ? "<" : ">"} ${cur.key} → go ${dir}.`, { [cur.id]: ACT });
        if (!cur[dir]) { cur[dir] = node(key); snap(`The ${dir} child of ${cur.key} is empty → place ${key} there. Cost: ${path.length} comparison${path.length > 1 ? "s" : ""}, i.e. the tree's height.`, { [cur[dir].id]: NEW }); break; }
        cur = cur[dir];
      }
      if (avl) rebalance(path);
      if (quiet) F = [];
      return F;
    }
    function remove(key) {
      F = [];
      const path = [];
      let cur = root;
      while (cur && cur.key !== key) {
        path.push(cur);
        const dir = key < cur.key ? "left" : "right";
        snap(`Delete ${key}: ${key} ${dir === "left" ? "<" : ">"} ${cur.key} → go ${dir}.`, { [cur.id]: ACT });
        cur = cur[dir];
      }
      if (!cur) { snap(`Reached an empty spot: ${key} is not in the tree.`); return F; }
      const parent = path[path.length - 1] || null;
      if (!cur.left && !cur.right) {
        snap(`Found ${key}. Case 1: it is a leaf → simply detach it from its parent.`, { [cur.id]: DEL });
        attach(parent, cur, null);
        snap(`${key} removed.`);
      } else if (!cur.left || !cur.right) {
        const child = cur.left || cur.right;
        snap(`Found ${key}. Case 2: it has exactly one child (${child.key}) → splice it out; ${parent ? `its parent ${parent.key}` : "the root pointer"} adopts ${child.key}.`, { [cur.id]: DEL, [child.id]: ACT });
        attach(parent, cur, child);
        snap(`${key} removed; ${child.key}'s whole subtree moved up one level and stays in order.`, { [child.id]: DONE });
      } else {
        snap(`Found ${key}. Case 3: it has two children → replace it with its in-order successor, the smallest key in its right subtree.`, { [cur.id]: DEL });
        path.push(cur);
        let sp = cur;
        let sc = cur.right;
        snap(`Step into the right subtree: ${sc.key}.`, { [cur.id]: DEL, [sc.id]: ACT });
        while (sc.left) { path.push(sc); sp = sc; sc = sc.left; snap(`${sp.key} has a left child → go left to ${sc.key}.`, { [cur.id]: DEL, [sc.id]: ACT }); }
        snap(`${sc.key} has no left child, so it is the successor. Copy ${sc.key} into the node that held ${key}.`, { [cur.id]: DEL, [sc.id]: ACT });
        cur.key = sc.key;
        snap(`Now remove the old ${sc.key} node. It has no left child, so this is case 1 or 2.`, { [cur.id]: DONE, [sc.id]: DEL });
        if (sp.left === sc) sp.left = sc.right; else sp.right = sc.right;
        snap(`Done: ${key} deleted and every left < node < right relationship still holds.`, { [cur.id]: DONE });
      }
      if (avl) rebalance(path);
      return F;
    }
    function search(key) {
      F = [];
      let cur = root;
      let steps = 0;
      while (cur) {
        steps++;
        if (cur.key === key) { snap(`${key} == ${cur.key} → found after ${steps} comparison${steps > 1 ? "s" : ""}. Search costs O(height): O(log n) when balanced, O(n) for a degenerate chain.`, { [cur.id]: DONE }); return F; }
        const dir = key < cur.key ? "left" : "right";
        snap(`${key} ${dir === "left" ? "<" : ">"} ${cur.key} → go ${dir}; the whole ${dir === "left" ? "right" : "left"} subtree is ruled out.`, { [cur.id]: ACT });
        cur = cur[dir];
      }
      snap(`Fell off the tree after ${steps} comparison${steps === 1 ? "" : "s"} → ${key} is not present.`);
      return F;
    }
    function traverse(kind) {
      F = [];
      const out = [];
      const seen = {};
      const visit = (n, why) => { out.push(n.key); seen[n.id] = DONE; snap(`Visit ${n.key}. ${why}`, { ...seen, [n.id]: ACT }, [...out]); };
      const rec = (n) => {
        if (!n) return;
        if (kind === "pre") visit(n, "Pre-order: node first, then left subtree, then right. Useful for copying a tree.");
        rec(n.left);
        if (kind === "in") visit(n, "In-order: left subtree, node, right subtree. On a BST this yields the keys in sorted order.");
        rec(n.right);
        if (kind === "post") visit(n, "Post-order: both subtrees before the node. Useful for deleting or evaluating a tree bottom-up.");
      };
      if (!root) { snap("The tree is empty."); return F; }
      if (kind === "level") {
        const q = [root];
        snap(`Level-order (BFS) uses a queue: start with [${root.key}].`, {}, []);
        while (q.length) {
          const n = q.shift();
          if (n.left) q.push(n.left);
          if (n.right) q.push(n.right);
          out.push(n.key);
          seen[n.id] = DONE;
          snap(`Dequeue ${n.key} and visit it; enqueue its children → queue [${q.map((x) => x.key).join(", ")}].`, { ...seen, [n.id]: ACT }, [...out]);
        }
      } else rec(root);
      snap(`${{ in: "In-order", pre: "Pre-order", post: "Post-order", level: "Level-order" }[kind]} result: ${out.join(", ")}.`, seen, out);
      return F;
    }
    function draw(f) {
      const W = 640;
      const g = s("g");
      g.append(T(14, 12, `${count(f.tree)} keys, height ${heightOf(f.tree)}${f.avl ? " · AVL mode (numbers show balance factor = height(left) - height(right))" : ""}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      let y = 26 + drawBinTree(g, f.tree, 26, {
        W, label: (n) => n.key, fill: (n) => f.hl[n.id],
        badge: f.avl ? (n) => { const b = bf(n); return { text: b > 0 ? `+${b}` : String(b), color: Math.abs(b) > 1 ? V("bad") : V("fg-faint") }; } : null,
      });
      if (f.out) { g.append(T(14, y + 10, `output: ${f.out.join(" ")}`, { anchor: "start", size: 12, weight: 700, fill: V("viz-3") })); y += 26; }
      const svg = svgBox(W, y + 6);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const vIn = field("", 60, "number");
    const num = () => { const t = vIn.value.trim(); vIn.value = ""; const x = Number(t); return t && Number.isFinite(x) ? Math.round(x) : null; };
    const anyKey = () => { const ks = []; (function w(n) { if (n) { ks.push(n.key); w(n.left); w(n.right); } })(root); return ks.length ? ks[randInt(0, ks.length - 1)] : randInt(1, 99); };
    const build = (vals) => { root = null; vals.forEach((v) => insert(v, true)); };
    const setTitle = () => { ui.head.querySelector(".w-title").textContent = avl ? "AVL tree (self-balancing BST)" : "Binary search tree"; };
    const start = (vals = init) => { build(vals); setTitle(); F = []; snap(avl ? "AVL mode: after each insert or delete, nodes on the path back to the root are checked; any balance factor outside -1..+1 triggers rotations." : "BST rule: every key in a node's left subtree is smaller and every key in its right subtree is larger."); TL.reset(F[0]); };
    let trav = "in";
    onEnter(vIn, () => { const k = num(); TL.add(insert(k ?? randInt(1, 99))); });
    tb.append(vIn, button("Insert", () => { const k = num(); TL.add(insert(k ?? randInt(1, 99))); }, "btn small primary"),
      button("Delete", () => { const k = num(); TL.add(remove(k ?? anyKey())); }),
      button("Search", () => { const k = num(); TL.add(search(k ?? anyKey())); }),
      label("traversal", select([["in", "in-order"], ["pre", "pre-order"], ["post", "post-order"], ["level", "level-order"]], trav, (v) => { trav = v; })),
      button("Traverse", () => TL.add(traverse(trav))));
    tb2.append(button("Random tree", () => start(shuffle(Array.from({ length: 30 }, (_, i) => (i + 1) * 3)).slice(0, randInt(6, 11)))),
      button("Sorted inserts 1..7", () => start([1, 2, 3, 4, 5, 6, 7])),
      checkbox("AVL balancing", avl, (on) => { avl = on; start(); }),
      button("Reset", () => start()));
    ui.setLegend([["comparing", ACT], ["inserted", NEW], ["deleting / unbalanced", DEL], ["found / visited", DONE]]);
    start();
  });

  /* ---------- heap ---------- */
  registerViz("heap", (el, cfg) => {
    let kind = cfg.kind === "max" ? "max" : "min";
    const init = (Array.isArray(cfg.values) ? cfg.values : [5, 9, 3, 7, 1, 8, 2]).map(Number).filter(Number.isFinite).slice(0, 15);
    const MAXN = 15;
    const ui = shell(el, { title: "", kind: "Binary heap" });
    const tb = toolbar(ui);
    let A = [];
    let F = [];
    const better = (a, b) => (kind === "min" ? a < b : a > b);
    const sym = () => (kind === "min" ? "<" : ">");
    const nsym = () => (kind === "min" ? "≥" : "≤");
    const fn = (name) => (kind === "min" ? `heapq.${name}` : `heapq.${name}_max`);
    const snap = (log, hl = {}, popped = null) => F.push({ A: [...A], hl, kind, popped, log });
    function siftDown(i) {
      const n = A.length;
      for (;;) {
        const l = 2 * i + 1;
        const r = l + 1;
        if (l >= n) { snap(`${A[i]} at index ${i} has no children (2·${i}+1 = ${l} ≥ ${n}) → stop.`, { [i]: DONE }); return; }
        const c = r < n && better(A[r], A[l]) ? r : l;
        snap(`Children of ${A[i]} (index ${i}) are at ${l}${r < n ? ` and ${r}` : ""}: ${A[l]}${r < n ? `, ${A[r]}` : ""}. The ${kind === "min" ? "smaller" : "larger"} one is ${A[c]}.`, { [i]: ACT, [c]: SOFT(2) });
        if (better(A[c], A[i])) {
          snap(`${A[c]} ${sym()} ${A[i]} → swap them (sift down).`, { [i]: ACT, [c]: ACT });
          [A[i], A[c]] = [A[c], A[i]];
          i = c;
        } else { snap(`${A[i]} ${kind === "min" ? "≤" : "≥"} ${A[c]} → heap property holds here, stop.`, { [i]: DONE }); return; }
      }
    }
    function push(v) {
      F = [];
      if (A.length >= MAXN) { snap(`The demo holds at most ${MAXN} items.`); return F; }
      A.push(v);
      let i = A.length - 1;
      snap(`${fn("heappush")}(h, ${v}): append at index ${i}, the next free leaf, so the tree stays complete.`, { [i]: NEW });
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (better(A[i], A[p])) {
          snap(`Compare ${A[i]} with its parent ${A[p]} (index (${i}-1)//2 = ${p}): ${A[i]} ${sym()} ${A[p]} → swap (sift up).`, { [i]: ACT, [p]: ACT });
          [A[i], A[p]] = [A[p], A[i]];
          i = p;
        } else { snap(`Compare ${A[i]} with its parent ${A[p]}: ${A[i]} ${nsym()} ${A[p]} → stop. At most log₂(n) swaps: O(log n).`, { [i]: DONE, [p]: SOFT(2) }); return F; }
      }
      snap(`${A[0]} reached the root: it is the new ${kind === "min" ? "minimum" : "maximum"}.`, { 0: DONE });
      return F;
    }
    function pop() {
      F = [];
      if (!A.length) { snap(`${fn("heappop")} on an empty heap raises IndexError.`); return F; }
      const top = A[0];
      snap(`${fn("heappop")}(h): the ${kind === "min" ? "smallest" : "largest"} item is always at index 0 → remove ${top}.`, { 0: DEL });
      const last = A.pop();
      if (!A.length) { snap(`Returned ${top}; the heap is now empty.`, {}, top); return F; }
      A[0] = last;
      snap(`Move the last leaf ${last} into the root to keep the tree complete, then sift it down. Returned ${top}.`, { 0: ACT }, top);
      siftDown(0);
      return F;
    }
    function heapify(list) {
      F = [];
      A = list.slice(0, MAXN);
      const n = A.length;
      snap(`${fn("heapify")}(h) on [${A.join(", ")}]: sift down every non-leaf from index ${Math.max(0, (n >> 1) - 1)} back to 0. Total work is O(n), cheaper than n pushes (O(n log n)).${kind === "max" ? " heapify_max and friends are new in Python 3.14; earlier code pushed negated values." : ""}`);
      for (let i = (n >> 1) - 1; i >= 0; i--) { snap(`Sift down index ${i} (${A[i]}).`, { [i]: ACT }); siftDown(i); }
      snap(`Heap built: every parent is ${kind === "min" ? "≤" : "≥"} its children. (CPython's heapq sifts with a slightly different strategy, so equal-priority layouts can differ.)`);
      return F;
    }
    function draw(f) {
      const W = 640;
      const g = s("g");
      const nodes = f.A.map((v, i) => ({ i, v, left: null, right: null }));
      nodes.forEach((n, i) => { n.left = nodes[2 * i + 1] || null; n.right = nodes[2 * i + 2] || null; });
      g.append(T(14, 12, `${f.kind}-heap · children of i are 2i+1 and 2i+2 · parent is (i-1)//2${f.popped != null ? ` · last popped: ${f.popped}` : ""}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      let y = 26 + drawBinTree(g, nodes[0] || null, 26, { W, label: (n) => n.v, fill: (n) => f.hl[n.i], badge: (n) => ({ text: n.i, color: V("fg-faint") }) });
      const n = f.A.length;
      const cw = Math.min(38, (W - 40) / Math.max(1, n));
      const x0 = W / 2 - (n * cw) / 2;
      g.append(T(x0 - 8, y + 14, "array", { anchor: "end", size: 10, fill: V("fg-muted") }));
      f.A.forEach((v, i) => {
        g.append(R(x0 + i * cw, y, cw - 2, 28, f.hl[i] || V("viz-node"), V("border-strong"), { rx: 3 }), T(x0 + i * cw + cw / 2 - 1, y + 14, v, { size: 11.5, weight: 700 }), T(x0 + i * cw + cw / 2 - 1, y + 38, i, { size: 9, fill: V("fg-faint") }));
      });
      y += 50;
      const svg = svgBox(W, y);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const vIn = field("", 110, "value or list");
    const setTitle = () => { ui.head.querySelector(".w-title").textContent = kind === "min" ? "Min-heap (heapq)" : "Max-heap (heapq *_max functions, Python 3.14)"; };
    const start = () => { setTitle(); F = []; A = []; heapify(init); A = F.length ? F[F.length - 1].A : []; F = []; snap(kind === "min" ? "A min-heap keeps the smallest item at index 0. heapq stores the tree in a plain list." : "A max-heap keeps the largest item at index 0. Python 3.14 adds heapq.heappush_max, heappop_max and heapify_max."); TL.reset(F[0]); };
    const pushVals = () => { const vals = parseList(vIn.value); vIn.value = ""; const all = []; (vals.length ? vals : [randInt(1, 99)]).forEach((v) => all.push(...push(v))); TL.add(all); };
    onEnter(vIn, pushVals);
    tb.append(vIn, button("Push", pushVals, "btn small primary"), button("Pop", () => TL.add(pop())),
      button("Heapify", () => { const vals = parseList(vIn.value); vIn.value = ""; TL.add(heapify(vals.length ? vals : Array.from({ length: randInt(7, 12) }, () => randInt(1, 99)))); }),
      label("kind", select([["min", "min"], ["max", "max"]], kind, (v) => { kind = v; start(); })),
      button("Reset", start));
    ui.setLegend([["comparing / moving", ACT], ["candidate child", SOFT(2)], ["new leaf", NEW], ["removed root", DEL], ["settled", DONE]]);
    start();
  });

  /* ---------- trie ---------- */
  registerViz("trie", (el, cfg) => {
    const init = (Array.isArray(cfg.words) ? cfg.words : ["car", "cart", "cat", "do", "dog"]).map((w) => String(w).toLowerCase().replace(/[^a-z]/g, "").slice(0, 10)).filter(Boolean);
    const ui = shell(el, { title: "Trie (prefix tree)", kind: "Trie" });
    const tb = toolbar(ui);
    let root;
    let nid = 0;
    let F = [];
    const mk = (ch) => ({ id: nid++, ch, end: false, c: {} });
    const kids = (n) => Object.keys(n.c).sort().map((k) => n.c[k]);
    const snap = (log, hl = {}, found = null) => F.push({ root: deep(root), hl, found, log });
    const nodeCount = (n) => 1 + kids(n).reduce((a, k) => a + nodeCount(k), 0);
    function insert(w, quiet) {
      F = [];
      if (!w) { snap("Type a word made of letters a-z."); return F; }
      if (nodeCount(root) + w.length > 60) { snap("The demo trie is full (60 nodes). Reset to start over."); return F; }
      let cur = root;
      const path = { [root.id]: SOFT(1) };
      snap(`insert("${w}"): start at the root. Each edge spells one character.`, { ...path, [root.id]: ACT });
      for (let i = 0; i < w.length; i++) {
        const ch = w[i];
        if (cur.c[ch]) { cur = cur.c[ch]; path[cur.id] = SOFT(1); snap(`'${ch}' already exists → follow it. The prefix "${w.slice(0, i + 1)}" is shared with earlier words.`, { ...path, [cur.id]: ACT }); }
        else { cur.c[ch] = mk(ch); cur = cur.c[ch]; path[cur.id] = SOFT(1); snap(`No child '${ch}' → create a new node for "${w.slice(0, i + 1)}".`, { ...path, [cur.id]: NEW }); }
      }
      if (cur.end) snap(`"${w}" was already stored (its last node is already marked end-of-word).`, { ...path, [cur.id]: DONE });
      else { cur.end = true; snap(`Mark the last node as end-of-word: "${w}" is stored. Insert cost is O(length of the word), independent of how many words are stored.`, { ...path, [cur.id]: DONE }); }
      if (quiet) F = [];
      return F;
    }
    function walk(p) {
      let cur = root;
      const path = { [root.id]: SOFT(1) };
      snap(`Follow "${p}" one character at a time from the root.`, { [root.id]: ACT });
      for (let i = 0; i < p.length; i++) {
        const ch = p[i];
        if (!cur.c[ch]) { snap(`No child '${ch}' after "${p.slice(0, i)}" → no stored word starts with "${p.slice(0, i + 1)}".`, { ...path, [cur.id]: DEL }); return null; }
        cur = cur.c[ch];
        path[cur.id] = SOFT(1);
        snap(`'${ch}' found → now at "${p.slice(0, i + 1)}".`, { ...path, [cur.id]: ACT });
      }
      return { cur, path };
    }
    function contains(w) {
      F = [];
      const r = walk(w);
      if (r) {
        if (r.cur.end) snap(`The node for "${w}" is marked end-of-word → "${w}" is in the trie.`, { ...r.path, [r.cur.id]: DONE }, [w]);
        else snap(`The path "${w}" exists but its last node is NOT marked end-of-word → "${w}" is only a prefix of stored words, not a word itself.`, { ...r.path, [r.cur.id]: DEL });
      }
      return F;
    }
    function prefix(p) {
      F = [];
      const r = walk(p);
      if (!r) return F;
      const found = [];
      const hl = { ...r.path };
      const dfs = (n, sofar) => {
        hl[n.id] = SOFT(2);
        if (n.end) { found.push(sofar); hl[n.id] = DONE; snap(`Collect "${sofar}" (end-of-word node).`, { ...hl }, [...found]); }
        kids(n).forEach((k) => dfs(k, sofar + k.ch));
      };
      snap(`Every word with prefix "${p}" lives in this node's subtree. Walk it depth-first in alphabetical order.`, { ...hl, [r.cur.id]: ACT });
      dfs(r.cur, p);
      snap(found.length ? `${found.length} word${found.length > 1 ? "s" : ""} start with "${p}": ${found.join(", ")}. This is why tries power autocomplete.` : `No complete words below "${p}".`, hl, found);
      return F;
    }
    function draw(f) {
      const { pos, width, depth } = layoutTree(f.root, kids);
      const W = Math.max(640, width * 40 + 40);
      const dx = Math.min(56, (W - 40) / width);
      const X = (p) => W / 2 + (p.x - (width - 1) / 2) * dx;
      const Y = (p) => 30 + p.y * 54;
      const g = s("g");
      for (const [n, p] of pos) for (const k of kids(n)) g.append(L(X(p), Y(p), X(pos.get(k)), Y(pos.get(k)), V("viz-edge"), 1.5));
      for (const [n, p] of pos) {
        const fill = f.hl[n.id] || V("viz-node");
        if (n.end) g.append(Ci(X(p), Y(p), 19, "none", V("viz-3"), 2.5));
        g.append(Ci(X(p), Y(p), 15, fill, V("border-strong"), 1.4), T(X(p), Y(p), n.ch || "•", { size: 12.5, weight: 700 }));
      }
      let y = 30 + (depth - 1) * 54 + 30;
      if (f.found) { g.append(T(14, y + 8, `result: ${f.found.join(", ") || "(none)"}`, { anchor: "start", size: 12, weight: 700, fill: V("viz-3") })); y += 24; }
      const svg = svgBox(W, y);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const wIn = field("", 100, "word or prefix");
    const read = () => { const t = wIn.value.toLowerCase().replace(/[^a-z]/g, "").slice(0, 10); wIn.value = ""; return t; };
    const RAND = ["cap", "card", "care", "dot", "dove", "door", "cab", "data", "deal", "car", "catalog", "do"];
    const start = () => { root = mk(""); init.forEach((w) => insert(w, true)); F = []; snap("Each node is one character; a ring marks the end of a stored word. Words that share a prefix share the path for it."); TL.reset(F[0]); };
    onEnter(wIn, () => TL.add(insert(read() || RAND[randInt(0, RAND.length - 1)])));
    tb.append(wIn, button("Insert", () => TL.add(insert(read() || RAND[randInt(0, RAND.length - 1)])), "btn small primary"),
      button("Contains word?", () => TL.add(contains(read() || "ca"))),
      button("Prefix search", () => TL.add(prefix(read() || "ca"))),
      button("Reset", start));
    ui.setLegend([["current", ACT], ["path", SOFT(1)], ["new node", NEW], ["end of word / found", DONE], ["missing", DEL]]);
    start();
  });

  /* ---------- union-find ---------- */
  registerViz("union-find", (el, cfg) => {
    const n = Math.max(2, Math.min(16, Math.round(Number(cfg.n) || 8)));
    const ui = shell(el, { title: `Disjoint sets on 0..${n - 1}`, kind: "Union-find" });
    const tb = toolbar(ui);
    let parent;
    let rank;
    let F = [];
    const snap = (log, hl = {}, cells = {}) => F.push({ parent: [...parent], rank: [...rank], hl, cells, log });
    function find(x) {
      const path = [x];
      let cur = x;
      snap(`find(${x}): follow parent pointers up to the root.`, { [x]: ACT });
      while (parent[cur] !== cur) {
        snap(`parent[${cur}] = ${parent[cur]} ≠ ${cur} → move up to ${parent[cur]}.`, { ...Object.fromEntries(path.map((p) => [p, SOFT(2)])), [parent[cur]]: ACT }, { [`p${cur}`]: ACT });
        cur = parent[cur];
        path.push(cur);
      }
      const r = cur;
      snap(`parent[${r}] = ${r} → ${r} is the root, the representative of this set.`, { ...Object.fromEntries(path.map((p) => [p, SOFT(2)])), [r]: DONE });
      for (const v of path.slice(0, -1)) {
        if (parent[v] !== r) {
          parent[v] = r;
          snap(`Path compression: parent[${v}] = ${r}. Next time, find(${v}) takes one hop.`, { [v]: NEW, [r]: DONE }, { [`p${v}`]: NEW });
        }
      }
      return r;
    }
    function union(a, b) {
      F = [];
      snap(`union(${a}, ${b}): find both roots, then link the shorter tree under the taller one (union by rank).`, { [a]: ACT, [b]: ACT });
      let ra = find(a);
      let rb = find(b);
      if (ra === rb) { snap(`${a} and ${b} already share root ${ra} → same set, nothing to do.`, { [ra]: DONE }); return F; }
      if (rank[ra] < rank[rb]) { [ra, rb] = [rb, ra]; }
      if (rank[ra] === rank[rb]) {
        parent[rb] = ra;
        rank[ra]++;
        snap(`Ranks are equal (${rank[ra] - 1}) → attach root ${rb} under ${ra} and increase rank[${ra}] to ${rank[ra]}.`, { [rb]: NEW, [ra]: DONE }, { [`p${rb}`]: NEW, [`r${ra}`]: NEW });
      } else {
        parent[rb] = ra;
        snap(`rank[${ra}] = ${rank[ra]} > rank[${rb}] = ${rank[rb]} → attach the shorter tree ${rb} under ${ra}; no tree gets taller.`, { [rb]: NEW, [ra]: DONE }, { [`p${rb}`]: NEW });
      }
      snap(`Merged. With union by rank plus path compression, each operation costs nearly O(1) amortized (inverse Ackermann).`);
      return F;
    }
    function connected(a, b) {
      F = [];
      const ra = find(a);
      const rb = find(b);
      snap(ra === rb ? `find(${a}) = find(${b}) = ${ra} → connected (same set).` : `find(${a}) = ${ra} but find(${b}) = ${rb} → different sets.`, { [a]: ra === rb ? DONE : DEL, [b]: ra === rb ? DONE : DEL });
      return F;
    }
    function draw(f) {
      const W = 640;
      const g = s("g");
      const kidsOf = Array.from({ length: n }, () => []);
      const roots = [];
      f.parent.forEach((p, i) => { if (p === i) roots.push(i); else kidsOf[p].push(i); });
      const tree = (i) => ({ i, children: kidsOf[i].map(tree) });
      const top = { i: -1, children: roots.map(tree) };
      const { pos, width, depth } = layoutTree(top);
      const dx = Math.min(60, (W - 40) / width);
      const X = (p) => W / 2 + (p.x - (width - 1) / 2) * dx;
      const Y = (p) => 30 + (p.y - 1) * 58;
      g.append(T(14, 10, `${roots.length} set${roots.length === 1 ? "" : "s"} · arrows point from child to parent`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      for (const [nd, p] of pos) for (const c of nd.children) if (nd.i >= 0) { const q = pos.get(c); const ang = Math.atan2(Y(p) - Y(q), X(p) - X(q)); g.append(arrow(X(q), Y(q) - 16, X(p) - Math.cos(ang) * 17, Y(p) - Math.sin(ang) * 17 + 0, V("viz-edge"), { head: 6 })); }
      for (const [nd, p] of pos) {
        if (nd.i < 0) continue;
        const isRoot = f.parent[nd.i] === nd.i;
        g.append(Ci(X(p), Y(p), 16, f.hl[nd.i] || V("viz-node"), isRoot ? V("viz-1") : V("border-strong"), isRoot ? 2.6 : 1.4), T(X(p), Y(p), nd.i, { weight: 700 }));
      }
      let y = 30 + (depth - 2) * 58 + 36;
      const cw = Math.min(36, (W - 90) / n);
      const x0 = 80;
      [["i", null], ["parent", "p"], ["rank", "r"]].forEach(([name, key], row) => {
        const yy = y + row * 30;
        g.append(T(x0 - 8, yy + 13, name, { anchor: "end", size: 10.5, fill: V("fg-muted") }));
        for (let i = 0; i < n; i++) {
          const v = key === null ? i : key === "p" ? f.parent[i] : f.rank[i];
          const fill = key ? f.cells[`${key}${i}`] || V("viz-node") : V("bg-sunk");
          g.append(R(x0 + i * cw, yy, cw - 2, 26, fill, V("border-strong"), { rx: 3 }), T(x0 + i * cw + cw / 2 - 1, yy + 13, v, { size: 11, weight: key ? 700 : 400, fill: key ? V("fg") : V("fg-faint") }));
        }
      });
      y += 96;
      const svg = svgBox(W, y);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const aIn = field("0", 44, "a");
    const bIn = field("1", 44, "b");
    const get = (inp) => { const v = Math.round(Number(inp.value)); return Number.isFinite(v) && v >= 0 && v < n ? v : randInt(0, n - 1); };
    const start = () => { parent = Array.from({ length: n }, (_, i) => i); rank = Array(n).fill(0); F = []; snap(`Every element starts in its own set: parent[i] = i, rank[i] = 0. union(a, b) merges sets; find(x) returns a set's root.`); TL.reset(F[0]); };
    tb.append(label("a", aIn), label("b", bIn), button("Union", () => TL.add(union(get(aIn), get(bIn))), "btn small primary"),
      button("Find a", () => { F = []; find(get(aIn)); TL.add(F); }),
      button("Connected?", () => TL.add(connected(get(aIn), get(bIn)))),
      button("Random union", () => { const a = randInt(0, n - 1); let b = randInt(0, n - 1); if (b === a) b = (a + 1) % n; aIn.value = a; bIn.value = b; TL.add(union(a, b)); }),
      button("Reset", start));
    ui.setLegend([["current", ACT], ["on the find path", SOFT(2)], ["root", DONE], ["re-linked", NEW]]);
    start();
  });

  /* ---------- lru-cache ---------- */
  registerViz("lru-cache", (el, cfg) => {
    const cap = Math.max(1, Math.min(6, Math.round(Number(cfg.capacity) || 3)));
    const ui = shell(el, { title: `LRU cache (capacity ${cap}): dict + doubly linked list`, kind: "LRU cache" });
    const tb = toolbar(ui);
    let list;
    let mapOrder;
    let hits;
    let misses;
    let F = [];
    const snap = (log, x = {}) => F.push({ list: deep(list), mapOrder: [...mapOrder], hl: x.hl || {}, mapHl: x.mapHl || null, hits, misses, ret: x.ret ?? null, log });
    const idx = (k) => list.findIndex((e) => e.k === k);
    function get(k) {
      F = [];
      snap(`get(${showKey(k)}): look the key up in the dict, O(1).`, { mapHl: k });
      const i = idx(k);
      if (i < 0) { misses++; snap(`${showKey(k)} is not in the dict → cache miss, return -1 (a real cache would now compute the value).`, { mapHl: k, ret: -1 }); return F; }
      hits++;
      const e = list[i];
      snap(`Hit: the dict entry points straight at node ${showKey(k)}. Unlink it using its prev/next pointers, O(1).`, { hl: { [k]: ACT }, mapHl: k });
      list.splice(i, 1);
      list.unshift(e);
      snap(`Splice it in right after head: ${showKey(k)} is now the most recently used. Return ${e.v}.`, { hl: { [k]: DONE }, ret: e.v });
      return F;
    }
    function put(k, v) {
      F = [];
      const i = idx(k);
      if (i >= 0) {
        snap(`put(${showKey(k)}, ${v}): key exists → update the value and move it to the front.`, { hl: { [k]: ACT }, mapHl: k });
        list[i].v = v;
        const e = list.splice(i, 1)[0];
        list.unshift(e);
        snap(`${showKey(k)} = ${v} is now the most recently used.`, { hl: { [k]: DONE } });
        return F;
      }
      if (list.length >= cap) {
        const lru = list[list.length - 1];
        snap(`put(${showKey(k)}, ${v}): the cache is full (${cap}/${cap}). Evict the least recently used entry, ${showKey(lru.k)}: the node just before tail.`, { hl: { [lru.k]: DEL }, mapHl: lru.k });
        list.pop();
        mapOrder = mapOrder.filter((x) => x !== lru.k);
        snap(`Removed node ${showKey(lru.k)} from the list and deleted its dict entry, both O(1).`);
      }
      list.unshift({ k, v });
      mapOrder.push(k);
      snap(`Insert node ${showKey(k)}=${v} right after head and store dict[${showKey(k)}] → node. Size ${list.length}/${cap}.`, { hl: { [k]: NEW }, mapHl: k });
      return F;
    }
    function draw(f) {
      const step = 92;
      const W = Math.max(640, 40 + (f.list.length + 2) * step);
      const g = s("g");
      const y = 50;
      const xs = {};
      const boxes = [{ k: "head", sentinel: true }, ...f.list, { k: "tail", sentinel: true }];
      g.append(T(14, 12, `hits ${f.hits} · misses ${f.misses}${f.hits + f.misses ? ` · hit rate ${Math.round((100 * f.hits) / (f.hits + f.misses))}%` : ""}${f.ret != null ? ` · returned ${f.ret}` : ""}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      boxes.forEach((b, i) => {
        const x = 20 + i * step;
        if (!b.sentinel) xs[b.k] = x;
        g.append(R(x, y, 68, 40, b.sentinel ? V("bg-sunk") : f.hl[b.k] || V("viz-node"), V("border-strong"), { rx: 5, dash: b.sentinel ? "4 3" : null }));
        g.append(T(x + 34, y + 20, b.sentinel ? b.k : `${showKey(b.k)}: ${b.v}`, { size: b.sentinel ? 11 : 12, weight: b.sentinel ? 400 : 700, fill: b.sentinel ? V("fg-faint") : V("fg") }));
        if (i < boxes.length - 1) {
          g.append(arrow(x + 68, y + 13, x + step, y + 13, V("viz-1"), { head: 6 }));
          g.append(arrow(x + step, y + 28, x + 68, y + 28, V("viz-5"), { head: 6 }));
        }
      });
      if (f.list.length) {
        g.append(T(20 + step + 34, y - 12, "MRU", { size: 10, weight: 700, fill: V("viz-3") }));
        g.append(T(20 + f.list.length * step + 34, y - 12 - (f.list.length === 1 ? 12 : 0), "LRU (evicted next)", { size: 10, weight: 700, fill: V("viz-4") }));
      }
      const my = 160;
      g.append(T(20, my - 14, "dict: key → node", { anchor: "start", size: 11, fill: V("fg-muted"), weight: 700 }));
      f.mapOrder.forEach((k, i) => {
        const x = 20 + i * 76;
        const on = f.mapHl === k;
        g.append(R(x, my, 64, 28, on ? ACT : V("bg-elev"), V("border-strong"), { rx: 3 }), T(x + 24, my + 14, showKey(k), { size: 11, weight: 700 }), Ci(x + 52, my + 14, 3.5, V("fg"), V("fg"), 1));
        if (xs[k] != null) g.append(arrow(x + 52, my + 8, xs[k] + 34, y + 42, on ? V("accent") : V("viz-edge"), { dash: on ? null : "3 3", sw: on ? 2 : 1.2, head: 6 }));
      });
      if (f.mapHl != null && !f.mapOrder.includes(f.mapHl)) g.append(T(20 + f.mapOrder.length * 76, my + 14, `${showKey(f.mapHl)}: not in dict`, { anchor: "start", size: 11, fill: V("bad") }));
      const svg = svgBox(W, my + 44);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const kIn = field("", 60, "key");
    const vIn = field("", 60, "value");
    const key = () => { const t = kIn.value.trim().slice(0, 6); kIn.value = ""; return t ? parseKey(t) : randInt(1, 6); };
    const value = () => { const t = vIn.value.trim().slice(0, 5); vIn.value = ""; return t || String(randInt(10, 99)); };
    const start = () => { list = []; mapOrder = []; hits = 0; misses = 0; F = []; snap("The dict finds a key's node in O(1); the doubly linked list keeps usage order (front = most recent) and unlinks any node in O(1). functools.lru_cache and OrderedDict.move_to_end use the same idea."); TL.reset(F[0]); };
    onEnter(kIn, () => TL.add(get(key())));
    tb.append(kIn, vIn, button("get(key)", () => TL.add(get(key())), "btn small primary"), button("put(key, value)", () => TL.add(put(key(), value()))),
      button("Random ops ×5", () => { const all = []; for (let i = 0; i < 5; i++) { const k = randInt(1, cap + 2); all.push(...(Math.random() < 0.5 ? get(k) : put(k, String(randInt(10, 99))))); } TL.add(all); }),
      button("Reset", start));
    ui.setLegend([["next pointer", V("viz-1")], ["prev pointer", V("viz-5")], ["looked up", ACT], ["inserted", NEW], ["moved to front", DONE], ["evicted", DEL]]);
    start();
  });

  /* ---------- bloom-filter ---------- */
  registerViz("bloom-filter", (el, cfg) => {
    let m = Math.max(8, Math.min(128, Math.round(Number(cfg.m) || 32)));
    let k = Math.max(1, Math.min(8, Math.round(Number(cfg.k) || 3)));
    const ui = shell(el, { title: "", kind: "Bloom filter" });
    const tb = toolbar(ui);
    const tb2 = toolbar(ui);
    let bits;
    let added;
    let F = [];
    const fp = () => (1 - Math.exp((-k * added.length) / m)) ** k;
    const snap = (log, hl = {}, x = {}) => F.push({ bits: [...bits], added: [...added], m, k, hl, verdict: x.verdict || null, log });
    function positions(w) {
      const h1 = fnv1a(w);
      const h2 = djb2(w) | 1;
      return { h1, h2, ps: Array.from({ length: k }, (_, i) => Number((BigInt(h1) + BigInt(i) * BigInt(h2 >>> 0)) % BigInt(m))) };
    }
    function add(w) {
      F = [];
      const { h1, h2, ps } = positions(w);
      snap(`add("${w}"): compute ${k} positions with double hashing, position_i = (h1 + i·h2) mod ${m}, where h1 = ${h1} and h2 = ${h2 >>> 0}.`);
      const hl = {};
      ps.forEach((p, i) => {
        const was = bits[p];
        bits[p] = 1;
        hl[p] = ACT;
        snap(`h${i}("${w}") = ${p} → set bit ${p} to 1${was ? " (it was already 1; another word set it)" : ""}.`, { ...hl });
        hl[p] = SOFT(1);
      });
      if (!added.includes(w)) added.push(w);
      snap(`"${w}" added. ${bits.filter(Boolean).length}/${m} bits set. Estimated false-positive rate (1 - e^(-k·n/m))^k = ${(fp() * 100).toFixed(1)}% for n = ${added.length}.`, hl);
      return F;
    }
    function check(w) {
      F = [];
      const { ps } = positions(w);
      snap(`check("${w}"): compute the same ${k} positions: ${ps.join(", ")}. All must be 1 for a "maybe".`);
      const hl = {};
      for (let i = 0; i < ps.length; i++) {
        const p = ps[i];
        if (!bits[p]) { hl[p] = DEL; snap(`Bit ${p} is 0 → "${w}" was definitely never added. Bloom filters have no false negatives.`, { ...hl }, { verdict: "definitely not present" }); return F; }
        hl[p] = DONE;
        snap(`Bit ${p} is 1 ✓`, { ...hl });
      }
      if (added.includes(w)) snap(`All ${k} bits are 1 → "${w}" is probably present (and it really was added).`, hl, { verdict: "probably present (true positive)" });
      else snap(`All ${k} bits are 1, but "${w}" was never added → FALSE POSITIVE: other words happened to set these bits. The filter trades this risk for tiny memory use.`, hl, { verdict: "false positive!" });
      return F;
    }
    function draw(f) {
      const W = 640;
      const g = s("g");
      g.append(T(14, 10, `m = ${f.m} bits · k = ${f.k} hashes · n = ${f.added.length} added · ${f.bits.filter(Boolean).length} bits set`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      const per = 16;
      const cw = 37;
      const y0 = 26;
      for (let i = 0; i < f.m; i++) {
        const x = 16 + (i % per) * cw;
        const y = y0 + Math.floor(i / per) * 46;
        const on = f.bits[i];
        g.append(R(x, y, cw - 3, 28, f.hl[i] || (on ? SOFT(1) : V("bg-sunk")), f.hl[i] ? V("fg") : V("border-strong"), { rx: 3, sw: f.hl[i] ? 2 : 1.2 }), T(x + (cw - 3) / 2, y + 14, on, { size: 12, weight: on ? 700 : 400, fill: on ? V("fg") : V("fg-faint") }), T(x + (cw - 3) / 2, y + 36, i, { size: 8.5, fill: V("fg-faint") }));
      }
      let y = y0 + Math.ceil(f.m / per) * 46 + 6;
      g.append(T(14, y + 8, `added: ${f.added.join(", ") || "(nothing yet)"}`, { anchor: "start", size: 11, fill: V("fg-muted") }));
      y += 22;
      if (f.verdict) { g.append(T(14, y + 8, `verdict: ${f.verdict}`, { anchor: "start", size: 12.5, weight: 700, fill: f.verdict.startsWith("false") ? V("bad") : f.verdict.startsWith("def") ? V("fg") : V("ok") })); y += 22; }
      const svg = svgBox(W, y + 6);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const TL = timeline(ui, draw);
    const wIn = field("", 100, "word");
    const POOL = [...WORDS, "cat", "dog", "owl", "fox", "bee", "ant", "elk", "yak"];
    const word = (fallback) => { const t = wIn.value.trim().slice(0, 12); wIn.value = ""; return t || fallback(); };
    const mIn = field(String(m), 46, "m");
    const kIn = field(String(k), 34, "k");
    const start = () => {
      m = Math.max(8, Math.min(128, Math.round(Number(mIn.value) || m)));
      k = Math.max(1, Math.min(8, Math.round(Number(kIn.value) || k)));
      mIn.value = m;
      kIn.value = k;
      ui.head.querySelector(".w-title").textContent = `Bloom filter: ${m} bits, ${k} hash functions`;
      bits = Array(m).fill(0);
      added = [];
      F = [];
      snap("A Bloom filter answers 'have I seen this?' with a bit array. add sets k bits; check reports 'definitely not' if any bit is 0, otherwise 'probably yes'.");
      TL.reset(F[0]);
    };
    onEnter(wIn, () => TL.add(add(word(() => POOL[randInt(0, POOL.length - 1)]))));
    tb.append(wIn, button("Add", () => TL.add(add(word(() => POOL[randInt(0, POOL.length - 1)]))), "btn small primary"),
      button("Check", () => TL.add(check(word(() => POOL[randInt(0, POOL.length - 1)])))),
      button("Add 5 random", () => { const all = []; shuffle(POOL.filter((w) => !added.includes(w))).slice(0, 5).forEach((w) => all.push(...add(w))); TL.add(all); }),
      button("Hunt a false positive", () => {
        const cands = ["zebra", "quail", "viper", "tiger", "moose", "llama", "koala", "hyena", "gecko", "camel", "bison", "otter", "panda", "raven", "shark", "squid", "whale", "crane", "eagle", "horse"];
        const hit = cands.find((w) => !added.includes(w) && positions(w).ps.every((p) => bits[p]));
        TL.add(check(hit || cands[randInt(0, cands.length - 1)]));
      }));
    tb2.append(label("m", mIn), label("k", kIn), button("Rebuild", start), button("Reset", start));
    ui.setLegend([["bit set", SOFT(1)], ["being set / checked", ACT], ["checked = 1", DONE], ["checked = 0", DEL]]);
    start();
  });

  /* ---------- matrix ---------- */
  registerViz("matrix", (el, cfg) => {
    let op = ["dot", "matmul", "transpose", "broadcast"].includes(cfg.op) ? cfg.op : "matmul";
    const DEFAULTS = { dot: ["1 2 3 4", "5 6 7 8"], matmul: ["1 2 3; 4 5 6", "7 8; 9 10; 11 12"], transpose: ["1 2 3; 4 5 6", ""], broadcast: ["1; 2; 3", "10 20 30 40"] };
    const ui = shell(el, { title: "", kind: "Matrix" });
    const tb = toolbar(ui);
    const aIn = field("", 150, "A, e.g. 1 2; 3 4");
    const bIn = field("", 150, "B");
    const parse = (t) => {
      const txt = String(t).trim();
      if (!txt) return null;
      const rows = txt.split(";").map((r) => parseList(r)).filter((r) => r.length);
      if (!rows.length) return null;
      if (!txt.includes(";")) return { d: [rows[0]], shape: [rows[0].length], vec: true };
      const c = rows[0].length;
      if (rows.some((r) => r.length !== c)) return { err: "every row needs the same number of columns" };
      return { d: rows, shape: [rows.length, c], vec: false };
    };
    const shp = (a) => `(${a.join(", ")}${a.length === 1 ? "," : ""})`;
    const K = (i, j) => `${i},${j}`;
    const frame = (log, mats, extra = {}) => ({ mats, log, lines: extra.lines || [], syms: extra.syms || [] });
    const mat = (name, d, x = {}) => ({ name, d, hl: x.hl || {}, shade: x.shade || {}, note: x.note || "" });
    function build(A, B) {
      const F = [];
      if (!A || A.err || (op !== "transpose" && (!B || B.err))) return [frame(`Could not read the input: ${(A && A.err) || (B && B.err) || "enter numbers separated by spaces, rows separated by ;"}.`, [])];
      if (op === "dot") {
        const a = A.d.flat();
        const b = B.d.flat();
        if (a.length !== b.length) return [frame(`np.dot needs equal lengths: ${a.length} != ${b.length} → ValueError: shapes (${a.length},) and (${b.length},) not aligned.`, [mat("a", [a]), mat("b", [b])], { syms: ["·"] })];
        let sum = 0;
        const terms = [];
        F.push(frame(`a · b multiplies matching positions and adds the products. Both have length ${a.length}.`, [mat("a", [a]), mat("b", [b]), mat("sum", [[0]])], { syms: ["·", "="] }));
        a.forEach((v, i) => {
          sum += v * b[i];
          terms.push(`${v}·${b[i]}`);
          F.push(frame(`a[${i}] · b[${i}] = ${v} · ${b[i]} = ${v * b[i]}; running sum = ${fmtNum(sum)}.`, [mat("a", [a], { hl: { [K(0, i)]: ACT } }), mat("b", [b], { hl: { [K(0, i)]: ACT } }), mat("sum", [[fmtNum(sum)]], { hl: { "0,0": NEW } })], { syms: ["·", "="], lines: [terms.join(" + ")] }));
        });
        F.push(frame(`a @ b = np.dot(a, b) = ${fmtNum(sum)}. Geometrically, the dot product measures how much two vectors point the same way.`, [mat("a", [a]), mat("b", [b]), mat("sum", [[fmtNum(sum)]], { hl: { "0,0": DONE } })], { syms: ["·", "="], lines: [`${terms.join(" + ")} = ${fmtNum(sum)}`] }));
        return F;
      }
      if (op === "transpose") {
        const a = A.d;
        const r = a.length;
        const c = a[0].length;
        const t = Array.from({ length: c }, () => Array(r).fill(null));
        F.push(frame(`A has shape (${r}, ${c}); A.T has shape (${c}, ${r}). Row i of A becomes column i of A.T.`, [mat("A", a), mat("A.T", t.map((x) => [...x]))], { syms: ["→"] }));
        for (let i = 0; i < r; i++) for (let j = 0; j < c; j++) {
          t[j][i] = a[i][j];
          F.push(frame(`A[${i}][${j}] = ${a[i][j]} → A.T[${j}][${i}].`, [mat("A", a, { hl: { [K(i, j)]: ACT } }), mat("A.T", t.map((x) => [...x]), { hl: { [K(j, i)]: NEW } })], { syms: ["→"] }));
        }
        F.push(frame("Done. In NumPy, A.T is a view: no data is copied, only the strides are swapped.", [mat("A", a), mat("A.T", t)], { syms: ["→"] }));
        return F;
      }
      if (op === "matmul") {
        const a = A.d;
        const b = B.vec ? B.d[0].map((v) => [v]) : B.d;
        const [n, k1] = [a.length, a[0].length];
        const [k2, p] = [b.length, b[0].length];
        if (k1 !== k2) return [frame(`A @ B needs A's column count to equal B's row count: shapes (${n}, ${k1}) and (${k2}, ${p}) not aligned: ${k1} (dim 1) != ${k2} (dim 0).`, [mat("A", a), mat("B", b)], { syms: ["@"] })];
        const C = Array.from({ length: n }, () => Array(p).fill(null));
        F.push(frame(`A is (${n}, ${k1}) and B is (${k2}, ${p}): the inner sizes match (${k1}), so C = A @ B has shape (${n}, ${p}). Each C[i][j] is row i of A dotted with column j of B.`, [mat("A", a), mat("B", b), mat("C", C.map((r) => [...r]))], { syms: ["@", "="] }));
        for (let i = 0; i < n; i++) for (let j = 0; j < p; j++) {
          let sum = 0;
          const terms = [];
          for (let q = 0; q < k1; q++) { sum += a[i][q] * b[q][j]; terms.push(`${a[i][q]}·${b[q][j]}`); }
          C[i][j] = fmtNum(sum);
          const hlA = Object.fromEntries(a[i].map((_, q) => [K(i, q), ACT]));
          const hlB = Object.fromEntries(b.map((_, q) => [K(q, j), SOFT(1)]));
          F.push(frame(`C[${i}][${j}] = row ${i} of A · column ${j} of B = ${terms.join(" + ")} = ${fmtNum(sum)}.`, [mat("A", a, { hl: hlA }), mat("B", b, { hl: hlB }), mat("C", C.map((r) => [...r]), { hl: { [K(i, j)]: NEW } })], { syms: ["@", "="], lines: [`C[${i}][${j}] = ${terms.join(" + ")} = ${fmtNum(sum)}`] }));
        }
        F.push(frame(`Done: ${n * p} cells × ${k1} multiplications each = ${n * p * k1} multiply-adds. Naive matrix multiply of two n×n matrices is O(n³).`, [mat("A", a), mat("B", b), mat("C", C)], { syms: ["@", "="] }));
        return F;
      }
      const sa = A.shape;
      const sb = B.shape;
      const nd = Math.max(sa.length, sb.length);
      const pad = (s0) => [...Array(nd - s0.length).fill(1), ...s0];
      const pa = pad(sa);
      const pb = pad(sb);
      const align = () => {
        const w = (s0) => s0.map((d) => String(d).padStart(3)).join(" ");
        return [`A: ${w(sa).padStart(nd * 4)}`, `B: ${w(sb).padStart(nd * 4)}`];
      };
      const a2 = pa.length === 1 ? [A.d.flat()] : A.d;
      const b2 = pb.length === 1 ? [B.d.flat()] : B.d;
      const show = [mat(`A ${shp(sa)}`, a2), mat(`B ${shp(sb)}`, b2)];
      F.push(frame(`Broadcasting A ${shp(sa)} + B ${shp(sb)}: line the shapes up from the RIGHT and compare one dimension at a time.`, show, { syms: ["+"], lines: align() }));
      if (sa.length !== sb.length) F.push(frame(`${sa.length < sb.length ? "A" : "B"} has fewer dimensions, so NumPy treats its shape as ${shp(sa.length < sb.length ? pa : pb)} by prepending 1s on the left.`, show, { syms: ["+"], lines: [`A: ${shp(pa)}`, `B: ${shp(pb)}`] }));
      const res = [];
      for (let d = nd - 1; d >= 0; d--) {
        const x = pa[d];
        const y = pb[d];
        if (x !== y && x !== 1 && y !== 1) return [...F, frame(`Dimension ${d - nd}: ${x} vs ${y}. They differ and neither is 1 → ValueError: operands could not be broadcast together with shapes ${shp(sa)} ${shp(sb)}.`, show, { syms: ["+"], lines: [`A: ${shp(pa)}`, `B: ${shp(pb)}`, "✗ incompatible"] })];
        res.unshift(Math.max(x, y));
        F.push(frame(`Dimension ${d - nd}: A has ${x}, B has ${y} → ${x === y ? "equal, fine" : `one of them is 1, so ${x === 1 ? "A" : "B"} is stretched to ${Math.max(x, y)}`}.`, show, { syms: ["+"], lines: [`A: ${shp(pa)}`, `B: ${shp(pb)}`, `result so far: (…${res.join(", ")})`] }));
      }
      const [R0, C0] = res.length === 1 ? [1, res[0]] : res;
      const ar = a2.length;
      const ac = a2[0].length;
      const br = b2.length;
      const bc = b2[0].length;
      const at = (m0, r, c, i, j) => m0[r === 1 ? 0 : i][c === 1 ? 0 : j];
      const stretch = (m0, r, c) => {
        const d = [];
        const shade = {};
        for (let i = 0; i < R0; i++) { d.push([]); for (let j = 0; j < C0; j++) { d[i].push(at(m0, r, c, i, j)); if ((r === 1 && i > 0) || (c === 1 && j > 0)) shade[K(i, j)] = 1; } }
        return { d, shade };
      };
      const SA = stretch(a2, ar, ac);
      const SB = stretch(b2, br, bc);
      const out = Array.from({ length: R0 }, () => Array(C0).fill(null));
      const stretched = () => [mat("A stretched", SA.d, { shade: SA.shade }), mat("B stretched", SB.d, { shade: SB.shade })];
      F.push(frame(`Result shape ${shp(res)}. Shaded cells are virtual copies: NumPy uses a stride of 0 along stretched dimensions, so no memory is copied.`, [...stretched(), mat(`A + B ${shp(res)}`, out.map((r) => [...r]))], { syms: ["+", "="], lines: [`A: ${shp(pa)}`, `B: ${shp(pb)}`, `→ ${shp(res)}`] }));
      for (let i = 0; i < R0; i++) {
        for (let j = 0; j < C0; j++) out[i][j] = fmtNum(SA.d[i][j] + SB.d[i][j]);
        const hl = Object.fromEntries(Array.from({ length: C0 }, (_, j) => [K(i, j), ACT]));
        F.push(frame(`Row ${i}: [${SA.d[i].map((v, j) => `${v}+${SB.d[i][j]}`).join(", ")}] = [${out[i].join(", ")}].`, [mat("A stretched", SA.d, { shade: SA.shade, hl }), mat("B stretched", SB.d, { shade: SB.shade, hl }), mat(`A + B ${shp(res)}`, out.map((r) => [...r]), { hl: Object.fromEntries(Array.from({ length: C0 }, (_, j) => [K(i, j), NEW])) })], { syms: ["+", "="], lines: [`→ ${shp(res)}`] }));
      }
      F.push(frame(`A + B has shape ${shp(res)}. Rule: dimensions are compatible when they are equal or one of them is 1.`, [...stretched(), mat(`A + B ${shp(res)}`, out)], { syms: ["+", "="], lines: [`A: ${shp(pa)}`, `B: ${shp(pb)}`, `→ ${shp(res)}`] }));
      return F;
    }
    function draw(f) {
      const cw = 42;
      const ch = 30;
      const gap = 40;
      const top = 18 + f.lines.length * 17 + 18;
      let x = 20;
      const g = s("g");
      f.lines.forEach((ln, i) => g.append(T(20, 14 + i * 17, ln, { anchor: "start", size: 12, fill: V("fg-muted"), font: MONO })));
      let maxH = 0;
      f.mats.forEach((m0, mi) => {
        const rows = m0.d.length;
        const cols = m0.d[0].length;
        g.append(T(x + (cols * cw) / 2, top - 10, m0.name, { size: 11, weight: 700, fill: V("fg-muted") }));
        for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) {
          const v = m0.d[i][j];
          const sh = m0.shade[K(i, j)];
          g.append(R(x + j * cw, top + i * ch, cw - 2, ch - 2, m0.hl[K(i, j)] || (sh ? V("bg-sunk") : V("viz-node")), sh ? V("fg-faint") : V("border-strong"), { rx: 3, dash: sh ? "3 3" : null }));
          g.append(T(x + j * cw + cw / 2 - 1, top + i * ch + ch / 2 - 1, v == null ? "·" : v, { size: 12, weight: 700, op: sh ? 0.5 : null, fill: v == null ? V("fg-faint") : V("fg") }));
        }
        const hh = rows * ch;
        const br = (bx, dir) => s("path", { d: `M${bx + dir * 6},${top - 3} L${bx},${top - 3} L${bx},${top + hh + 1} L${bx + dir * 6},${top + hh + 1}`, style: `fill:none;stroke:${V("fg-muted")};stroke-width:1.5` });
        g.append(br(x - 5, 1), br(x + cols * cw + 3, -1));
        maxH = Math.max(maxH, hh);
        x += cols * cw;
        if (f.syms[mi]) { g.append(T(x + gap / 2, top + Math.min(hh, 60) / 2, f.syms[mi], { size: 18, weight: 700, fill: V("fg-muted") })); }
        x += gap;
      });
      const W = Math.max(400, x);
      const svg = svgBox(W, top + maxH + 14);
      svg.append(g);
      ui.stage.replaceChildren(svg);
    }
    const P = player(ui.controls, (f) => { draw(f); ui.setLog(esc(f.log)); }, { speed: 900 });
    const run = () => { P.load(build(parse(aIn.value), parse(bIn.value)), 0); };
    const setOp = (o) => {
      op = o;
      ui.head.querySelector(".w-title").textContent = { dot: "Dot product a · b", matmul: "Matrix multiply A @ B", transpose: "Transpose A.T", broadcast: "Broadcasting A + B" }[op];
      [aIn.value, bIn.value] = DEFAULTS[op];
      (bIn.parentElement || bIn).style.display = op === "transpose" ? "none" : "";
      run();
    };
    const rnd = (r, c) => Array.from({ length: r }, () => Array.from({ length: c }, () => randInt(-3, 9)).join(" ")).join("; ");
    const randomize = () => {
      if (op === "dot") { const n = randInt(3, 5); aIn.value = rnd(1, n); bIn.value = rnd(1, n); }
      else if (op === "matmul") { const n = randInt(2, 3); const k0 = randInt(2, 4); const p = randInt(2, 3); aIn.value = rnd(n, k0); bIn.value = rnd(k0, p); }
      else if (op === "transpose") aIn.value = rnd(randInt(2, 3), randInt(2, 4));
      else { const opts = [["1; 2; 3", rnd(1, 4)], [rnd(2, 3), rnd(1, 3)], [rnd(3, 1).replace(/;/g, ";"), rnd(1, 2)], [rnd(2, 3), "1 2"]]; [aIn.value, bIn.value] = opts[randInt(0, opts.length - 1)]; }
      run();
    };
    onEnter(aIn, run);
    onEnter(bIn, run);
    tb.append(label("op", select([["dot", "dot product"], ["matmul", "matrix multiply"], ["transpose", "transpose"], ["broadcast", "broadcasting"]], op, setOp)), label("A", aIn), label("B", bIn),
      button("Run", run, "btn small primary"), button("Random", randomize), button("Reset", () => setOp(op)));
    ui.setLegend([["current", ACT], ["column in use", SOFT(1)], ["result written", NEW], ["stretched (virtual) copy", V("bg-sunk")]]);
    setOp(op);
  });
})();
