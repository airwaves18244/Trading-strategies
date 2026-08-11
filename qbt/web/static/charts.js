/* qbt chart rendering — QCH API (frozen contract: docs/ui-upgrade.md §3).
 *
 * ECharts only (static/vendor/echarts.min.js, global `echarts`), plain ES2020,
 * classic script. One instance in #chart-main, reused via setOption(opt, true).
 *
 * All colors are read from the CSS custom properties of §4 at render time —
 * nothing is cached, so a theme flip between calls is picked up on the next
 * render (re-rendering on toggle is WS-D's job).
 *
 * Contract-ambiguity decisions (per the "section owner decides + documents"
 * rule in docs/ui-upgrade.md):
 *  - §3 says to read vars off document.documentElement, but §4 puts the light
 *    theme on `body.light`. Custom properties inherit, so we read the computed
 *    style of document.body first (sees both :root definitions and body.light
 *    overrides) and fall back to documentElement, then to the dark defaults
 *    below when a var is empty (the shell may be mid-rewrite).
 *  - equity(): log y-axis silently falls back to linear when any plotted value
 *    is <= 0 (log axis cannot represent them).
 *  - monthly(): the YEAR total column is visually separated from Dec by an
 *    empty spacer category; the diverging color range is symmetric around 0
 *    and sized from the MONTH cells only, so yearly totals saturate at the
 *    palette ends instead of washing out month-level contrast. Cell labels are
 *    percent points with 1 decimal, no "%" suffix (tooltip carries the full
 *    "x.x%"); null cells are simply not emitted, which leaves them blank.
 *  - exposure(): `short` is plotted as a negative line regardless of the sign
 *    convention upstream (the engine stores it positive).
 */
"use strict";

/* ---------------------------------------------------------------- theme -- */

const QCH_FALLBACK = {
  "--bg": "#0d1117", "--panel": "#161b22", "--panel2": "#010409",
  "--border": "#21262d", "--text": "#c9d1d9", "--muted": "#8b949e",
  "--accent": "#58a6ff", "--pos": "#3fb950", "--neg": "#f85149",
  "--warn": "#d29922", "--bench": "#d29922", "--grid": "#161b22",
  "--s1": "#58a6ff", "--s2": "#3fb950", "--s3": "#d29922",
  "--s4": "#bc8cff", "--s5": "#39c5cf", "--s6": "#f778ba",
};

function qchVar(name) {
  let v = "";
  try {
    if (document.body) v = getComputedStyle(document.body).getPropertyValue(name).trim();
    if (!v) v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  } catch (e) { v = ""; }
  return v || QCH_FALLBACK[name] || "#8b949e";
}

function qchTheme() {
  return {
    bg: qchVar("--bg"), panel: qchVar("--panel"), panel2: qchVar("--panel2"),
    border: qchVar("--border"), text: qchVar("--text"), muted: qchVar("--muted"),
    accent: qchVar("--accent"), pos: qchVar("--pos"), neg: qchVar("--neg"),
    warn: qchVar("--warn"), bench: qchVar("--bench"), grid: qchVar("--grid"),
    s: ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6"].map(n => qchVar(n)),
  };
}

/* Add alpha to a css color (#rgb / #rrggbb / rgb()/rgba()); other formats are
 * returned untouched (opaque). */
