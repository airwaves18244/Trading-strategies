/* qbt terminal Alpine state */
"use strict";

function terminal() {
  return {
    strategies: [], universes: [], sel: null, search: "",
    form: { params: {}, universe: "moex_liquid", start: "2018-01-01", end: "2025-12-31",
            cost_preset: "moex_equity", execution_lag: 1, overlay: "", vol_target: "" },
    sweepCfg: { p1: "", p2: "" },
    ensureCfg: { universe: "moex_liquid", start: "2015-01-01" },
    ensureStatus: "",
    runs: [], currentRunId: null, result: null, trades: [], sweepRows: null, sweepMeta: null,
    running: false, progress: 0, error: "", statusLine: "", docHtml: "",
    tab: "Equity", rtab: "Summary", health: [], coverage: [],
    _sortKey: "ts", _sortAsc: false,

    async init() {
      this.strategies = await (await fetch("/api/strategies")).json();
      this.universes = await (await fetch("/api/universes")).json();
      this.runs = await (await fetch("/api/runs")).json();
      if (this.strategies.length) this.select(this.strategies[0]);
    },

    get groupedStrategies() {
      const q = this.search.toLowerCase();
      const items = this.strategies.filter(s =>
        !q || s.key.includes(q) || s.name.toLowerCase().includes(q));
      const by = {};
      for (const s of items) (by[s.category] ||= []).push(s);
      return Object.entries(by).map(([category, items]) => ({ category, items }));
    },

    select(s) {
      this.sel = s; this.form.params = {};
      for (const p of s.params) this.form.params[p.name] = p.default;
      this.form.universe = s.default_universe;
      this.loadDoc(s.key);
    },

    async loadDoc(key) {
      try {
        const d = await (await fetch(`/api/strategies/${key}/doc`)).json();
        this.docHtml = mdToHtml(d.markdown || "(no doc section found)");
      } catch { this.docHtml = ""; }
    },

    _payload() {
      const params = {};
      for (const p of this.sel.params) {
        let v = this.form.params[p.name];
        if (typeof v === "string" && v !== "" && !isNaN(+v) && p.choices === null) v = +v;
        if (v === "true") v = true; if (v === "false") v = false;
        params[p.name] = v;
      }
      return {
        strategy_key: this.sel.key, params, universe: this.form.universe,
        start: this.form.start, end: this.form.end, cost_preset: this.form.cost_preset,
        execution_lag: +this.form.execution_lag,
        overlay: this.form.overlay || null,
        vol_target: this.form.vol_target ? +this.form.vol_target : null,
      };
    },

    async run() {
      this.error = ""; this.running = true; this.progress = 0;
      try {
        const r = await fetch("/api/runs", { method: "POST",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify(this._payload()) });
        if (!r.ok) throw new Error(await r.text());
        const { run_id } = await r.json();
        this.currentRunId = run_id;
        await this._poll(run_id, "run");
        await this._fetchResult(run_id);
        this.runs = await (await fetch("/api/runs")).json();
      } catch (e) { this.error = String(e.message || e); }
      this.running = false;
    },

    async runSweep() {
      this.error = "";
      const grid = {};
      for (const spec of [this.sweepCfg.p1, this.sweepCfg.p2]) {
        if (!spec) continue;
        const [name, range] = spec.split("=");
        if (!name || !range) { this.error = "sweep format: name=lo:hi:step"; return; }
        const [lo, hi, step] = range.split(":").map(Number);
        const vals = [];
        for (let v = lo; v <= hi + 1e-12; v += (step || 1)) vals.push(+v.toFixed(10));
        grid[name.trim()] = vals;
      }
      if (!Object.keys(grid).length) { this.error = "define at least one sweep param"; return; }
      this.running = true; this.progress = 0;
      try {
        const body = Object.assign(this._payload(), { grid });
        const r = await fetch("/api/sweeps", { method: "POST",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        if (!r.ok) throw new Error(await r.text());
        const { run_id } = await r.json();
        await this._poll(run_id, "sweep");
        const out = await (await fetch(`/api/sweeps/${run_id}`)).json();
        this.sweepRows = out.rows || [];
        this.sweepMeta = { params: Object.keys(grid), metric: "sharpe" };
        this.tab = "Sweep"; this.renderCurrent();
      } catch (e) { this.error = String(e.message || e); }
      this.running = false;
    },

    async _poll(id, kind) {
      for (;;) {
        const st = await (await fetch(kind === "sweep" ? `/api/sweeps/${id}` : `/api/runs/${id}`)).json();
        this.progress = st.progress || 0;
        this.statusLine = `${st.kind} ${st.state} ${(100 * this.progress).toFixed(0)}%`;
        if (st.state === "done") return;
        if (st.state === "error") throw new Error(st.error || "job failed");
        await new Promise(res => setTimeout(res, 700));
      }
    },

    async _fetchResult(id) {
      this.result = await (await fetch(`/api/runs/${id}/result`)).json();
      this.trades = this.result.trades || [];
      this.tab = "Equity"; this.renderCurrent();
    },

    async loadRun(r) {
      if (r.state !== "done") return;
      this.currentRunId = r.run_id; this.error = "";
      try { await this._fetchResult(r.run_id); } catch (e) { this.error = String(e); }
    },

    renderCurrent() {
      this.$nextTick(() => {
        if (this.tab === "Equity" && this.result) QCH.equity(this.result);
        else if (this.tab === "Drawdown" && this.result) QCH.drawdown(this.result);
        else if (this.tab === "Chart") this._candles();
        else if (this.tab === "Sweep" && this.sweepRows)
          QCH.heatmap(this.sweepRows, this.sweepMeta.params[0], this.sweepMeta.params[1], this.sweepMeta.metric);
      });
    },

    async _candles() {
      const sym = (this.trades[0] && this.trades[0].symbol) ||
        (this.result && Object.keys(this.result.exposure || {}).length ? null : null);
      const symbol = sym || "MOEX:IMOEX";
      try {
        const bars = await (await fetch(`/api/bars?symbol=${encodeURIComponent(symbol)}&freq=1d&start=${this.form.start}&end=${this.form.end}`)).json();
        QCH.candles(bars, this.trades.filter(t => t.symbol === symbol));
      } catch (e) { this.error = "bars: " + e; }
    },

    async loadData() {
      try {
        this.health = await (await fetch("/api/data/health")).json();
        this.coverage = await (await fetch("/api/data/status")).json();
      } catch (e) { this.error = String(e); }
    },

    async ensure() {
      this.ensureStatus = "submitting…";
      const r = await fetch("/api/data/ensure", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ universe: this.ensureCfg.universe, start: this.ensureCfg.start }) });
      const { run_id } = await r.json();
      try { await this._poll(run_id, "run"); this.ensureStatus = "done"; this.loadData(); }
      catch (e) { this.ensureStatus = "error: " + e.message; }
    },

    get metricRows() {
      const m = this.result?.metrics || {};
      const order = ["sharpe", "sortino", "cagr", "ann_vol", "max_dd", "dd_duration_days",
                     "calmar", "skew", "hit_rate", "turnover_ann", "avg_gross", "avg_net",
                     "cost_drag_bps_ann", "t_stat", "best_year", "worst_year", "n_trades", "n_obs"];
      return order.filter(k => k in m).map(k => [k, m[k]]);
    },

    sortTrades(k) {
      this._sortAsc = this._sortKey === k ? !this._sortAsc : false; this._sortKey = k;
      const dir = this._sortAsc ? 1 : -1;
      this.trades = [...this.trades].sort((a, b) => (a[k] > b[k] ? dir : -dir));
    },

    exportTrades() {
      const cols = ["ts", "symbol", "side", "qty", "price", "notional", "cost_bps", "reason", "tag", "pnl"];
      const csv = [cols.join(",")].concat(
        this.trades.map(t => cols.map(c => t[c] ?? "").join(","))).join("\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
      a.download = `trades_${this.currentRunId}.csv`; a.click();
    },

    fmt(k, v) {
      if (v === null || v === undefined) return "—";
      if (["cagr", "ann_vol", "max_dd", "hit_rate", "best_year", "worst_year"].includes(k)) return this.pct(v);
      if (["n_trades", "n_obs", "dd_duration_days"].includes(k)) return String(Math.round(v));
      return this.num(v);
    },
    pct(v) { return v === null || v === undefined ? "—" : (100 * v).toFixed(1) + "%"; },
    num(v) { return v === null || v === undefined || !isFinite(v) ? "—" : (+v).toFixed(2); },
    short(s) { return String(s || "").replace("MOEX:", "").replace("CRYPTO:", ""); },
  };
}

