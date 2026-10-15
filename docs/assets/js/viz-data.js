/* Data, concurrency, and ML visualizers: event-loop, gradient-descent, kmeans, neural-net, pipeline. */
(() => {
  "use strict";
  if (!window.PPViz) return;
  const { registerViz } = window.PPViz;

  // ---------------------------------------------------------------- shared helpers
  function mulberry32(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(r) {
    let u = 0;
    while (u === 0) u = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r());
  }
  const newSeed = () => Math.floor(Math.random() * 2147483647);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const clear = (node) => { while (node.firstChild) node.removeChild(node.firstChild); };
  let uidCounter = 0;
  const uid = (p) => `${p}-${++uidCounter}`;

  function fmt(v, d = 3) {
    if (!Number.isFinite(v)) return Number.isNaN(v) ? "NaN" : v > 0 ? "∞" : "−∞";
    const a = Math.abs(v);
    if (a !== 0 && (a >= 1e5 || a < 1e-3)) return v.toExponential(2).replace(/-/g, "−");
    return Number(v.toFixed(d)).toString().replace(/-/g, "−");
  }
  const fmtV = (v) => `(${v.map((x) => fmt(x)).join(", ")})`;

  function makeSvg(s, w, hgt, label) {
    return s("svg", {
      viewBox: `0 0 ${w} ${hgt}`, width: "100%", role: "img", "aria-label": label,
      style: `max-width:${w}px;height:auto;font-family:var(--font-sans)`,
    });
  }
  function txt(s, x, y, str, attrs = {}) {
    return s("text", { x, y, "font-size": 11, fill: "var(--fg-muted)", ...attrs, text: str });
  }
  function checkbox(api, text, checked, onChange) {
    const cb = api.h("input", { type: "checkbox" });
    cb.checked = checked;
    cb.addEventListener("change", () => onChange(cb.checked));
    return api.label(text, cb);
  }
  function svgPoint(svg, evt) {
    const m = svg.getScreenCTM();
    if (!m) return null;
    const pt = svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    return pt.matrixTransform(m.inverse());
  }
  const pathD = (pts) => pts.map((p, i) => `${i ? "L" : "M"}${clamp(p[0], -1e4, 1e4).toFixed(1)},${clamp(p[1], -1e4, 1e4).toFixed(1)}`).join("");

  /** Small line chart in a framed box. */
  function miniChart(s, x0, y0, w, hh, values, { title = "", color = "var(--viz-1)", log = false, xMax = null } = {}) {
    const g = s("g");
    g.append(s("rect", { x: x0, y: y0, width: w, height: hh, rx: 5, fill: "var(--bg-elev)", stroke: "var(--border)" }));
    g.append(txt(s, x0 + 7, y0 + 14, title, { "font-size": 10.5 }));
    const tf = log ? (v) => Math.log10(clamp(v, 1e-12, 1e12)) : (v) => clamp(v, -1e12, 1e12);
    const vals = values.map((v) => (Number.isFinite(v) ? v : 1e12));
    if (!vals.length) return g;
    const tv = vals.map(tf);
    let lo = Math.min(...tv);
    let hi = Math.max(...tv);
    if (!log) lo = Math.min(0, lo);
    if (hi - lo < 1e-9) hi = lo + 1;
    const n = Math.max(xMax ?? vals.length, 2);
    const left = x0 + 8;
    const right = x0 + w - 8;
    const top = y0 + 22;
    const bottom = y0 + hh - 14;
    const px = (i) => left + ((right - left) * i) / (n - 1);
    const py = (v) => bottom - ((bottom - top) * (tf(v) - lo)) / (hi - lo);
    g.append(s("line", { x1: left, y1: bottom, x2: right, y2: bottom, stroke: "var(--border-strong)" }));
    g.append(s("path", { d: pathD(vals.map((v, i) => [px(i), py(v)])), fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round" }));
    const last = vals[vals.length - 1];
    g.append(s("circle", { cx: px(vals.length - 1), cy: py(last), r: 3, fill: color }));
    g.append(txt(s, x0 + w - 7, y0 + 14, fmt(values[values.length - 1]), { "text-anchor": "end", "font-size": 10.5, fill: "var(--fg)", "font-family": "var(--font-mono)" }));
    g.append(txt(s, left, y0 + hh - 3, log ? "log scale" : "", { "font-size": 9, fill: "var(--fg-faint)" }));
    g.append(txt(s, right, y0 + hh - 3, `${vals.length - 1}`, { "font-size": 9, fill: "var(--fg-faint)", "text-anchor": "end" }));
    return g;
  }

  // ---------------------------------------------------------------- event-loop
  registerViz("event-loop", (el, config, api) => {
    const { s } = api;
    const ui = api.shell(el, { title: "Three downloads: sequential vs asyncio vs threads" });
    const TICK = 100;
    const ms = (t) => `${t * TICK} ms`;
    const NAMES = ["download(a)", "download(b)", "download(c)"];
    const COLORS = ["var(--viz-1)", "var(--viz-5)", "var(--viz-6)"];
    const WORK = {
      io: [[["cpu", 1], ["io", 4], ["cpu", 1]], [["cpu", 1], ["io", 3], ["cpu", 1]], [["cpu", 1], ["io", 5], ["cpu", 1]]],
      cpu: [[["cpu", 1], ["io", 1], ["cpu", 4]], [["cpu", 1], ["io", 1], ["cpu", 3]], [["cpu", 1], ["io", 1], ["cpu", 4]]],
    };
    const SWITCH = 2;
    let scenario = ["sequential", "asyncio", "threads"].includes(config.scenario) ? config.scenario : "asyncio";
    let build = config.build === "free-threaded" ? "free-threaded" : "gil";
    let workload = config.workload === "cpu" ? "cpu" : "io";
    let totals = {};

    function simulate(sc, bld, wl) {
      const tasks = WORK[wl].map((ph) => ({ ph, pi: 0, rem: ph[0][1], done: false }));
      const n = tasks.length;
      const kindOf = (tk) => (tk.done ? "done" : tk.ph[tk.pi][0]);
      const advance = (tk) => { tk.pi += 1; if (tk.pi >= tk.ph.length) tk.done = true; else tk.rem = tk.ph[tk.pi][1]; };
      const hist = tasks.map(() => []);
      const thread = [];
      const frames = [];
      let t = 0;
      const snap = (msg, info) => frames.push({ t, hist: hist.map((r) => [...r]), thread: thread.map((c) => [...c]), msg: `<b>t = ${ms(t)}</b> · ${msg}`, info });
      const idx = [0, 1, 2];

      if (sc === "sequential") {
        let cur = 0;
        const info = () => [
          { label: "the one thread", items: cur < n ? [{ i: cur, note: kindOf(tasks[cur]) === "io" ? "blocked on I/O" : "running" }] : [], text: cur >= n ? "(finished)" : "" },
          { label: "not started", items: idx.filter((i) => i > cur).map((i) => ({ i })), text: cur >= n - 1 ? "(none)" : "" },
        ];
        snap("Plain synchronous code: each download runs to completion before the next one starts.", info());
        while (cur < n) {
          const tk = tasks[cur];
          const kind = kindOf(tk);
          const ev = [];
          tasks.forEach((o, i) => hist[i].push(i === cur ? kind : o.done ? "done" : "idle"));
          thread.push([{ i: cur, kind }]);
          tk.rem -= 1;
          t += 1;
          if (tk.rem === 0) {
            const was = cur;
            advance(tk);
            if (tk.done) {
              ev.push(`${NAMES[was]} returns.`);
              cur += 1;
              if (cur < n) ev.push(`Only now does ${NAMES[cur]} start.`);
            } else if (kindOf(tk) === "io") {
              ev.push(`${NAMES[was]} sent its request and calls a blocking socket read: the thread will wait ${ms(tk.rem)} doing nothing.`);
            } else {
              ev.push(`${NAMES[was]}'s response arrived; it parses the body on the CPU.`);
            }
          }
          if (!ev.length) ev.push(kind === "io" ? `The only thread is still blocked on ${NAMES[cur]}'s socket; the other downloads can't even start.` : `${NAMES[cur]} runs Python code.`);
          snap(ev.join(" "), info());
        }
      } else if (sc === "asyncio") {
        const ready = [0, 1, 2];
        const waiting = [];
        let running = null;
        const info = () => [
          { label: "running", items: running === null ? [] : [{ i: running }], text: running === null ? "(loop idle)" : "" },
          { label: "ready queue", items: ready.map((i) => ({ i })), text: ready.length ? "" : "(empty)" },
          { label: "waiting on I/O", items: waiting.map((i) => ({ i, note: `${ms(tasks[i].rem)} left` })), text: waiting.length ? "" : "(none)" },
        ];
        snap("<code>asyncio.gather()</code> wraps the three coroutines in Tasks; all start on the ready queue of one single-threaded event loop.", info());
        while (tasks.some((o) => !o.done)) {
          const ev = [];
          if (running === null && ready.length) { running = ready.shift(); ev.push(`The loop takes ${NAMES[running]} off the ready queue and resumes it.`); }
          tasks.forEach((o, i) => hist[i].push(o.done ? "done" : i === running ? "cpu" : waiting.includes(i) ? "io" : ready.includes(i) ? "ready" : "idle"));
          thread.push(running === null ? [] : [{ i: running, kind: "cpu" }]);
          if (running === null) ev.push("Nothing is ready, so the loop sleeps in <code>select()</code>/<code>epoll</code> until a socket becomes readable. No CPU is wasted.");
          waiting.forEach((i) => { tasks[i].rem -= 1; });
          if (running !== null) tasks[running].rem -= 1;
          t += 1;
          if (running !== null && tasks[running].rem === 0) {
            const i = running;
            advance(tasks[i]);
            running = null;
            if (tasks[i].done) ev.push(`${NAMES[i]} returns; its Task is done.`);
            else if (kindOf(tasks[i]) === "io") { waiting.push(i); ev.push(`${NAMES[i]} reaches <code>await reader.read()</code>: it registers its socket with the loop and yields control.`); }
            else ready.push(i);
          } else if (running !== null) {
            ev.push(`${NAMES[running]} is still doing CPU work and has not reached an <code>await</code>, so no other task can run: CPU-bound code blocks the loop.`);
          }
          for (const i of [...waiting]) {
            if (tasks[i].rem === 0) {
              waiting.splice(waiting.indexOf(i), 1);
              advance(tasks[i]);
              ready.push(i);
              ev.push(`${NAMES[i]}'s socket is readable: the loop moves it back to the ready queue.`);
            }
          }
          snap(ev.join(" "), info());
        }
      } else {
        const free = bld === "free-threaded";
        let holder = null;
        let held = 0;
        let last = -1;
        const needCpu = () => idx.filter((i) => !tasks[i].done && kindOf(tasks[i]) === "cpu");
        const inIo = () => idx.filter((i) => !tasks[i].done && kindOf(tasks[i]) === "io");
        const info = () => (free
          ? [
            { label: "running in parallel", items: needCpu().map((i) => ({ i })), text: needCpu().length ? "" : "(none)" },
            { label: "in blocking I/O", items: inIo().map((i) => ({ i })), text: inIo().length ? "" : "(none)" },
            { label: "GIL", items: [], text: "none: python3.14t (PEP 703, supported per PEP 779)" },
          ]
          : [
            { label: "GIL held by", items: holder === null ? [] : [{ i: holder }], text: holder === null ? "(free)" : "" },
            { label: "waiting for GIL", items: needCpu().filter((i) => i !== holder).map((i) => ({ i })), text: needCpu().filter((i) => i !== holder).length ? "" : "(none)" },
            { label: "in I/O (GIL released)", items: inIo().map((i) => ({ i })), text: inIo().length ? "" : "(none)" },
          ]);
        snap(free
          ? "Free-threaded build (<code>python3.14t</code>): three OS threads and no GIL, so CPU work can run on several cores at once."
          : "Standard build: three OS threads share one GIL. Only the holder may run Python bytecode; blocking I/O releases it.", info());
        while (tasks.some((o) => !o.done)) {
          const ev = [];
          const need = needCpu();
          let runSet;
          if (free) {
            runSet = need;
          } else {
            if (holder !== null && !need.includes(holder)) holder = null;
            if (holder !== null && held >= SWITCH && need.length > 1) {
              const nxt = need.find((i) => i > holder) ?? need[0];
              ev.push(`Switch interval elapsed (<code>sys.getswitchinterval()</code>): T${holder + 1} drops the GIL and T${nxt + 1} takes it.`);
              holder = nxt;
              held = 0;
            }
            if (holder === null && need.length) {
              holder = need.find((i) => i > last) ?? need[0];
              held = 0;
              ev.push(`T${holder + 1} acquires the GIL.`);
            }
            if (holder !== null) last = holder;
            runSet = holder === null ? [] : [holder];
          }
          tasks.forEach((o, i) => hist[i].push(o.done ? "done" : runSet.includes(i) ? "cpu" : kindOf(o) === "io" ? "io" : "gil"));
          thread.push(runSet.map((i) => ({ i, kind: "cpu" })));
          if (!runSet.length) ev.push("Every unfinished thread is waiting on the network; the CPU is idle.");
          if (free && runSet.length > 1) ev.push(`${runSet.length} threads execute Python code at the same instant on different cores.`);
          tasks.forEach((o, i) => { if (!o.done && (runSet.includes(i) || kindOf(o) === "io")) o.rem -= 1; });
          held += 1;
          t += 1;
          tasks.forEach((o, i) => {
            if (o.done || o.rem > 0) return;
            advance(o);
            if (o.done) {
              ev.push(`T${i + 1} finishes${!free && holder === i ? " and releases the GIL" : ""}.`);
              if (holder === i) holder = null;
            } else if (kindOf(o) === "io") {
              ev.push(free ? `T${i + 1} starts a blocking socket read.` : `T${i + 1} starts a blocking socket read and releases the GIL.`);
              if (holder === i) holder = null;
            } else {
              ev.push(free ? `T${i + 1}'s data arrived; it keeps running on its own core.` : `T${i + 1}'s data arrived; it must re-acquire the GIL before running Python again.`);
            }
          });
          snap(ev.join(" "), info());
        }
      }
      frames[frames.length - 1].msg += ` <b>All three finished at ${ms(t)}.</b>`;
      return { frames, total: t };
    }

    const svg = makeSvg(s, 660, 392, "Timeline of three downloads");
    ui.stage.append(svg);
    const W = 660;
    const LBL = 150;
    const X1 = 645;

    function segs(row) {
      const out = [];
      row.forEach((k, i) => {
        const lastSeg = out[out.length - 1];
        if (lastSeg && lastSeg.k === k) lastSeg.e = i + 1;
        else out.push({ k, s: i, e: i + 1 });
      });
      return out;
    }

    function render(frame) {
      clear(svg);
      const maxT = Math.max(...Object.values(totals));
      const cw = (X1 - LBL) / maxT;
      const xAt = (k) => LBL + k * cw;
      const rowLabel = scenario === "threads" ? (build === "gil" ? "GIL holder" : "CPU cores busy") : "main thread";
      svg.append(txt(s, 10, 18, `Scenario: ${scenario}${scenario === "threads" ? (build === "gil" ? " · standard build (GIL)" : " · free-threaded 3.14t") : ""} · ${workload === "io" ? "I/O-bound" : "CPU-heavy"} work`, { "font-size": 12, fill: "var(--fg)", "font-weight": 600 }));
      // thread row
      const ty = 30;
      svg.append(txt(s, 10, ty + 15, rowLabel, { "font-weight": 600 }));
      svg.append(s("rect", { x: LBL, y: ty, width: X1 - LBL, height: 22, fill: "var(--bg-sunk)", rx: 3 }));
      frame.thread.forEach((cell, k) => {
        cell.forEach((c, j) => {
          const hh = 22 / cell.length;
          svg.append(s("rect", { x: xAt(k), y: ty + j * hh, width: cw + 0.3, height: hh, fill: COLORS[c.i], "fill-opacity": c.kind === "io" ? 0.25 : 0.95 }));
        });
      });
      // task rows
      for (let i = 0; i < 3; i++) {
        const y = 66 + i * 34;
        const name = scenario === "threads" ? `T${i + 1} · ${NAMES[i]}` : NAMES[i];
        svg.append(s("rect", { x: 8, y: y + 6, width: 10, height: 10, rx: 2, fill: COLORS[i] }));
        svg.append(txt(s, 24, y + 15, name, { fill: "var(--fg)", "font-family": "var(--font-mono)", "font-size": 10.5 }));
        svg.append(s("line", { x1: LBL, y1: y + 11, x2: X1, y2: y + 11, stroke: "var(--border)" }));
        for (const sg of segs(frame.hist[i])) {
          const x = xAt(sg.s);
          const w = (sg.e - sg.s) * cw;
          let labelText = "";
          if (sg.k === "cpu") {
            svg.append(s("rect", { x, y, width: w, height: 22, rx: 3, fill: COLORS[i] }));
            labelText = "CPU";
          } else if (sg.k === "io") {
            svg.append(s("rect", { x, y, width: w, height: 22, rx: 3, fill: COLORS[i], "fill-opacity": 0.18, stroke: COLORS[i] }));
            labelText = scenario === "sequential" ? "blocked on I/O" : scenario === "asyncio" ? "await I/O" : "blocking I/O";
          } else if (sg.k === "ready" || sg.k === "gil") {
            svg.append(s("rect", { x, y, width: w, height: 22, rx: 3, fill: "var(--viz-2)", "fill-opacity": 0.15, stroke: "var(--viz-2)", "stroke-dasharray": "3 2" }));
            labelText = sg.k === "ready" ? "ready" : "wants GIL";
          } else {
            continue;
          }
          if (w > labelText.length * 5.6 + 6) svg.append(txt(s, x + w / 2, y + 15, labelText, { "text-anchor": "middle", "font-size": 9.5, fill: sg.k === "cpu" ? "var(--bg-elev)" : "var(--fg)" }));
        }
      }
      // axis
      const ay = 170;
      svg.append(s("line", { x1: LBL, y1: ay, x2: X1, y2: ay, stroke: "var(--border-strong)" }));
      const step = maxT > 14 ? 2 : 1;
      for (let k = 0; k <= maxT; k += step) {
        svg.append(s("line", { x1: xAt(k), y1: ay, x2: xAt(k), y2: ay + 4, stroke: "var(--border-strong)" }));
        svg.append(txt(s, xAt(k), ay + 15, `${(k * TICK) / 1000}s`, { "text-anchor": "middle", "font-size": 9, fill: "var(--fg-faint)" }));
      }
      svg.append(s("line", { x1: xAt(frame.t), y1: ty - 4, x2: xAt(frame.t), y2: ay, stroke: "var(--fg)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }));
      // info panel
      frame.info.forEach((row, r) => {
        const y = 200 + r * 24;
        svg.append(txt(s, 10, y + 13, row.label, { "font-weight": 600 }));
        let x = LBL;
        for (const it of row.items) {
          const label = (scenario === "threads" ? `T${it.i + 1}` : NAMES[it.i]) + (it.note ? ` · ${it.note}` : "");
          const w = label.length * 6.1 + 16;
          svg.append(s("rect", { x, y, width: w, height: 18, rx: 9, fill: COLORS[it.i], "fill-opacity": 0.16, stroke: COLORS[it.i] }));
          svg.append(txt(s, x + w / 2, y + 13, label, { "text-anchor": "middle", fill: "var(--fg)", "font-family": "var(--font-mono)", "font-size": 10 }));
          x += w + 6;
        }
        if (row.text) svg.append(txt(s, x, y + 13, row.text, { fill: "var(--fg-faint)" }));
      });
      // totals
      const by = 284;
      svg.append(txt(s, 10, by, "Total elapsed time for the same three downloads", { "font-weight": 600, fill: "var(--fg)" }));
      const rows = [["sequential", "sequential", "gil"], ["asyncio", "asyncio", "gil"], ["threads (GIL)", "threads", "gil"], ["threads (3.14t, no GIL)", "threads", "free-threaded"]];
      rows.forEach(([name, sc, bl], r) => {
        const y = by + 10 + r * 24;
        const key = `${sc}/${bl}`;
        const active = sc === scenario && (sc !== "threads" || bl === build);
        const w = (totals[key] / maxT) * (X1 - LBL - 60);
        svg.append(txt(s, 10, y + 13, name, { fill: active ? "var(--fg)" : "var(--fg-muted)", "font-weight": active ? 700 : 400 }));
        svg.append(s("rect", { x: LBL, y, width: w, height: 17, rx: 3, fill: "var(--accent)", "fill-opacity": active ? 1 : 0.35 }));
        svg.append(txt(s, LBL + w + 6, y + 13, ms(totals[key]), { fill: "var(--fg)", "font-family": "var(--font-mono)", "font-size": 10.5 }));
      });
      ui.setLog(frame.msg);
    }

    const scenSel = api.select([["sequential", "sequential"], ["asyncio", "asyncio"], ["threads", "threads"]], scenario, (v) => { scenario = v; rebuild(); });
    const buildSel = api.select([["gil", "standard build (GIL)"], ["free-threaded", "free-threaded 3.14t"]], build, (v) => { build = v; rebuild(); });
    const workSel = api.select([["io", "I/O-bound downloads"], ["cpu", "CPU-heavy parsing"]], workload, (v) => { workload = v; rebuild(); });
    ui.controls.append(api.label("scenario", scenSel), api.label("build", buildSel), api.label("work", workSel));
    const player = api.player(ui.controls, render);
    ui.setLegend([["running Python (task colour)", "var(--viz-1)"], ["waiting on I/O (faded)", "color-mix(in srgb, var(--viz-1) 22%, transparent)"], ["ready, or waiting for the GIL", "var(--viz-2)"]]);

    function rebuild() {
      totals = {
        "sequential/gil": simulate("sequential", "gil", workload).total,
        "asyncio/gil": simulate("asyncio", "gil", workload).total,
        "threads/gil": simulate("threads", "gil", workload).total,
        "threads/free-threaded": simulate("threads", "free-threaded", workload).total,
      };
      buildSel.disabled = scenario !== "threads";
      player.load(simulate(scenario, build, workload).frames);
    }
    rebuild();
  });

  // ---------------------------------------------------------------- gradient-descent
  registerViz("gradient-descent", (el, config, api) => {
    const { s } = api;
    const FNS = {
      quadratic: {
        dim: 1, label: "f(x) = x²", f: ([x]) => x * x, g: ([x]) => [2 * x], xr: [-3, 3], yr: [-0.6, 9.6], start: [2.6],
        lr: [0.005, 1.2], lr0: 0.1, iters: 30, every: 1, min: [0],
        hint: "each step multiplies x by (1 − 2·lr): it zig-zags past the minimum for lr > 0.5 and diverges for lr > 1",
      },
      bowl: {
        dim: 2, label: "f(x, y) = x² + 5y²", f: ([x, y]) => x * x + 5 * y * y, g: ([x, y]) => [2 * x, 10 * y], xr: [-3, 3], yr: [-2, 2],
        start: [-2.6, 1.6], lr: [0.005, 0.25], lr0: 0.05, iters: 60, every: 1, min: [0, 0], levels: [0.1, 0.3, 0.7, 1.5, 3, 6, 10, 16, 24, 34],
        hint: "the steep y direction diverges first, for lr > 0.2, while the shallow x direction is still crawling",
      },
      rosenbrock: {
        dim: 2, label: "Rosenbrock (1 − x)² + 100(y − x²)²", f: ([x, y]) => (1 - x) ** 2 + 100 * (y - x * x) ** 2,
        g: ([x, y]) => [-2 * (1 - x) - 400 * x * (y - x * x), 200 * (y - x * x)], xr: [-2, 2], yr: [-1, 3], start: [-1.2, 1],
        lr: [0.00005, 0.005], lr0: 0.001, iters: 3000, every: 30, min: [1, 1], levels: [0.05, 0.2, 0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2000],
        hint: "the curved valley is quick to reach but slow to follow; too large a step bounces off the steep walls",
      },
    };
    let fnName = FNS[config.fn] ? config.fn : "quadratic";
    let lr = Number(config.lr) > 0 ? Number(config.lr) : FNS[fnName].lr0;
    let momentum = Boolean(config.momentum);
    let start = [...FNS[fnName].start];
    let run = null;

    const ui = api.shell(el, { title: "Gradient descent: step size, divergence, and momentum" });
    const W = 640;
    const H = 330;
    const PX = 44;
    const PY = 14;
    const PW = 376;
    const PH = 290;
    const svg = makeSvg(s, W, H, "Gradient descent on a loss surface");
    ui.stage.append(svg);
    const clipId = uid("gd-clip");
    const staticG = s("g");
    const dynG = s("g", { "clip-path": `url(#${clipId})` });
    const chartG = s("g");
    svg.append(s("defs", {}, s("clipPath", { id: clipId }, s("rect", { x: PX, y: PY, width: PW, height: PH }))), staticG, dynG, chartG);

    const F = () => FNS[fnName];
    const sx = (x) => PX + ((x - F().xr[0]) / (F().xr[1] - F().xr[0])) * PW;
    const sy = (y) => PY + PH - ((y - F().yr[0]) / (F().yr[1] - F().yr[0])) * PH;
    const ix = (px) => F().xr[0] + ((px - PX) / PW) * (F().xr[1] - F().xr[0]);
    const iy = (py) => F().yr[0] + ((PY + PH - py) / PH) * (F().yr[1] - F().yr[0]);

    function contourPath(vals, nx, ny, level, toPx) {
      let d = "";
      const v = (i, j) => vals[j * nx + i];
      const lerp = (p, q, a, b) => p + ((level - a) / (b - a)) * (q - p);
      for (let j = 0; j < ny - 1; j++) {
        for (let i = 0; i < nx - 1; i++) {
          const a = v(i, j); const b = v(i + 1, j); const c = v(i + 1, j + 1); const dd = v(i, j + 1);
          const A = a > level; const B = b > level; const C = c > level; const D = dd > level;
          const pts = {};
          if (A !== B) pts.T = [lerp(i, i + 1, a, b), j];
          if (B !== C) pts.R = [i + 1, lerp(j, j + 1, b, c)];
          if (C !== D) pts.B = [lerp(i + 1, i, c, dd), j + 1];
          if (D !== A) pts.L = [i, lerp(j + 1, j, dd, a)];
          const keys = Object.keys(pts);
          let pairs = [];
          if (keys.length === 2) pairs = [keys];
          else if (keys.length === 4) {
            const center = (a + b + c + dd) / 4 > level;
            pairs = center === A ? [["T", "R"], ["B", "L"]] : [["L", "T"], ["R", "B"]];
          }
          for (const [p, q] of pairs) {
            const P = toPx(pts[p]); const Q = toPx(pts[q]);
            d += `M${P[0].toFixed(1)},${P[1].toFixed(1)}L${Q[0].toFixed(1)},${Q[1].toFixed(1)}`;
          }
        }
      }
      return d;
    }

    function drawStatic() {
      clear(staticG);
      const fn = F();
      staticG.append(s("rect", { x: PX, y: PY, width: PW, height: PH, fill: "var(--bg-elev)", stroke: "var(--border)" }));
      if (fn.dim === 1) {
        const pts = [];
        for (let k = 0; k <= 200; k++) { const x = fn.xr[0] + ((fn.xr[1] - fn.xr[0]) * k) / 200; pts.push([sx(x), sy(fn.f([x]))]); }
        staticG.append(s("line", { x1: PX, y1: sy(0), x2: PX + PW, y2: sy(0), stroke: "var(--border-strong)" }));
        staticG.append(s("path", { d: pathD(pts), fill: "none", stroke: "var(--viz-1)", "stroke-width": 2.2, "clip-path": `url(#${clipId})` }));
        for (let x = -3; x <= 3; x++) staticG.append(txt(s, sx(x), PY + PH + 13, String(x).replace("-", "−"), { "text-anchor": "middle", "font-size": 9.5, fill: "var(--fg-faint)" }));
        for (const y of [0, 2, 4, 6, 8]) staticG.append(txt(s, PX - 5, sy(y) + 3, String(y), { "text-anchor": "end", "font-size": 9.5, fill: "var(--fg-faint)" }));
      } else {
        const nx = 72; const ny = 56;
        const vals = new Float64Array(nx * ny);
        for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
          vals[j * nx + i] = fn.f([fn.xr[0] + ((fn.xr[1] - fn.xr[0]) * i) / (nx - 1), fn.yr[0] + ((fn.yr[1] - fn.yr[0]) * j) / (ny - 1)]);
        }
        const toPx = ([gi, gj]) => [PX + (gi / (nx - 1)) * PW, PY + PH - (gj / (ny - 1)) * PH];
        fn.levels.forEach((lv, k) => {
          staticG.append(s("path", { d: contourPath(vals, nx, ny, lv, toPx), fill: "none", stroke: "var(--viz-1)", "stroke-opacity": 0.85 - (0.55 * k) / fn.levels.length, "stroke-width": 1.1 }));
        });
        const [mx, my] = fn.min;
        staticG.append(s("path", { d: `M${sx(mx) - 6},${sy(my)}h12M${sx(mx)},${sy(my) - 6}v12`, stroke: "var(--viz-3)", "stroke-width": 2.5 }));
        for (const x of [fn.xr[0], 0, fn.xr[1]]) staticG.append(txt(s, sx(x), PY + PH + 13, String(x).replace("-", "−"), { "text-anchor": "middle", "font-size": 9.5, fill: "var(--fg-faint)" }));
        for (const y of [fn.yr[0], 0, fn.yr[1]]) staticG.append(txt(s, PX - 5, sy(y) + 3, String(y).replace("-", "−"), { "text-anchor": "end", "font-size": 9.5, fill: "var(--fg-faint)" }));
      }
      staticG.append(txt(s, PX + 6, PY + 14, fn.label, { fill: "var(--fg)", "font-size": 11, "font-weight": 600 }));
      staticG.append(txt(s, PX + PW - 6, PY + 14, "click to set the start", { "text-anchor": "end", "font-size": 9.5, fill: "var(--fg-faint)" }));
    }

    function compute() {
      const fn = F();
      let p = [...start];
      let v = p.map(() => 0);
      const beta = momentum ? 0.9 : 0;
      const pts = [[...p]];
      const losses = [fn.f(p)];
      const steps = [];
      const frames = [{ n: 1, msg: `Start at ${fmtV(p)} with loss ${fmt(losses[0])}. Each iteration: ${momentum ? "v ← 0.9·v − lr·∇f(x), x ← x + v" : "x ← x − lr·∇f(x)"} with lr = ${fmt(lr, 5)}.` }];
      let status = "ran";
      for (let k = 1; k <= fn.iters; k++) {
        const g = fn.g(p);
        v = v.map((vi, j) => beta * vi - lr * g[j]);
        p = p.map((pi, j) => pi + v[j]);
        const L = fn.f(p);
        pts.push([...p]);
        losses.push(L);
        steps.push(Math.hypot(...v));
        const diverged = !Number.isFinite(L) || L > 1e4 * Math.max(losses[0], 1) || p.some((c) => !Number.isFinite(c));
        const converged = L < 1e-10;
        if (k <= 5 || k % fn.every === 0 || diverged || converged || k === fn.iters) {
          frames.push({ n: pts.length, msg: `iter ${k}: ∇f = ${fmtV(g)}, step ${momentum ? "v" : "−lr·∇f"} = ${fmtV(v)} → x = ${fmtV(p)}, loss ${fmt(L, 4)}.` });
        }
        if (diverged) { status = "diverged"; break; }
        if (converged) { status = "converged"; break; }
      }
      const lastF = frames[frames.length - 1];
      const n = pts.length - 1;
      if (status === "diverged") lastF.msg += ` <b>Diverged</b> after ${n} iterations: every step overshoots further than the last. lr = ${fmt(lr, 5)} is too large: ${fn.hint}.`;
      else if (status === "converged") lastF.msg += ` <b>Converged</b> to the minimum in ${n} iterations.`;
      else {
        const tail = losses.slice(-100);
        const ups = tail.filter((L, i) => i > 0 && L > tail[i - 1]).length;
        const verdict = losses[n] > losses[0] ? "It got worse: the step is too large."
          : ups > tail.length / 5 ? "The loss keeps going up and down: the step is too large to settle, so it bounces between the valley walls."
            : momentum ? "Momentum carries speed through flat, narrow directions." : "Try momentum, or a different learning rate.";
        lastF.msg += ` <b>After ${n} iterations</b> the loss is ${fmt(losses[n], 4)} (started at ${fmt(losses[0], 4)}). ${verdict}`;
      }
      return { pts, losses, steps, frames, status };
    }

    function render(frame) {
      const fn = F();
      clear(dynG);
      clear(chartG);
      const pts = run.pts.slice(0, frame.n);
      const toPx = fn.dim === 1 ? (p) => [sx(p[0]), sy(fn.f(p))] : (p) => [sx(p[0]), sy(p[1])];
      const px = pts.map(toPx);
      dynG.append(s("path", { d: pathD(px), fill: "none", stroke: "var(--viz-4)", "stroke-width": 1.6, "stroke-opacity": 0.8 }));
      px.forEach((q, i) => {
        if (i === px.length - 1) return;
        dynG.append(s("circle", { cx: clamp(q[0], -1e4, 1e4), cy: clamp(q[1], -1e4, 1e4), r: i === 0 ? 5 : 2.6, fill: i === 0 ? "var(--viz-3)" : "var(--viz-4)", "fill-opacity": i === 0 ? 1 : 0.7 }));
      });
      const cur = pts[pts.length - 1];
      const cq = px[px.length - 1];
      if (fn.dim === 1 && Number.isFinite(cur[0]) && Math.abs(cur[0]) < 10) {
        const slope = fn.g(cur)[0];
        const y0 = fn.f(cur);
        dynG.append(s("line", { x1: sx(cur[0] - 0.7), y1: sy(y0 - 0.7 * slope), x2: sx(cur[0] + 0.7), y2: sy(y0 + 0.7 * slope), stroke: "var(--viz-2)", "stroke-width": 2 }));
      }
      dynG.append(s("circle", { cx: clamp(cq[0], -1e4, 1e4), cy: clamp(cq[1], -1e4, 1e4), r: 6, fill: "var(--viz-4)", stroke: "var(--bg-elev)", "stroke-width": 2 }));
      const losses = run.losses.slice(0, frame.n);
      chartG.append(miniChart(s, 440, PY, 190, 140, losses, { title: "loss per iteration", color: "var(--viz-4)", log: true }));
      chartG.append(miniChart(s, 440, PY + 152, 190, 124, run.steps.slice(0, frame.n - 1).length ? run.steps.slice(0, frame.n - 1) : [0], { title: "step length |Δx|", color: "var(--viz-2)", log: true }));
      chartG.append(txt(s, 440, PY + PH + 13, `lr ${fmt(lr, 5)} · momentum ${momentum ? "0.9" : "off"} · ${run.status}`, { "font-size": 10, fill: run.status === "diverged" ? "var(--bad)" : "var(--fg-muted)" }));
      ui.setLog(frame.msg);
    }

    const fnSel = api.select([["quadratic", "1-D quadratic"], ["bowl", "2-D bowl"], ["rosenbrock", "2-D Rosenbrock"]], fnName, (v) => {
      fnName = v;
      lr = F().lr0;
      start = [...F().start];
      syncSlider();
      drawStatic();
      rebuild(0);
    });
    const slider = api.h("input", { type: "range", min: 0, max: 1000, value: 500, "aria-label": "Learning rate" });
    const lrOut = api.h("span", { class: "status", style: "font-family:var(--font-mono);min-width:5em" });
    const lrFromSlider = () => { const [lo, hi] = F().lr; return lo * (hi / lo) ** (Number(slider.value) / 1000); };
    function syncSlider() {
      const [lo, hi] = F().lr;
      lr = clamp(lr, lo, hi);
      slider.value = String(Math.round((1000 * Math.log(lr / lo)) / Math.log(hi / lo)));
      lrOut.textContent = fmt(lr, 5);
    }
    slider.addEventListener("input", () => { lr = Number(lrFromSlider().toPrecision(3)); lrOut.textContent = fmt(lr, 5); rebuild("end"); });
    const mom = checkbox(api, "momentum", momentum, (v) => { momentum = v; rebuild("end"); });
    const resetStart = api.button("reset start", () => { start = [...F().start]; rebuild(0); });
    ui.controls.append(api.label("function", fnSel), api.label("learning rate", slider), lrOut, mom, resetStart);
    const player = api.player(ui.controls, render, { speed: 300 });
    ui.setLegend([["start", "var(--viz-3)"], ["iterates", "var(--viz-4)"], ["tangent (gradient)", "var(--viz-2)"], ["contours of the loss", "var(--viz-1)"]]);

    function rebuild(at) {
      run = compute();
      player.load(run.frames, at === "end" ? run.frames.length - 1 : 0);
    }
    svg.addEventListener("click", (e) => {
      const p = svgPoint(svg, e);
      if (!p || p.x < PX || p.x > PX + PW || p.y < PY || p.y > PY + PH) return;
      start = F().dim === 1 ? [Number(ix(p.x).toFixed(2))] : [Number(ix(p.x).toFixed(2)), Number(iy(p.y).toFixed(2))];
      rebuild("end");
    });
    svg.style.cursor = "crosshair";
    syncSlider();
    drawStatic();
    rebuild(0);
  });

  // ---------------------------------------------------------------- kmeans
  registerViz("kmeans", (el, config, api) => {
    const { s } = api;
    const COL = ["var(--viz-1)", "var(--viz-2)", "var(--viz-3)", "var(--viz-4)", "var(--viz-5)", "var(--viz-6)"];
    let k = clamp(Math.round(Number(config.k)) || 3, 2, 6);
    let init = config.init === "kmeans++" || config.init === "k-means++" ? "kmeans++" : "random";
    let dataSeed = 20261014;
    let initSeed = 3;
    let runs = [];

    function normalize(raw) {
      const pts = raw.filter((p) => Array.isArray(p) && p.length >= 2 && p.every(Number.isFinite)).map((p) => [Number(p[0]), Number(p[1])]);
      if (pts.length < 3) return null;
      const xs = pts.map((p) => p[0]); const ys = pts.map((p) => p[1]);
      const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      return pts.map(([x, y]) => [5 + (90 * (x - x0)) / (x1 - x0 || 1), 5 + (90 * (y - y0)) / (y1 - y0 || 1)]);
    }
    const custom = Array.isArray(config.points) ? normalize(config.points) : null;

    function genPoints(seed) {
      const r = mulberry32(seed);
      const centers = [];
      for (let tries = 0; centers.length < 4 && tries < 200; tries++) {
        const c = [15 + r() * 70, 15 + r() * 70];
        if (centers.every((o) => Math.hypot(o[0] - c[0], o[1] - c[1]) > 26)) centers.push(c);
      }
      const pts = [];
      centers.forEach((c) => {
        const n = 16 + Math.floor(r() * 14);
        const sd = 4 + r() * 5;
        for (let i = 0; i < n; i++) pts.push([clamp(c[0] + gauss(r) * sd, 1, 99), clamp(c[1] + gauss(r) * sd, 1, 99)]);
      });
      return pts;
    }
    let points = custom || genPoints(dataSeed);

    const d2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
    const nearest = (p, cents) => { let best = 0; let bd = Infinity; cents.forEach((c, j) => { const d = d2(p, c); if (d < bd) { bd = d; best = j; } }); return best; };

    function compute() {
      const r = mulberry32(initSeed * 7919 + k);
      const frames = [{ cents: null, assign: null, inertias: [], msg: `${points.length} points, k = ${k}. k-means alternates two steps: <b>assign</b> each point to its nearest centroid, then <b>update</b> each centroid to the mean of its points.` }];
      let cents = [];
      if (init === "random") {
        const picks = new Set();
        while (picks.size < Math.min(k, points.length)) picks.add(Math.floor(r() * points.length));
        cents = [...picks].map((i) => [...points[i]]);
        frames.push({ cents: cents.map((c) => [...c]), assign: null, inertias: [], msg: `Random init (Forgy): ${k} data points picked uniformly at random become the starting centroids (seed ${initSeed}). A bad pick can put two centroids in one blob.` });
      } else {
        cents.push([...points[Math.floor(r() * points.length)]]);
        frames.push({ cents: cents.map((c) => [...c]), assign: null, inertias: [], msg: "k-means++: the first centroid is a uniformly random point." });
        while (cents.length < k) {
          const D = points.map((p) => Math.min(...cents.map((c) => d2(p, c))));
          const total = D.reduce((a, b) => a + b, 0);
          frames.push({ cents: cents.map((c) => [...c]), assign: null, weights: D.map((x) => x / total), inertias: [], msg: `k-means++: the next centroid is sampled with probability ∝ D(x)², the squared distance to the nearest chosen centroid. Larger dots are likelier picks.` });
          let u = r() * total;
          let pick = 0;
          for (; pick < D.length - 1; pick++) { u -= D[pick]; if (u <= 0) break; }
          cents.push([...points[pick]]);
          frames.push({ cents: cents.map((c) => [...c]), assign: null, inertias: [], msg: `k-means++ picked point ${pick} as centroid ${cents.length} (it had a ${(100 * D[pick] / total).toFixed(1)}% chance).` });
        }
      }
      let assign = null;
      const inertias = [];
      let it = 0;
      for (it = 1; it <= 40; it++) {
        const next = points.map((p) => nearest(p, cents));
        const changed = assign ? next.filter((a, i) => a !== assign[i]).length : points.length;
        assign = next;
        const inertia = points.reduce((acc, p, i) => acc + d2(p, cents[assign[i]]), 0);
        inertias.push(inertia);
        if (changed === 0) {
          frames.push({ cents: cents.map((c) => [...c]), assign: [...assign], inertias: [...inertias], msg: `Iteration ${it} · assign: no point changed cluster, so the algorithm has <b>converged</b>. Final inertia ${fmt(inertia, 1)}. This is a local optimum, not necessarily the best one: press <b>Re-seed</b> to start elsewhere.` });
          break;
        }
        frames.push({ cents: cents.map((c) => [...c]), assign: [...assign], inertias: [...inertias], msg: `Iteration ${it} · assign: every point joins its nearest centroid (${changed} changed). Inertia (sum of squared distances to centroids) = ${fmt(inertia, 1)}.` });
        const prev = cents.map((c) => [...c]);
        cents = cents.map((c, j) => {
          const mine = points.filter((_, i) => assign[i] === j);
          return mine.length ? [mine.reduce((a, p) => a + p[0], 0) / mine.length, mine.reduce((a, p) => a + p[1], 0) / mine.length] : c;
        });
        const shift = Math.max(...cents.map((c, j) => Math.sqrt(d2(c, prev[j]))));
        frames.push({ cents: cents.map((c) => [...c]), prev, assign: [...assign], inertias: [...inertias], msg: `Iteration ${it} · update: each centroid moves to the mean of its cluster (largest move ${fmt(shift, 2)}). Inertia can only go down or stay the same.` });
      }
      return { frames, final: inertias[inertias.length - 1] };
    }

    const ui = api.shell(el, { title: "k-means clustering, step by step" });
    const svg = makeSvg(s, 640, 330, "k-means clustering scatter plot");
    ui.stage.append(svg);
    const PX = 10; const PY = 10; const PW = 360; const PH = 310;
    const tx = (x) => PX + (x / 100) * PW;
    const ty = (y) => PY + PH - (y / 100) * PH;

    function render(frame) {
      clear(svg);
      svg.append(s("rect", { x: PX, y: PY, width: PW, height: PH, fill: "var(--bg-elev)", stroke: "var(--border)" }));
      if (frame.cents) {
        const cell = 10;
        for (let gx = 0; gx < PW / cell; gx++) {
          for (let gy = 0; gy < Math.ceil(PH / cell); gy++) {
            const hh = Math.min(cell, PH - gy * cell);
            const c = nearest([((gx + 0.5) * cell * 100) / PW, 100 - ((gy * cell + hh / 2) * 100) / PH], frame.cents);
            svg.append(s("rect", { x: PX + gx * cell, y: PY + gy * cell, width: cell, height: hh, fill: COL[c], "fill-opacity": 0.1 }));
          }
        }
      }
      const maxW = frame.weights ? Math.max(...frame.weights) : 1;
      points.forEach((p, i) => {
        const a = frame.assign ? frame.assign[i] : null;
        const rad = frame.weights ? 2 + 7 * Math.sqrt(frame.weights[i] / maxW) : 4;
        svg.append(s("circle", { cx: tx(p[0]), cy: ty(p[1]), r: rad, fill: a === null ? "var(--viz-node)" : COL[a], stroke: a === null ? "var(--fg-muted)" : "var(--bg-elev)", "stroke-width": 1 }));
      });
      if (frame.prev) {
        frame.prev.forEach((c, j) => {
          svg.append(s("circle", { cx: tx(c[0]), cy: ty(c[1]), r: 7, fill: "none", stroke: COL[j], "stroke-dasharray": "3 2", "stroke-width": 1.5 }));
          svg.append(s("line", { x1: tx(c[0]), y1: ty(c[1]), x2: tx(frame.cents[j][0]), y2: ty(frame.cents[j][1]), stroke: "var(--fg)", "stroke-width": 1.4 }));
        });
      }
      (frame.cents || []).forEach((c, j) => {
        const x = tx(c[0]); const y = ty(c[1]);
        svg.append(s("path", { d: `M${x},${y - 10}L${x + 10},${y}L${x},${y + 10}L${x - 10},${y}Z`, fill: COL[j], stroke: "var(--fg)", "stroke-width": 2 }));
      });
      svg.append(miniChart(s, 390, PY, 240, 150, frame.inertias.length ? frame.inertias : [0], { title: "inertia per iteration", color: "var(--accent)" }));
      svg.append(txt(s, 390, 186, "Final inertia per seed (lower is better):", { fill: "var(--fg)", "font-weight": 600 }));
      const best = Math.min(...runs.map((rr) => rr.final));
      runs.slice(-6).forEach((rr, j) => {
        const isBest = rr.final === best && runs.length > 1;
        svg.append(txt(s, 396, 206 + j * 18, `seed ${rr.seed} · ${rr.init}: ${fmt(rr.final, 1)}${isBest ? "  ← best" : ""}`, { "font-family": "var(--font-mono)", "font-size": 10.5, fill: isBest ? "var(--ok)" : "var(--fg-muted)" }));
      });
      ui.setLog(frame.msg);
    }

    const kSel = api.select([2, 3, 4, 5, 6].map((n) => [String(n), `k = ${n}`]), String(k), (v) => { k = Number(v); runs = []; rebuild(); });
    const initSel = api.select([["random", "random init"], ["kmeans++", "k-means++ init"]], init, (v) => { init = v; rebuild(); });
    const reseed = api.button("Re-seed", () => { initSeed = (initSeed % 997) + 1 + Math.floor(Math.random() * 50); rebuild(true); });
    const newData = api.button("New data", () => { dataSeed = newSeed(); points = genPoints(dataSeed); runs = []; rebuild(); });
    if (custom) newData.disabled = true;
    ui.controls.append(kSel, initSel, reseed, newData);
    const player = api.player(ui.controls, render, { speed: 600 });
    ui.setLegend([["centroid", "var(--fg)"], ["unassigned point", "var(--viz-node)"], ["background: nearest-centroid region", "color-mix(in srgb, var(--viz-1) 25%, transparent)"]]);

    function rebuild(autoplay = false) {
      const res = compute();
      runs.push({ seed: initSeed, init: init === "random" ? "random" : "k-means++", final: res.final });
      player.load(res.frames);
      if (autoplay) player.toggle();
    }
    rebuild();
  });

  // ---------------------------------------------------------------- neural-net
  registerViz("neural-net", (el, config, api) => {
    const { s } = api;
    const XOR = [[[0, 0], 0], [[0, 1], 1], [[1, 0], 1], [[1, 1], 0]];
    let layers = Array.isArray(config.layers) && config.layers.length >= 2 && config.layers.every((n) => Number(n) >= 1)
      ? config.layers.slice(0, 6).map((n) => clamp(Math.round(Number(n)), 1, 8))
      : [2, 3, 1];
    let mode = config.mode === "train" ? "train" : "forward";
    let seed = 7;
    let lr = 1;
    let inputIdx = 3;
    let trained = false;
    const sig = (z) => 1 / (1 + Math.exp(-z));

    function makeNet(L, sd) {
      const r = mulberry32(sd);
      const W = []; const b = [];
      for (let l = 0; l < L.length - 1; l++) {
        const lim = Math.sqrt(6 / (L[l] + L[l + 1]));
        W.push(Array.from({ length: L[l + 1] }, () => Array.from({ length: L[l] }, () => (r() * 2 - 1) * lim)));
        b.push(Array.from({ length: L[l + 1] }, () => (r() * 2 - 1) * 0.1));
      }
      return { L: [...L], W, b };
    }
    const clone = (net) => ({ L: [...net.L], W: net.W.map((m) => m.map((row) => [...row])), b: net.b.map((v) => [...v]) });
    function forward(net, x) {
      const a = [x]; const z = [];
      net.W.forEach((m, l) => {
        const zl = m.map((row, j) => row.reduce((acc, w, i) => acc + w * a[l][i], net.b[l][j]));
        z.push(zl);
        a.push(zl.map((v) => (l === net.W.length - 1 ? sig(v) : Math.tanh(v))));
      });
      return { a, z };
    }
    function trainStep(net, rate) {
      const gW = net.W.map((m) => m.map((row) => row.map(() => 0)));
      const gb = net.b.map((v) => v.map(() => 0));
      let loss = 0;
      for (const [x, y] of XOR) {
        const { a } = forward(net, x);
        const L = net.W.length;
        const out = a[L][0];
        loss += -(y * Math.log(out + 1e-12) + (1 - y) * Math.log(1 - out + 1e-12));
        let delta = [out - y];
        for (let l = L - 1; l >= 0; l--) {
          delta.forEach((dj, j) => { gb[l][j] += dj; a[l].forEach((ai, i) => { gW[l][j][i] += dj * ai; }); });
          if (l > 0) {
            const d = delta;
            delta = a[l].map((ai, i) => net.W[l].reduce((acc, row, j) => acc + row[i] * d[j], 0) * (1 - ai * ai));
          }
        }
      }
      net.W.forEach((m, l) => m.forEach((row, j) => row.forEach((_, i) => { row[i] -= (rate * gW[l][j][i]) / XOR.length; })));
      net.b.forEach((v, l) => v.forEach((_, j) => { v[j] -= (rate * gb[l][j]) / XOR.length; }));
      return loss / XOR.length;
    }
    let net = makeNet(layers, seed);
    const xorShaped = () => layers[0] === 2 && layers[layers.length - 1] === 1;

    function trainFrames() {
      let note = "";
      if (!xorShaped()) {
        const hidden = layers.slice(1, -1);
        layers = [2, ...(hidden.length ? hidden : [3]), 1];
        note = ` XOR has 2 inputs and 1 output, so the net was reshaped to [${layers.join(", ")}].`;
      }
      const work = makeNet(layers, seed);
      const losses = [];
      const preds = (nn) => XOR.map(([x]) => forward(nn, x).a[nn.L.length - 1][0]);
      const describe = (nn) => XOR.map(([x], i) => `${x.join("")}→${preds(nn)[i].toFixed(2)}`).join(" ");
      const frames = [{ net: clone(work), losses: [], epoch: 0, msg: `Training on XOR with full-batch gradient descent, lr ${lr}. Hidden layers use tanh, the output uses a sigmoid, and the loss is binary cross-entropy. Backpropagation applies the chain rule layer by layer to get every weight's gradient.${note} Predictions: ${describe(work)}.` }];
      const EPOCHS = 3000; const EVERY = 60;
      for (let e = 1; e <= EPOCHS; e++) {
        losses.push(trainStep(work, lr));
        if (e % EVERY === 0 || e === 1) frames.push({ net: clone(work), losses: [...losses], epoch: e, msg: `epoch ${e}: mean loss ${fmt(losses[losses.length - 1], 4)}. Predictions ${describe(work)}.` });
      }
      const ok = preds(work).every((p, i) => (p > 0.5) === (XOR[i][1] === 1));
      frames[frames.length - 1].msg += ok
        ? " <b>Solved XOR.</b> No single straight line separates XOR; the hidden layer bends the decision boundary so it can."
        : " <b>Not solved</b>: training stalled in a poor region. Press <b>Re-init weights</b> or change the learning rate.";
      net = clone(work);
      trained = true;
      return frames;
    }

    function forwardFrames() {
      const r = mulberry32(seed + 101);
      const x = layers[0] === 2 ? [...XOR[inputIdx][0]] : Array.from({ length: layers[0] }, () => Number(r().toFixed(2)));
      const { a, z } = forward(net, x);
      const frames = [{ upto: 0, a, msg: `Input layer: x = ${fmtV(x)}. ${trained ? "Using the weights learned in training." : "Weights are random (untrained)."} Edge thickness is |w|; blue is positive, red is negative.` }];
      for (let l = 1; l < net.L.length; l++) {
        const act = l === net.L.length - 1 ? "σ" : "tanh";
        const row = net.W[l - 1][0];
        const terms = row.slice(0, 4).map((w, i) => `${fmt(w, 2)}·${a[l - 1][i] < 0 ? `(${fmt(a[l - 1][i], 2)})` : fmt(a[l - 1][i], 2)}`).join(" + ") + (row.length > 4 ? " + …" : "");
        frames.push({ upto: l, a, msg: `Layer ${l}: each neuron computes z = Σ wᵢ·aᵢ + b, then a = ${act}(z). Neuron 1: z = ${terms} + ${fmt(net.b[l - 1][0], 2)} = ${fmt(z[l - 1][0], 3)}, a = ${act}(z) = ${fmt(a[l][0], 3)}.` });
      }
      const out = a[a.length - 1];
      let tail = ` Output = ${fmtV(out)}.`;
      if (xorShaped() && layers[0] === 2) {
        const target = XOR[inputIdx][1];
        tail += ` XOR target is ${target}: the net says ${out[0] > 0.5 ? 1 : 0} (${(out[0] > 0.5) === (target === 1) ? "correct" : "wrong"}).${trained ? "" : " Switch to training mode to learn the weights."}`;
      }
      frames[frames.length - 1].msg += tail;
      return frames;
    }

    const ui = api.shell(el, { title: "Feed-forward neural network" });
    const svg = makeSvg(s, 640, 330, "Neural network diagram");
    ui.stage.append(svg);

    function drawNet(nn, netW, frame) {
      const H = 300;
      const nL = nn.L.length;
      const maxN = Math.max(...nn.L);
      const gap = Math.min(52, (H - 50) / maxN);
      const rad = clamp(gap / 2.6, 7, 15);
      const pos = (l, i) => [30 + rad + (l * (netW - 60 - 2 * rad)) / (nL - 1), 24 + (H - 48) / 2 + (i - (nn.L[l] - 1) / 2) * gap];
      const maxAbs = Math.max(1e-6, ...nn.W.flat(2).map(Math.abs));
      nn.W.forEach((m, l) => m.forEach((row, j) => row.forEach((w, i) => {
        const [x1, y1] = pos(l, i); const [x2, y2] = pos(l + 1, j);
        let op = 0.8;
        if (frame.upto !== undefined) op = frame.upto === l + 1 ? 0.95 : frame.upto > l + 1 ? 0.35 : 0.12;
        svg.append(s("line", { x1, y1, x2, y2, stroke: w >= 0 ? "var(--viz-1)" : "var(--viz-4)", "stroke-width": 0.5 + (4.5 * Math.abs(w)) / maxAbs, "stroke-opacity": op }, s("title", { text: `w = ${fmt(w, 3)}` })));
      })));
      nn.L.forEach((n, l) => {
        for (let i = 0; i < n; i++) {
          const [x, y] = pos(l, i);
          const shown = frame.a && frame.upto !== undefined && l <= frame.upto;
          const v = shown ? frame.a[l][i] : null;
          const active = frame.upto === l;
          svg.append(s("circle", { cx: x, cy: y, r: rad, fill: "var(--viz-node)", stroke: active ? "var(--viz-active)" : "var(--fg-muted)", "stroke-width": active ? 3 : 1.2 }));
          if (v !== null) {
            svg.append(s("circle", { cx: x, cy: y, r: rad - 1.5, fill: v >= 0 ? "var(--viz-1)" : "var(--viz-4)", "fill-opacity": 0.1 + 0.75 * Math.min(1, Math.abs(v)) }));
            svg.append(txt(s, x, y + 3.5, v.toFixed(2), { "text-anchor": "middle", "font-size": rad > 11 ? 9.5 : 8, fill: "var(--fg)", stroke: "var(--bg-elev)", "stroke-width": 2.5, "paint-order": "stroke", "font-family": "var(--font-mono)" }));
          }
        }
        const lbl = l === 0 ? "input" : l === nL - 1 ? "output (σ)" : `hidden ${l} (tanh)`;
        svg.append(txt(s, pos(l, 0)[0], H + 16, lbl, { "text-anchor": "middle", "font-size": 10 }));
      });
    }

    function render(frame) {
      clear(svg);
      if (mode === "forward") {
        drawNet(net, 640, frame);
      } else {
        const nn = frame.net;
        drawNet(nn, 350, {});
        const HX = 380; const HY = 22; const HS = 200; const N = 20;
        const lo = -0.25; const span = 1.5;
        svg.append(txt(s, HX, HY - 8, "decision boundary: P(y = 1 | x)", { fill: "var(--fg)", "font-weight": 600, "font-size": 10.5 }));
        for (let gi = 0; gi < N; gi++) {
          for (let gj = 0; gj < N; gj++) {
            const x = [lo + ((gi + 0.5) * span) / N, lo + ((gj + 0.5) * span) / N];
            const p = forward(nn, x).a[nn.L.length - 1][0];
            svg.append(s("rect", { x: HX + (gi * HS) / N, y: HY + HS - ((gj + 1) * HS) / N, width: HS / N + 0.3, height: HS / N + 0.3, fill: p >= 0.5 ? "var(--viz-1)" : "var(--viz-4)", "fill-opacity": 0.08 + 0.7 * Math.abs(p - 0.5) * 2 }));
          }
        }
        svg.append(s("rect", { x: HX, y: HY, width: HS, height: HS, fill: "none", stroke: "var(--border-strong)" }));
        const hx = (v) => HX + ((v - lo) / span) * HS;
        const hy = (v) => HY + HS - ((v - lo) / span) * HS;
        XOR.forEach(([[a, b], y]) => {
          svg.append(s("circle", { cx: hx(a), cy: hy(b), r: 7, fill: y ? "var(--viz-1)" : "var(--viz-4)", stroke: "var(--fg)", "stroke-width": 2 }));
          svg.append(txt(s, hx(a) + (a ? -12 : 12), hy(b) + 4, `(${a},${b})→${y}`, { "text-anchor": a ? "end" : "start", "font-size": 9.5, fill: "var(--fg)", stroke: "var(--bg-elev)", "stroke-width": 2.5, "paint-order": "stroke" }));
        });
        svg.append(txt(s, HX + HS / 2, HY + HS + 13, "x₁", { "text-anchor": "middle", "font-size": 10 }));
        svg.append(txt(s, HX - 6, HY + HS / 2, "x₂", { "text-anchor": "end", "font-size": 10 }));
        svg.append(txt(s, HX + HS + 8, HY + 20, `epoch ${frame.epoch}`, { "font-family": "var(--font-mono)", "font-size": 10.5, fill: "var(--fg)" }));
        svg.append(miniChart(s, HX, HY + HS + 22, 250, 84, frame.losses.length ? frame.losses : [0], { title: "training loss (BCE)", color: "var(--viz-4)", log: true, xMax: 3000 }));
      }
      ui.setLog(frame.msg);
    }

    const modeSel = api.select([["forward", "forward pass"], ["train", "train on XOR"]], mode, (v) => { mode = v; rebuild(); });
    const inSel = api.select(XOR.map(([x], i) => [String(i), `x = (${x.join(", ")})`]), String(inputIdx), (v) => { inputIdx = Number(v); rebuild(); });
    const lrSel = api.select([["0.1", "lr 0.1"], ["0.5", "lr 0.5"], ["1", "lr 1"], ["2", "lr 2"], ["5", "lr 5"]], String(lr), (v) => { lr = Number(v); rebuild(); });
    const reinit = api.button("Re-init weights", () => { seed = newSeed(); net = makeNet(layers, seed); trained = false; rebuild(); });
    ui.controls.append(modeSel, inSel, lrSel, reinit);
    const player = api.player(ui.controls, render, { speed: 400 });
    ui.setLegend([["positive weight / activation", "var(--viz-1)"], ["negative weight / activation", "var(--viz-4)"], ["layer being computed", "var(--viz-active)"]]);

    function rebuild() {
      inSel.style.display = mode === "forward" && layers[0] === 2 ? "" : "none";
      lrSel.style.display = mode === "train" ? "" : "none";
      player.load(mode === "train" ? trainFrames() : forwardFrames());
    }
    rebuild();
  });

  // ---------------------------------------------------------------- pipeline
  registerViz("pipeline", (el, config, api) => {
    const { s, esc } = api;
    const stages = Array.isArray(config.stages) && config.stages.length ? config.stages.slice(0, 7).map(String) : ["extract", "validate", "transform", "load"];
    const S = stages.length;
    let vIdx = stages.findIndex((n) => /valid|check|clean/i.test(n));
    if (vIdx < 0) vIdx = Math.min(1, S - 1);
    const RECORDS = Array.from({ length: 12 }, (_, i) => ({ id: 101 + i, bad: null }));
    RECORDS[2].bad = "email is missing";
    RECORDS[6].bad = "amount is negative";
    RECORDS[10].bad = "date '2026-13-40' does not parse";
    const byId = new Map(RECORDS.map((r) => [r.id, r]));
    const nValid = RECORDS.filter((r) => !r.bad).length;
    let mode = config.mode === "batch" ? "batch" : "streaming";
    let write = config.write === "append" ? "append" : "upsert";
    let runs = 1;
    const RUNCOL = ["var(--viz-1)", "var(--viz-2)", "var(--viz-5)", "var(--viz-6)"];
    const verb = (name) => (/extract|read|ingest/i.test(name) ? "reads" : /valid|check|clean/i.test(name) ? "checks" : /load|write|sink/i.test(name) ? "writes" : "processes");

    function applyWrite(rows, id, run) {
      if (write === "append") {
        rows.push({ id, run });
        return rows.filter((r) => r.id === id).length > 1 ? "duplicate" : "inserted";
      }
      const existing = rows.find((r) => r.id === id);
      if (existing) { existing.run = run; return "updated"; }
      rows.push({ id, run });
      return "inserted";
    }

    function simulate() {
      const rows = [];
      for (let q = 1; q < runs; q++) RECORDS.filter((r) => !r.bad).forEach((r) => applyWrite(rows, r.id, q));
      const queues = stages.map(() => []);
      queues[0] = RECORDS.map((r) => r.id);
      const counters = stages.map(() => ({ in: 0, out: 0, fail: 0 }));
      counters[0].in = RECORDS.length;
      const dlq = [];
      const validated = new Set();
      const tally = { inserted: 0, updated: 0, duplicate: 0 };
      let t = 0;
      let first = null;
      const frames = [];
      const snap = (processing, msg) => {
        frames.push({ t, queues: queues.map((q) => [...q]), processing: [...processing], dlq: [...dlq], rows: rows.map((r) => ({ ...r })), counters: counters.map((c) => ({ ...c })), validated: new Set(validated), msg });
        return frames[frames.length - 1];
      };
      const prior = runs > 1 ? ` The target already holds ${rows.length} rows from ${runs - 1} earlier run${runs > 2 ? "s" : ""}.` : "";
      snap(stages.map(() => null), `Run #${runs}: 12 source records, ${mode} mode, ${write === "upsert" ? "upsert (insert or update by id)" : "append (plain INSERT)"} into the target.${prior} ${mode === "batch" ? "Batch: each stage processes the whole batch before the next stage starts." : "Streaming: every record moves on as soon as a stage is done with it, so all stages work at once."}`);
      while (queues.some((q) => q.length)) {
        const emptyAtStart = queues.map((q) => q.length === 0);
        const processing = stages.map((_, st) => {
          const enabled = mode === "streaming" || emptyAtStart.slice(0, st).every(Boolean);
          return enabled && queues[st].length ? queues[st].shift() : null;
        });
        t += 1;
        const frame = snap(processing, "");
        const ev = [];
        processing.forEach((id, st) => {
          if (id === null) return;
          const rec = byId.get(id);
          const name = esc(stages[st]);
          if (st === vIdx && rec.bad) {
            dlq.push(id);
            counters[st].fail += 1;
            ev.push(`<b>${name}</b> rejects ${id} (${rec.bad}) → dead-letter queue`);
            return;
          }
          if (st === vIdx) validated.add(id);
          counters[st].out += 1;
          if (st === S - 1) {
            const res = applyWrite(rows, id, runs);
            tally[res] += 1;
            if (first === null) first = t;
            ev.push(`<b>${name}</b> ${write === "append" ? "INSERTs" : "upserts"} ${id}: ${res === "duplicate" ? "<b>duplicate row!</b>" : res}`);
          } else {
            queues[st + 1].push(id);
            counters[st + 1].in += 1;
            ev.push(`<b>${name}</b> ${verb(stages[st])} ${id}`);
          }
        });
        if (mode === "batch") {
          const waiting = stages.findIndex((_, st) => st > 0 && queues[st].length && processing[st] === null);
          if (waiting > 0) ev.push(`(${esc(stages[waiting])} waits for the whole batch)`);
        }
        frame.msg = `<b>tick ${t}</b> · ${ev.join(" · ")}`;
      }
      const distinct = new Set(rows.map((r) => r.id)).size;
      let verdict = "";
      if (runs > 1 && write === "append") verdict = ` Re-running with append created <b>${rows.length - distinct} duplicate rows</b>: the load is not idempotent.`;
      else if (runs > 1) verdict = ` Upsert made the re-run <b>idempotent</b>: the same input gives the same table (${tally.updated} rows updated, ${tally.inserted} inserted).`;
      snap(stages.map(() => null), `<b>Run #${runs} done</b> in ${t} ticks (${mode}). The first row reached the target at tick ${first}. ${nValid} loaded, ${dlq.length} parked in the dead-letter queue for inspection. Target: ${rows.length} rows, ${distinct} distinct ids.${verdict}${runs === 1 ? " Press <b>Re-run</b> to run the same input again." : ""}`);
      return frames;
    }

    const ui = api.shell(el, { title: `ETL pipeline: ${stages.join(" → ")}` });
    const W = 680; const H = 330;
    const svg = makeSvg(s, W, H, "Data pipeline");
    ui.stage.append(svg);
    const colW = (W - 20) / (S + 1);
    const boxX = (c) => 10 + c * colW + 4;
    const boxW = colW - 26;

    function dot(x, y, id, fr, extra = {}) {
      const rec = byId.get(id);
      const failed = fr.dlq.includes(id);
      const fill = failed ? "var(--viz-4)" : fr.validated.has(id) ? "var(--viz-1)" : "var(--viz-node)";
      return s("circle", { cx: x, cy: y, r: 5, fill, stroke: fill === "var(--viz-node)" ? "var(--fg-muted)" : "var(--bg-elev)", "stroke-width": 1, ...extra }, s("title", { text: `record ${id}${rec.bad && failed ? ` (${rec.bad})` : ""}` }));
    }

    function render(fr) {
      clear(svg);
      const cols = Math.max(2, Math.min(4, Math.floor((boxW - 8) / 13)));
      stages.forEach((name, st) => {
        const x = boxX(st);
        const busy = fr.processing[st] !== null;
        svg.append(txt(s, x + boxW / 2, 30, name, { "text-anchor": "middle", fill: "var(--fg)", "font-weight": 600 }));
        svg.append(s("rect", { x, y: 40, width: boxW, height: 130, rx: 7, fill: "var(--bg-elev)", stroke: busy ? "var(--viz-active)" : "var(--border-strong)", "stroke-width": busy ? 2.5 : 1 }));
        svg.append(txt(s, x + 6, 53, st === 0 ? "source" : "queue", { "font-size": 9, fill: "var(--fg-faint)" }));
        fr.queues[st].forEach((id, i) => svg.append(dot(x + 11 + (i % cols) * 13, 64 + Math.floor(i / cols) * 13, id, fr)));
        svg.append(s("line", { x1: x + 6, y1: 112, x2: x + boxW - 6, y2: 112, stroke: "var(--border)", "stroke-dasharray": "3 3" }));
        svg.append(txt(s, x + 6, 124, "working on", { "font-size": 9, fill: "var(--fg-faint)" }));
        if (busy) {
          const id = fr.processing[st];
          svg.append(dot(x + boxW / 2, 145, id, fr, { r: 9, stroke: "var(--viz-active)", "stroke-width": 3 }));
          svg.append(txt(s, x + boxW / 2 + 13, 149, String(id), { "font-size": 9.5, fill: "var(--fg)", "font-family": "var(--font-mono)" }));
        }
        const c = fr.counters[st];
        svg.append(txt(s, x + boxW / 2, 188, `in ${c.in} · out ${c.out}`, { "text-anchor": "middle", "font-family": "var(--font-mono)", "font-size": 10 }));
        if (st === vIdx) svg.append(txt(s, x + boxW / 2, 202, `failed ${c.fail}`, { "text-anchor": "middle", "font-family": "var(--font-mono)", "font-size": 10, fill: "var(--bad)" }));
        const ax = x + boxW + 3;
        svg.append(s("path", { d: `M${ax},105h${colW - boxW - 12}`, stroke: "var(--fg-faint)", "stroke-width": 1.5 }));
        svg.append(s("path", { d: `M${ax + colW - boxW - 12},101l6,4l-6,4z`, fill: "var(--fg-faint)" }));
      });
      // dead-letter queue
      const dx = boxX(vIdx);
      svg.append(s("path", { d: `M${dx + boxW / 2},208v12`, stroke: "var(--bad)", "stroke-width": 1.5, "stroke-dasharray": "3 2" }));
      svg.append(s("rect", { x: dx, y: 222, width: boxW, height: 70, rx: 7, fill: "var(--bad-soft)", stroke: "var(--bad)" }));
      svg.append(txt(s, dx + boxW / 2, 236, "dead-letter queue", { "text-anchor": "middle", "font-size": 9.5, fill: "var(--bad)", "font-weight": 600 }));
      fr.dlq.forEach((id, i) => {
        svg.append(dot(dx + 14 + (i % cols) * 13, 252 + Math.floor(i / cols) * 14, id, fr));
      });
      if (fr.dlq.length) svg.append(txt(s, dx + 6, 285, fr.dlq.join(", "), { "font-size": 8.5, fill: "var(--fg-muted)", "font-family": "var(--font-mono)" }));
      // target
      const tx = boxX(S);
      const tw = colW - 14;
      svg.append(txt(s, tx + tw / 2, 30, "target table", { "text-anchor": "middle", fill: "var(--fg)", "font-weight": 600 }));
      svg.append(s("rect", { x: tx, y: 40, width: tw, height: 252, rx: 7, fill: "var(--bg-elev)", stroke: "var(--border-strong)" }));
      const counts = new Map();
      fr.rows.forEach((r) => counts.set(r.id, (counts.get(r.id) || 0) + 1));
      const tcols = 3;
      const cellW = (tw - 12) / tcols;
      const cellH = fr.rows.length > 36 ? 9 : 14;
      fr.rows.forEach((r, i) => {
        const x = tx + 6 + (i % tcols) * cellW;
        const y = 48 + Math.floor(i / tcols) * (cellH + 2);
        const dup = counts.get(r.id) > 1;
        svg.append(s("rect", { x, y, width: cellW - 3, height: cellH, rx: 2, fill: RUNCOL[(r.run - 1) % RUNCOL.length], "fill-opacity": 0.3, stroke: dup ? "var(--bad)" : "none", "stroke-width": 1.5 }, s("title", { text: `id ${r.id}, written by run #${r.run}${dup ? " (duplicate)" : ""}` })));
        if (cellH >= 12) svg.append(txt(s, x + (cellW - 3) / 2, y + 10.5, String(r.id), { "text-anchor": "middle", "font-size": 9, fill: "var(--fg)", "font-family": "var(--font-mono)" }));
      });
      const distinct = counts.size;
      svg.append(txt(s, tx + tw / 2, 306, `rows ${fr.rows.length} · distinct ids ${distinct}`, { "text-anchor": "middle", "font-family": "var(--font-mono)", "font-size": 10 }));
      if (fr.rows.length > distinct) svg.append(txt(s, tx + tw / 2, 320, `${fr.rows.length - distinct} duplicates`, { "text-anchor": "middle", "font-size": 10, fill: "var(--bad)", "font-weight": 600 }));
      svg.append(txt(s, 10, 318, `run #${runs} · ${mode} · ${write}`, { "font-size": 10, fill: "var(--fg-faint)" }));
      ui.setLog(fr.msg);
    }

    const modeSel = api.select([["streaming", "streaming"], ["batch", "batch"]], mode, (v) => { mode = v; rebuild(); });
    const writeSel = api.select([["upsert", "upsert by id (idempotent)"], ["append", "append (INSERT)"]], write, (v) => { write = v; rebuild(); });
    const rerun = api.button("Re-run same input", () => { runs = Math.min(4, runs + 1); rebuild(true); });
    const reset = api.button("Reset target", () => { runs = 1; rebuild(); });
    ui.controls.append(api.label("mode", modeSel), api.label("load", writeSel), rerun, reset);
    const player = api.player(ui.controls, render, { speed: 400 });
    ui.setLegend([["not yet validated", "var(--viz-node)"], ["passed validation", "var(--viz-1)"], ["failed → dead-letter queue", "var(--viz-4)"], ["row from run #2", "var(--viz-2)"], ["being processed", "var(--viz-active)"]]);

    function rebuild(autoplay = false) {
      rerun.disabled = runs >= 4;
      player.load(simulate());
      if (autoplay) player.toggle();
    }
    rebuild();
  });
})();