function qchAlpha(color, alpha) {
  const c = String(color || "").trim();
  let m = c.match(/^#([0-9a-fA-F]{6})$/);
  if (m) {
    const n = parseInt(m[1], 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }
  m = c.match(/^#([0-9a-fA-F]{3})$/);
  if (m) {
    const h = m[1];
    return "rgba(" + parseInt(h[0] + h[0], 16) + "," + parseInt(h[1] + h[1], 16) + ","
      + parseInt(h[2] + h[2], 16) + "," + alpha + ")";
  }
  m = c.match(/^rgba?\(([^)]+)\)$/i);
  if (m) {
    let parts = m[1].split(",").map(s => s.trim());
    if (parts.length < 3) parts = m[1].split(/[\s/]+/).filter(Boolean);
    if (parts.length >= 3) return "rgba(" + parts[0] + "," + parts[1] + "," + parts[2] + "," + alpha + ")";
  }
  return c;
}

/* ------------------------------------------------------------ formatting -- */

function qchPct1(v) { return (v == null || !isFinite(v)) ? "—" : (v * 100).toFixed(1) + "%"; }
function qchNum2(v) { return (v == null || !isFinite(v)) ? "—" : (+v).toFixed(2); }

/* percents 1 decimal, ratios 2 decimals — per contract */
function qchFmtMetric(metric, v) {
  if (v == null || !isFinite(v)) return "—";
  return (metric === "cagr" || metric === "max_dd") ? qchPct1(v) : qchNum2(v);
}

function qchFmtDate(ms) {
  if (ms == null || !isFinite(+ms)) return "";
  const d = new Date(+ms);
  return isNaN(d.getTime()) ? "" : d.toISOString().slice(0, 10);
}

/* trades carry `ts` as a datetime string (ledger) or unix seconds; return "YYYY-MM-DD" */
function qchTradeDay(ts) {
  if (ts == null) return null;
  if (typeof ts === "number" && isFinite(ts)) return qchFmtDate(ts > 1e12 ? ts : ts * 1000);
  const s = String(ts);
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/);
  if (m) return m[1];
  const d = new Date(s.replace(" ", "T"));
  return isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
}

function qchFmtVol(v) {
  if (v == null || !isFinite(v)) return "";
  const a = Math.abs(v);
  if (a >= 1e9) return (v / 1e9).toFixed(1) + "B";
  if (a >= 1e6) return (v / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return (v / 1e3).toFixed(0) + "k";
  return String(Math.round(v));
}

/* ------------------------------------------------------------ axis bits -- */

function qchTimeAxis(C, extra) {
  return Object.assign({
    type: "time",
    axisLine: { lineStyle: { color: C.border } },
    axisLabel: { color: C.muted },
    splitLine: { show: false },
  }, extra || {});
}

function qchValAxis(C, extra) {
  return Object.assign({
    type: "value", scale: true,
    axisLine: { show: false },
    axisLabel: { color: C.muted },
    splitLine: { lineStyle: { color: C.grid } },
  }, extra || {});
}

function qchCatAxis(C, data, extra) {
  return Object.assign({
    type: "category", data,
    axisLine: { lineStyle: { color: C.border } },
    axisTick: { show: false },
    axisLabel: { color: C.muted },
    nameTextStyle: { color: C.muted },
  }, extra || {});
}

/* ------------------------------------------------------------------ QCH -- */

const QCH = {
  inst: null,
  _resizeBound: false,

  el() { return document.getElementById("chart-main"); },

  get() {
    if (this.inst) return this.inst;
    const el = this.el();
    if (!el || typeof echarts === "undefined") return null;
    this.inst = echarts.init(el, null, { renderer: "canvas" });
    if (!this._resizeBound) {
      window.addEventListener("resize", () => { if (this.inst) this.inst.resize(); });
      this._resizeBound = true;
    }
    return this.inst;
  },

  render(opt) {
    const c = this.get();
    if (!c) return;
    try { c.setOption(opt, true); }
    catch (e) { console.error("QCH render:", e); }
  },

  dispose() {
    if (this.inst) { this.inst.dispose(); this.inst = null; }
  },

  /* [{time: unixSec, value}] -> [[ms, value|null]] */
  ts(series) {
    if (!Array.isArray(series)) return [];
    return series
      .filter(p => p && p.time != null)
      .map(p => [p.time * 1000, (p.value == null || !isFinite(p.value)) ? null : +p.value]);
  },

  base(C) {
    return {
      backgroundColor: "transparent",
      animation: false,
      textStyle: { color: C.muted, fontSize: 11 },
      grid: { left: 60, right: 20, top: 30, bottom: 45 },
      tooltip: {
        trigger: "axis",
        backgroundColor: C.panel, borderColor: C.border,
        textStyle: { color: C.text, fontSize: 11 },
      },
      dataZoom: [
        { type: "inside" },
        { type: "slider", height: 16, bottom: 8, borderColor: C.border,
          backgroundColor: C.bg, fillerColor: qchAlpha(C.accent, 0.12),
          handleStyle: { color: C.muted }, textStyle: { color: C.muted } },
      ],
    };
  },

  /* --------------------------------------------------------------------- */
  /* equity: net + optional gross dashed + benchmark, drawdown band on a
   * secondary right axis (0 pinned at the top of its own scale). */
  equity(result, opts) {
    const r = result || {}, o = opts || {};
    const C = qchTheme();
    const opt = this.base(C);

    const net = this.ts(r.equity);
    const gross = o.gross ? this.ts(r.equity_gross) : [];
    const bench = r.benchmark ? this.ts(r.benchmark) : [];
    const dd = this.ts(r.drawdown);

    let useLog = o.log === true;
    if (useLog) {
      // log axis breaks on values <= 0 — fall back to linear
      const bad = [net, gross, bench].some(a => a.some(p => p[1] != null && p[1] <= 0));
      if (bad) useLog = false;
    }

    opt.legend = { top: 0, textStyle: { color: C.muted }, inactiveColor: C.border };
    opt.grid.top = 36;
    opt.xAxis = qchTimeAxis(C);
    opt.yAxis = [
      useLog
        ? { type: "log", axisLine: { show: false }, axisLabel: { color: C.muted },
            splitLine: { lineStyle: { color: C.grid } } }
        : qchValAxis(C),
      { type: "value", position: "right", max: 0,
        // stretch the dd scale ~3x so the red band hugs the top of the chart
        min: v => (isFinite(v.min) && v.min < 0 ? v.min * 3 : -0.1),
        axisLine: { show: false }, splitLine: { show: false },
        axisLabel: { color: C.muted, formatter: v => (v * 100).toFixed(0) + "%" } },
    ];

    opt.series = [
      { name: "net", type: "line", showSymbol: false, data: net, z: 4,
        color: C.accent, lineStyle: { width: 1.6, color: C.accent } },
    ];
    if (gross.length) opt.series.push(
      { name: "gross", type: "line", showSymbol: false, data: gross, z: 3,
        color: C.muted, lineStyle: { width: 1, color: C.muted, type: "dashed" } });
    if (bench.length) opt.series.push(
      { name: "benchmark", type: "line", showSymbol: false, data: bench, z: 3,
        color: C.bench, lineStyle: { width: 1, color: C.bench } });
    opt.series.push(
      { name: "drawdown", type: "line", showSymbol: false, data: dd, z: 1,
        yAxisIndex: 1, silent: true, color: C.neg,
        lineStyle: { width: 0.8, color: C.neg, opacity: 0.6 },
        areaStyle: { color: qchAlpha(C.neg, 0.15) } });

    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const out = [qchFmtDate(list[0].value && list[0].value[0])];
      for (const p of list) {
        const v = p.value && p.value[1];
        out.push(p.marker + " " + p.seriesName + ": "
          + (p.seriesName === "drawdown" ? qchPct1(v) : qchNum2(v)));
      }
      return out.join("<br>");
    };
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* drawdown: underwater area; top-5 result.drawdowns shaded via markArea
   * with depth labels. */
  drawdown(result) {
    const r = result || {};
    const C = qchTheme();
    const opt = this.base(C);
    const dd = this.ts(r.drawdown);

    opt.xAxis = qchTimeAxis(C);
    opt.yAxis = qchValAxis(C, {
      max: 0,
      axisLabel: { color: C.muted, formatter: v => (v * 100).toFixed(0) + "%" },
    });

    const tops = Array.isArray(r.drawdowns) ? r.drawdowns.slice(0, 5) : [];
    const lastMs = dd.length ? dd[dd.length - 1][0] : Date.now();
    const areas = [];
    for (const d of tops) {
      if (!d || !d.start) continue;
      const a = Date.parse(d.start);
      const b = d.end ? Date.parse(d.end) : lastMs; // unrecovered: extend to the last point
      if (!isFinite(a) || !isFinite(b)) continue;
      areas.push([{ xAxis: a, name: qchPct1(d.depth) }, { xAxis: b }]);
    }

    const s = {
      name: "drawdown", type: "line", showSymbol: false, data: dd,
      color: C.neg, lineStyle: { width: 1, color: C.neg },
      areaStyle: { color: qchAlpha(C.neg, 0.25) },
    };
    if (areas.length) s.markArea = {
      silent: true,
      itemStyle: { color: qchAlpha(C.neg, 0.10) },
      label: { show: true, color: C.text, fontSize: 10, position: "insideTop" },
      data: areas,
    };
    opt.series = [s];

    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const p = list[0];
      return qchFmtDate(p.value && p.value[0]) + "<br>"
        + p.marker + " drawdown: " + qchPct1(p.value && p.value[1]);
    };
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* monthly: heatmap of calendar returns; rows = years (newest on top),
   * cols = Jan..Dec + spacer + YEAR total. No dataZoom. */
  monthly(result) {
    const m = (result && result.monthly) || {};
    const C = qchTheme();
    const opt = this.base(C);
    const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const YEAR_X = 13;                       // col 12 is a blank spacer
    const cols = MONTHS.concat(["", "YEAR"]);

    // sort ascending: category y-axis grows upward, so newest year lands on top
    const years = Array.isArray(m.years) ? m.years : [];
    const order = years.map((_, i) => i).sort((a, b) => (+years[a] || 0) - (+years[b] || 0));
    const yLabels = order.map(i => String(years[i]));

    const data = [];
    const monthAbs = [];
    order.forEach((src, yi) => {
      const row = (Array.isArray(m.cells) && Array.isArray(m.cells[src])) ? m.cells[src] : [];
      for (let mi = 0; mi < 12; mi++) {
        const v = row[mi];
        if (v == null || !isFinite(v)) continue;  // null cell -> blank
        data.push([mi, yi, +v]);
        monthAbs.push(Math.abs(+v));
      }
      const t = Array.isArray(m.totals) ? m.totals[src] : null;
      if (t != null && isFinite(t)) data.push([YEAR_X, yi, +t]);
    });

    // symmetric range centered at 0, from month cells (totals clamp to ends)
    let amp = monthAbs.length ? Math.max.apply(null, monthAbs) : 0;
    if (!(amp > 0)) amp = 0.01;

    opt.grid = { left: 60, right: 20, top: 20, bottom: 30 };
    opt.dataZoom = [];
    opt.xAxis = qchCatAxis(C, cols);
    opt.yAxis = qchCatAxis(C, yLabels);
    opt.visualMap = {
      show: false, min: -amp, max: amp,
      inRange: { color: [C.neg, C.panel, C.pos] },
    };
    opt.tooltip = {
      trigger: "item",
      backgroundColor: C.panel, borderColor: C.border,
      textStyle: { color: C.text, fontSize: 11 },
      formatter: pt => {
        const v = pt.value || [];
        const lab = v[0] === YEAR_X ? "total" : (cols[v[0]] || "");
        return (yLabels[v[1]] || "") + " " + lab + ": " + qchPct1(v[2]);
      },
    };
    opt.series = [{
      type: "heatmap", data,
      label: { show: true, color: C.text, fontSize: 10,
               formatter: pt => (pt.value[2] * 100).toFixed(1) },
      itemStyle: { borderColor: C.bg, borderWidth: 1 },
      emphasis: { itemStyle: { borderColor: C.accent } },
    }];
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* rolling: which in "sharpe"|"vol"|"beta"; zero line for sharpe/beta;
   * vol axis in %. */
  rolling(result, which) {
    const w = (which === "vol" || which === "beta") ? which : "sharpe";
    const roll = (result && result.rolling) || {};
    const tsArr = Array.isArray(roll.ts) ? roll.ts : [];
    const vals = Array.isArray(roll[w]) ? roll[w] : [];
    const isVol = w === "vol";
    const C = qchTheme();
    const opt = this.base(C);

    const data = tsArr
      .filter(t => t != null && isFinite(t))
      .map((t, i) => [t * 1000, (vals[i] == null || !isFinite(vals[i])) ? null : +vals[i]]);

    opt.xAxis = qchTimeAxis(C);
    opt.yAxis = qchValAxis(C, isVol
      ? { axisLabel: { color: C.muted, formatter: v => (v * 100).toFixed(0) + "%" } }
      : {});

    const s = {
      name: "rolling " + w, type: "line", showSymbol: false, data,
      color: C.accent, lineStyle: { width: 1.4, color: C.accent },
    };
    if (isVol) {
      s.areaStyle = { color: qchAlpha(C.accent, 0.10) };
    } else {
      s.markLine = {
        silent: true, symbol: "none",
        lineStyle: { color: C.muted, type: "dashed", width: 1 },
        label: { color: C.muted, formatter: "0" },
        data: [{ yAxis: 0 }],
      };
    }
    opt.series = [s];

    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const p = list[0];
      const v = p.value && p.value[1];
      return qchFmtDate(p.value && p.value[0]) + "<br>"
        + p.marker + " " + p.seriesName + ": " + (isVol ? qchPct1(v) : qchNum2(v));
    };
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* exposure: gross/net/long/short lines (short negative), n_positions as a
   * step line on the right axis; colors from --s1..--s6. */
  exposure(result) {
    const ex = (result && result.exposure) || {};
    const C = qchTheme();
    const opt = this.base(C);

    const shortData = (Array.isArray(ex.short) ? ex.short : [])
      .filter(p => p && p.time != null)
      .map(p => [p.time * 1000,
                 (p.value == null || !isFinite(p.value)) ? null : -Math.abs(+p.value)]);

    const line = (name, series, color) => ({
      name, type: "line", showSymbol: false, data: this.ts(series),
      color, lineStyle: { width: 1.2, color },
    });

    opt.legend = { top: 0, textStyle: { color: C.muted }, inactiveColor: C.border };
    opt.grid.top = 36;
    opt.xAxis = qchTimeAxis(C);
    opt.yAxis = [
      qchValAxis(C, { axisLabel: { color: C.muted, formatter: v => (v * 100).toFixed(0) + "%" } }),
      { type: "value", position: "right", min: 0,
        axisLine: { show: false }, splitLine: { show: false },
        axisLabel: { color: C.muted, formatter: v => String(Math.round(v)) } },
    ];
    const shortLine = line("short", null, C.s[3]);
    shortLine.data = shortData;
    opt.series = [
      line("gross", ex.gross, C.s[0]),
      line("net", ex.net, C.s[1]),
      line("long", ex.long, C.s[2]),
      shortLine,
      { name: "n_positions", type: "line", step: "end", showSymbol: false,
        yAxisIndex: 1, data: this.ts(ex.n_positions),
        color: C.s[4], lineStyle: { width: 1, color: C.s[4], type: "dotted" } },
    ];

    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const out = [qchFmtDate(list[0].value && list[0].value[0])];
      for (const p of list) {
        const v = p.value && p.value[1];
        out.push(p.marker + " " + p.seriesName + ": "
          + (p.seriesName === "n_positions"
             ? (v == null ? "—" : String(Math.round(v)))
             : qchPct1(v)));
      }
      return out.join("<br>");
    };
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* candles: candlestick + volume sub-grid (shared zoom / linked pointer);
   * trade markers with qty/price/pnl/reason tooltip. */
  candles(bars, trades, symbol) {
    const B = Array.isArray(bars) ? bars.filter(b => b && b.time != null) : [];
    let T = Array.isArray(trades) ? trades.filter(t => t) : [];
    if (symbol) T = T.filter(t => t.symbol == null || t.symbol === symbol);
    const C = qchTheme();

    const dates = B.map(b => qchFmtDate(b.time * 1000));
    const kdata = B.map(b => [b.open, b.close, b.low, b.high]);
    const vdata = B.map(b => ({
      value: (b.volume == null || !isFinite(b.volume)) ? 0 : +b.volume,
      itemStyle: { color: qchAlpha(b.close >= b.open ? C.pos : C.neg, 0.5) },
    }));

    let lo = Infinity, hi = -Infinity;
    for (const b of B) {
      if (b.low != null && isFinite(b.low)) lo = Math.min(lo, +b.low);
      if (b.high != null && isFinite(b.high)) hi = Math.max(hi, +b.high);
    }
    const pad = (isFinite(lo) && isFinite(hi)) ? ((hi - lo) * 0.04 || Math.abs(hi) * 0.01 || 1) : 1;

    const idxByDate = new Map();
    dates.forEach((d, i) => { if (d && !idxByDate.has(d)) idxByDate.set(d, i); });

    const marks = [];
    for (const t of T) {
      const day = qchTradeDay(t.ts != null ? t.ts : t.time);
      const i = day != null ? idxByDate.get(day) : undefined;
      if (i === undefined) continue;
      const b = B[i];
      if (!b || b.low == null || b.high == null) continue;
      const buy = +t.side > 0;
      marks.push({
        value: [i, buy ? +b.low - pad : +b.high + pad],
        symbol: "triangle", symbolRotate: buy ? 0 : 180, symbolSize: 9,
        itemStyle: { color: buy ? C.pos : C.neg, borderColor: C.bg, borderWidth: 0.5 },
        trade: t,
      });
    }

    const opt = this.base(C);
    if (symbol) opt.title = {
      text: String(symbol), left: 6, top: 2,
      textStyle: { color: C.muted, fontSize: 11, fontWeight: "normal" },
    };
    opt.axisPointer = { link: [{ xAxisIndex: "all" }], label: { backgroundColor: C.panel2 } };
    opt.grid = [
      { left: 60, right: 20, top: 26, height: "58%" },
      { left: 60, right: 20, top: "70%", height: "16%" },
    ];
    opt.xAxis = [
      qchCatAxis(C, dates, { gridIndex: 0, boundaryGap: true, axisLabel: { show: false } }),
      qchCatAxis(C, dates, { gridIndex: 1, boundaryGap: true }),
    ];
    opt.yAxis = [
      { type: "value", scale: true, gridIndex: 0, axisLine: { show: false },
        axisLabel: { color: C.muted }, splitLine: { lineStyle: { color: C.grid } } },
      { type: "value", gridIndex: 1, splitNumber: 2, axisLine: { show: false },
        axisLabel: { color: C.muted, formatter: v => qchFmtVol(v) },
        splitLine: { show: false } },
    ];
    opt.dataZoom = [
      { type: "inside", xAxisIndex: [0, 1] },
      { type: "slider", xAxisIndex: [0, 1], height: 16, bottom: 8,
        borderColor: C.border, backgroundColor: C.bg,
        fillerColor: qchAlpha(C.accent, 0.12), handleStyle: { color: C.muted },
        textStyle: { color: C.muted } },
    ];
    opt.series = [
      { name: "price", type: "candlestick", data: kdata, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: C.pos, color0: C.neg, borderColor: C.pos, borderColor0: C.neg } },
      { name: "volume", type: "bar", data: vdata, xAxisIndex: 1, yAxisIndex: 1, silent: true },
      { name: "trades", type: "scatter", data: marks, xAxisIndex: 0, yAxisIndex: 0, z: 10 },
    ];
    opt.tooltip.axisPointer = { type: "cross" };
    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const cp = list.find(p => p.seriesType === "candlestick" || p.seriesType === "bar");
      const i = cp ? cp.dataIndex : (list[0].data && list[0].data.value ? list[0].data.value[0] : null);
      const b = (i != null) ? B[i] : null;
      const out = [];
      if (b) {
        out.push(qchFmtDate(b.time * 1000));
        out.push("O " + qchNum2(b.open) + "  H " + qchNum2(b.high)
               + "  L " + qchNum2(b.low) + "  C " + qchNum2(b.close));
        if (b.volume != null) out.push("vol " + qchFmtVol(b.volume));
      }
      if (i != null) {
        for (const mk of marks) {
          if (mk.value[0] !== i) continue;
          const t = mk.trade || {};
          out.push((+t.side > 0 ? "BUY " : "SELL ")
            + (t.qty != null ? t.qty : "—")
            + " @ " + (t.price != null ? t.price : "—")
            + " · pnl " + (t.pnl != null ? qchNum2(t.pnl) : "—")
            + (t.reason ? " · " + t.reason : ""));
        }
      }
      return out.join("<br>");
    };
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* heatmap: 2-param sweep heatmap; p2 null -> line of metric vs p1 with
   * point labels. metric in {sharpe, sharpe_is, sharpe_oos, cagr, max_dd,
   * turnover_ann}. No dataZoom. */
  heatmap(rows, p1, p2, metric) {
    const R = Array.isArray(rows) ? rows.filter(r => r) : [];
    const C = qchTheme();
    const opt = this.base(C);
    opt.dataZoom = [];
    const val = r => {
      const v = r ? r[metric] : null;
      return (v == null || !isFinite(v)) ? null : +v;
    };
    const cmp = (a, b) => (typeof a === "number" && typeof b === "number")
      ? a - b : String(a).localeCompare(String(b));

    if (p2 == null || p2 === "") {
      // 1-param sweep: line of metric vs p1 with point labels
      const pts = R.slice().sort((a, b) => cmp(a[p1], b[p1]));
      const xs = pts.map(r => String(r[p1]));
      opt.xAxis = qchCatAxis(C, xs, {
        name: String(p1 || ""), nameLocation: "middle", nameGap: 28,
      });
      opt.yAxis = qchValAxis(C, {
        axisLabel: { color: C.muted, formatter: v => qchFmtMetric(metric, v) },
      });
      opt.series = [{
        type: "line", data: pts.map(val), showSymbol: true, symbolSize: 6,
        color: C.accent, lineStyle: { width: 1.5, color: C.accent },
        connectNulls: false,
        label: { show: pts.length <= 40, color: C.text, fontSize: 10,
                 position: "top", formatter: pt => qchFmtMetric(metric, pt.value) },
      }];
      opt.tooltip.formatter = params => {
        const list = Array.isArray(params) ? params : [params];
        if (!list.length) return "";
        const p = list[0];
        return String(p1) + " = " + (xs[p.dataIndex] || "") + "<br>"
          + String(metric) + ": " + qchFmtMetric(metric, p.value);
      };
      this.render(opt);
      return;
    }

    const xs = [...new Set(R.map(r => r[p1]))].sort(cmp);
    const ys = [...new Set(R.map(r => r[p2]))].sort(cmp);
    const data = [];
    const vals = [];
    for (const r of R) {
      const v = val(r);
      if (v == null) continue;                 // null metric -> blank cell
      data.push([xs.indexOf(r[p1]), ys.indexOf(r[p2]), v]);
      vals.push(v);
    }
    const lo = vals.length ? Math.min.apply(null, vals) : 0;
    const hi = vals.length ? Math.max.apply(null, vals) : 1;

    opt.grid.bottom = 60;
    opt.xAxis = qchCatAxis(C, xs.map(String), { name: String(p1 || "") });
    opt.yAxis = qchCatAxis(C, ys.map(String), { name: String(p2 || "") });
    opt.visualMap = {
      min: lo, max: hi > lo ? hi : lo + 1e-9,
      calculable: true, orient: "horizontal", left: "center", bottom: 0,
      textStyle: { color: C.muted },
      inRange: { color: [C.neg, C.panel, C.pos] },
    };
    opt.tooltip = {
      trigger: "item",
      backgroundColor: C.panel, borderColor: C.border,
      textStyle: { color: C.text, fontSize: 11 },
      formatter: pt => {
        const v = pt.value || [];
        return String(p1) + " = " + xs[v[0]] + ", " + String(p2) + " = " + ys[v[1]]
          + "<br>" + String(metric) + ": " + qchFmtMetric(metric, v[2]);
      },
    };
    opt.series = [{
      type: "heatmap", data,
      label: { show: data.length <= 80, color: C.text, fontSize: 10,
               formatter: pt => qchFmtMetric(metric, pt.value[2]) },
      itemStyle: { borderColor: C.bg, borderWidth: 1 },
      emphasis: { itemStyle: { borderColor: C.accent } },
    }];
    this.render(opt);
  },

  /* --------------------------------------------------------------------- */
  /* compare: each equity normalized to 1.0 at its first (finite, nonzero)
   * point; legend of labels; colors cycle --s1..--s6. */
  compare(items) {
    const arr = Array.isArray(items) ? items : [];
    const C = qchTheme();
    const opt = this.base(C);

    opt.legend = { top: 0, type: "scroll", textStyle: { color: C.muted },
                   inactiveColor: C.border, pageTextStyle: { color: C.muted } };
    opt.grid.top = 36;
    opt.xAxis = qchTimeAxis(C);
    opt.yAxis = qchValAxis(C, { axisLabel: { color: C.muted, formatter: v => qchNum2(v) } });

    opt.series = arr.map((it, i) => {
      const eq = (it && Array.isArray(it.equity)) ? it.equity : [];
      let baseV = null;
      for (const p of eq) {
        const v = p && p.value;
        if (v != null && isFinite(v) && v !== 0) { baseV = +v; break; }
      }
      const data = eq
        .filter(p => p && p.time != null)
        .map(p => [p.time * 1000,
                   (p.value == null || !isFinite(p.value) || baseV == null)
                     ? null : +p.value / baseV]);
      const color = C.s[i % C.s.length];
      return { name: (it && it.label) ? String(it.label) : "run " + (i + 1),
               type: "line", showSymbol: false, data, color,
               lineStyle: { width: 1.4, color } };
    });

    opt.tooltip.formatter = params => {
      const list = Array.isArray(params) ? params : [params];
      if (!list.length) return "";
      const out = [qchFmtDate(list[0].value && list[0].value[0])];
      for (const p of list) {
        out.push(p.marker + " " + p.seriesName + ": " + qchNum2(p.value && p.value[1]));
      }
      return out.join("<br>");
    };
    this.render(opt);
  },
};

/* Classic scripts share the global lexical scope, so `QCH` is visible to
 * app.js as-is; the window assignment is insurance against a future loader
 * change (e.g. modules). */
window.QCH = QCH;