/* minimal markdown renderer: headers, bold, code, tables, lists */
function mdToHtml(md) {
  const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const lines = md.split("\n"); const out = []; let inTable = false;
  for (const raw of lines) {
    let ln = esc(raw);
    if (/^\s*\|/.test(ln)) {
      const cells = ln.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      if (cells.every(c => /^:?-+:?$/.test(c))) continue;
      if (!inTable) { out.push("<table>"); inTable = true; }
      out.push("<tr>" + cells.map(c => `<td>${inline(c)}</td>`).join("") + "</tr>");
      continue;
    } else if (inTable) { out.push("</table>"); inTable = false; }
    if (/^### /.test(ln)) out.push(`<h3>${inline(ln.slice(4))}</h3>`);
    else if (/^## /.test(ln)) out.push(`<h2>${inline(ln.slice(3))}</h2>`);
    else if (/^- /.test(ln)) out.push(`<div>• ${inline(ln.slice(2))}</div>`);
    else if (/^\d+\. /.test(ln)) out.push(`<div>${inline(ln)}</div>`);
    else if (ln.trim() === "") out.push("<br>");
    else out.push(`<div>${inline(ln)}</div>`);
  }
  if (inTable) out.push("</table>");
  function inline(s) {
    return s.replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
            .replace(/\*([^*]+)\*/g, "<i>$1</i>");
  }
  return out.join("\n");
}
