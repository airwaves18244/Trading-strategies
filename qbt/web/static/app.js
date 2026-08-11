/* ============================================================================
   qbt terminal — Alpine state (WS-D)
   Contract: docs/ui-upgrade.md §2 (API v2), §3 (QCH), §5 (shell spec).
   Charts are ONLY driven through the global QCH facade from charts.js; this
   file never touches ECharts directly.
   Decisions taken here (contract left them to the section owner):
     - localStorage keys are namespaced "qbt.v2.*"; unknown/stale values are
       ignored silently so an old browser profile can never break boot.
     - strategy params are persisted per strategy key, not globally.
     - delete uses a 2.5s "armed" confirm state on the × button (no window.confirm).
   ========================================================================== */
"use strict";

const LS_PREFIX = "qbt.v2.";

function lsGet(key, dflt) {
  try {
    const raw = localStorage.getItem(LS_PREFIX + key);
    if (raw === null) return dflt;
    return JSON.parse(raw);
  } catch (_) { return dflt; }
}

function lsSet(key, val) {
  try { localStorage.setItem(LS_PREFIX + key, JSON.stringify(val)); } catch (_) { /* quota/private mode */ }
}

const CENTER_TABS = ["Equity", "Drawdown", "Monthly", "Rolling", "Exposure", "Chart", "Sweep", "Compare"];
const RIGHT_TABS = ["Summary", "Years", "Trades", "Attribution", "Costs", "Doc", "Data"];
const SWEEP_METRICS = ["sharpe", "sharpe_oos", "sharpe_is", "cagr", "max_dd", "turnover_ann"];

/* metric key → formatting family (contract §5: pct 1 decimal, ratios 2, counts int) */
const PCT_KEYS = new Set([
  "cagr", "ann_vol", "max_dd", "hit_rate", "best_year", "worst_year",
  "avg_gross", "avg_net", "alpha_ann", "te_ann", "win_rate", "depth",
]);
const INT_KEYS = new Set([
  "n_trades", "n_obs", "dd_duration_days", "n", "days", "recovery_days", "cost_drag_bps_ann",
]);

function terminal() {
  return {
    /* ---------------------------------------------------------- catalogue */
    strategies: [], universes: [], sel: null, search: "",
    centerTabs: CENTER_TABS, rightTabs: RIGHT_TABS, sweepMetrics: SWEEP_METRICS,

    /* --------------------------------------------------------------- form */
    form: {
      params: {}, universe: "moex_liquid", start: "2018-01-01", end: "2025-12-31",
      cost_preset: "moex_equity", execution_lag: 1, overlay: "", vol_target: "",
    },
    sweepCfg: { p1: "", p2: "" },
    ensureCfg: { universe: "moex_liquid", start: "2015-01-01" },
    ensureStatus: "",

    /* --------------------------------------------------------------- runs */
    runs: [], currentRunId: null, result: null, trades: [],
    sweepRows: null, sweepMeta: null,
    running: false, progress: 0, error: "", errorTrace: "", statusLine: "idle",
    docHtml: "", health: [], coverage: [],

    /* ----------------------------------------------------------------- ui */
    theme: "dark",
    tab: "Equity", rtab: "Summary",
    eqLog: false, eqGross: true,
    rollWhich: "sharpe",
    sweepMetric: "sharpe",
    chartSymbol: "",
    cmpSel: [], cmpRuns: null, cmpKey: "",
    editingId: null, labelDraft: "",
    confirmDel: null,
    _sortKey: "ts", _sortAsc: false,
    _delT: null, _rzT: null,

    /* =========================================================== lifecycle */
    async init() {
      this.theme = lsGet("theme", "dark") === "light" ? "light" : "dark";
      this._applyTheme();

      const savedForm = lsGet("form", null);
      if (savedForm && typeof savedForm === "object") {
        for (const k of ["universe", "start", "end", "cost_preset", "execution_lag", "overlay", "vol_target"]) {
          if (savedForm[k] !== undefined && savedForm[k] !== null) this.form[k] = savedForm[k];
        }
      }
      const savedSweep = lsGet("sweepCfg", null);
      if (savedSweep && typeof savedSweep === "object") Object.assign(this.sweepCfg, savedSweep);

      const t = lsGet("tab", "Equity"); if (CENTER_TABS.includes(t)) this.tab = t;
      const rt = lsGet("rtab", "Summary"); if (RIGHT_TABS.includes(rt)) this.rtab = rt;
      this.eqLog = lsGet("eqLog", false) === true;
      this.eqGross = lsGet("eqGross", true) !== false;
      const rw = lsGet("rollWhich", "sharpe"); if (["sharpe", "vol", "beta"].includes(rw)) this.rollWhich = rw;
      const sm = lsGet("sweepMetric", "sharpe"); if (SWEEP_METRICS.includes(sm)) this.sweepMetric = sm;

      try {
        const [strategies, universes, runs] = await Promise.all([
          this._json("/api/strategies"), this._json("/api/universes"), this._json("/api/runs"),
        ]);
        this.strategies = Array.isArray(strategies) ? strategies : [];
        this.universes = Array.isArray(universes) ? universes : [];
        this.runs = Array.isArray(runs) ? runs : [];
      } catch (e) { this._setError(e); }

      const wantKey = lsGet("selKey", null);
      const restored = wantKey ? this.strategies.find(s => s.key === wantKey) : null;
      if (restored) this.select(restored);
      else if (this.strategies.length) this.select(this.strategies[0]);
      /* select() resets the universe to the strategy default — re-apply the
         persisted one when it is still a valid universe. */
      if (savedForm && savedForm.universe && this.universes.includes(savedForm.universe)) {
        this.form.universe = savedForm.universe;
      }
      if (this.universes.length && !this.universes.includes(this.ensureCfg.universe)) {
        this.ensureCfg.universe = this.universes[0];
      }

      this._watch();
      this._bindKeys();
      window.addEventListener("resize", () => {
        clearTimeout(this._rzT);
        this._rzT = setTimeout(() => this.renderCurrent(), 160);
      });
      if (this.rtab === "Data") this.loadData();
      this.renderCurrent();
    },

    _watch() {
      try {
        this.$watch("form", () => this._saveForm());
        this.$watch("sweepCfg", v => lsSet("sweepCfg", { p1: v.p1, p2: v.p2 }));
        this.$watch("tab", v => lsSet("tab", v));
        this.$watch("rtab", v => lsSet("rtab", v));
        this.$watch("eqLog", v => lsSet("eqLog", v));
        this.$watch("eqGross", v => lsSet("eqGross", v));
        this.$watch("rollWhich", v => lsSet("rollWhich", v));
        this.$watch("sweepMetric", v => lsSet("sweepMetric", v));
      } catch (_) { /* $watch unavailable — persistence is best-effort */ }
    },

    _bindKeys() {
      window.addEventListener("keydown", (e) => {
        const el = e.target;
        const typing = !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" ||
                                el.tagName === "SELECT" || el.isContentEditable);
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
          e.preventDefault();
          if (!this.running && this.sel) this.run();
          return;
        }
        if (e.key === "Escape") {
          this.error = ""; this.errorTrace = "";
          this.editingId = null; this.confirmDel = null;
          return;
        }
        if (e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault();
          const s = document.getElementById("search");
          if (s) { s.focus(); s.select(); }
        }
      });
    },

    /* =============================================================== theme */
    _applyTheme() { document.body.classList.toggle("light", this.theme === "light"); },

    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      this._applyTheme();
      lsSet("theme", this.theme);
      /* charts read CSS vars at call time → re-render through the same dispatch */
      this.renderCurrent();
    },

    /* ========================================================== strategies */
    get groupedStrategies() {
      const q = (this.search || "").toLowerCase().trim();
      const items = this.strategies.filter(s =>
        !q || (s.key || "").toLowerCase().includes(q) ||
        (s.name || "").toLowerCase().includes(q) ||
        (s.category || "").toLowerCase().includes(q));
      const by = {};
      for (const s of items) (by[s.category] ||= []).push(s);
      return Object.entries(by).map(([category, list]) => ({ category, items: list }));
    },

    select(s) {
      if (!s) return;
      this.sel = s;
      const saved = (lsGet("params", {}) || {})[s.key] || null;
      const p = {};
      for (const d of (s.params || [])) {
        p[d.name] = (saved && Object.prototype.hasOwnProperty.call(saved, d.name)) ? saved[d.name] : d.default;
      }
      this.form.params = p;
      if (s.default_universe) this.form.universe = s.default_universe;
      lsSet("selKey", s.key);
      this.loadDoc(s.key);
    },

    async loadDoc(key) {
      try {
        const d = await this._json(`/api/strategies/${encodeURIComponent(key)}/doc`);
        this.docHtml = mdToHtml(d.markdown || "(no doc section found)");
      } catch (_) { this.docHtml = "<div class='dim'>doc unavailable</div>"; }
    },

    _saveForm() {
      lsSet("form", {
        universe: this.form.universe, start: this.form.start, end: this.form.end,
        cost_preset: this.form.cost_preset, execution_lag: this.form.execution_lag,
        overlay: this.form.overlay, vol_target: this.form.vol_target,
      });
      if (this.sel) {
        const all = lsGet("params", {}) || {};
        all[this.sel.key] = JSON.parse(JSON.stringify(this.form.params || {}));
        lsSet("params", all);
      }
    },

    /* =============================================================== jobs */
    _payload() {
      const params = {};
      for (const p of (this.sel?.params || [])) {
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
      if (!this.sel || this.running) return;
      this.error = ""; this.errorTrace = ""; this.running = true; this.progress = 0;
      try {
        const { run_id } = await this._json("/api/runs", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this._payload()),
        });
        this.currentRunId = run_id;
        await this._poll(run_id, "run");
        await this._fetchResult(run_id);
        await this.refreshRuns();
      } catch (e) { this._setError(e); }
      this.running = false;
    },

    async runSweep() {
      if (!this.sel || this.running) return;
      this.error = ""; this.errorTrace = "";
      const grid = {};
      for (const spec of [this.sweepCfg.p1, this.sweepCfg.p2]) {
        if (!spec) continue;
        const [name, range] = spec.split("=");
        if (!name || !range) { this.error = "sweep format: name=lo:hi:step"; return; }
        const [lo, hi, step] = range.split(":").map(Number);
        if (!isFinite(lo) || !isFinite(hi)) { this.error = "sweep format: name=lo:hi:step"; return; }
        const vals = [];
        for (let v = lo; v <= hi + 1e-12; v += (step || 1)) vals.push(+v.toFixed(10));
        grid[name.trim()] = vals;
      }
      if (!Object.keys(grid).length) { this.error = "define at least one sweep param"; return; }
      this.running = true; this.progress = 0;
      try {
        const body = Object.assign(this._payload(), { grid });
        const { run_id } = await this._json("/api/sweeps", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
        });
        await this._poll(run_id, "sweep");
        const out = await this._json(`/api/sweeps/${run_id}`);
        this.sweepRows = out.rows || [];
        this.sweepMeta = { params: Object.keys(grid) };
        this.tab = "Sweep";
        this.renderCurrent();
      } catch (e) { this._setError(e); }
      this.running = false;
    },

    async _poll(id, kind) {
      const url = kind === "sweep" ? `/api/sweeps/${id}` : `/api/runs/${id}`;
      for (;;) {
        const st = await this._json(url);
        this.progress = st.progress || 0;
        this.statusLine = `${st.kind || kind} · ${st.state} · ${(100 * this.progress).toFixed(0)}%`;
        if (st.state === "done") { this.statusLine = `${st.kind || kind} · done`; return st; }
        if (st.state === "error") {
          const e = new Error(st.error || "job failed");
          e.trace = st.trace || "";
          throw e;
        }
        await new Promise(res => setTimeout(res, 700));
      }
    },

    async _fetchResult(id) {
      this.result = await this._json(`/api/runs/${id}/result`);
      this.trades = this.result?.trades || [];
      this._syncSymbol();
      if (this.rollWhich === "beta" && this.result?.rolling?.beta == null) this.rollWhich = "sharpe";
      if (this.tab === "Sweep" || this.tab === "Compare") this.tab = "Equity";
      this.renderCurrent();
    },

    async loadRun(r) {
      if (!r || r.state !== "done") return;
      this.currentRunId = r.run_id;
      this.error = ""; this.errorTrace = "";
      try { await this._fetchResult(r.run_id); } catch (e) { this._setError(e); }
    },

    async refreshRuns() {
      try { this.runs = await this._json("/api/runs") || []; } catch (e) { this._setError(e); }
    },

    /* ============================================================ history */
    get sortedRuns() {
      /* starred first, otherwise keep the server order (newest first) */
      return [...(this.runs || [])].sort((a, b) => (b.starred ? 1 : 0) - (a.starred ? 1 : 0));
    },

    runRange(r) {
      const a = (r?.start || "").slice(0, 10), b = (r?.end || "").slice(0, 10);
      if (a && b) return `${a} → ${b}`;
      return (r?.created_at || "").slice(0, 16).replace("T", " ");
    },

    runTitle(r) {
      try { return JSON.stringify(r?.params || {}, null, 1); } catch (_) { return ""; }
    },

    async toggleStar(r, ev) {
      if (ev) ev.stopPropagation();
      const next = !r.starred;
      try {
        const up = await this._json(`/api/runs/${r.run_id}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ starred: next }),
        });
        r.starred = up && "starred" in up ? up.starred : next;
      } catch (e) { this._setError(e); }
    },

    async delRun(r, ev) {
      if (ev) ev.stopPropagation();
      if (this.confirmDel !== r.run_id) {
        this.confirmDel = r.run_id;
        clearTimeout(this._delT);
        this._delT = setTimeout(() => { this.confirmDel = null; }, 2500);
        return;
      }
      clearTimeout(this._delT);
      this.confirmDel = null;
      try {
        await this._json(`/api/runs/${r.run_id}`, { method: "DELETE" });
        this.cmpSel = this.cmpSel.filter(id => id !== r.run_id);
        if (this.currentRunId === r.run_id) {
          this.currentRunId = null; this.result = null; this.trades = [];
        }
        await this.refreshRuns();
        this.renderCurrent();
      } catch (e) { this._setError(e); }
    },

    startLabel(r, ev) {
      if (ev) ev.stopPropagation();
      this.editingId = r.run_id;
      this.labelDraft = r.label || "";
      this.$nextTick(() => {
        const el = document.getElementById("lbl-" + r.run_id);
        if (el) { el.focus(); el.select(); }
      });
    },

    async saveLabel(r) {
      if (this.editingId !== r.run_id) return;
      const v = (this.labelDraft || "").trim();
      this.editingId = null;
      if (v === (r.label || "")) return;
      try {
        const up = await this._json(`/api/runs/${r.run_id}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ label: v }),
        });
        r.label = up && "label" in up ? up.label : v;
      } catch (e) { this._setError(e); }
    },

    /* ============================================================ compare */
    cmpChecked(r) { return this.cmpSel.includes(r.run_id); },

    toggleCmp(r, ev) {
      if (ev) ev.stopPropagation();
      const i = this.cmpSel.indexOf(r.run_id);
      if (i >= 0) this.cmpSel.splice(i, 1);
      else if (this.cmpSel.length >= 6) { this.error = "compare: at most 6 runs"; return; }
      else this.cmpSel.push(r.run_id);
      if (this.tab === "Compare") this.renderCurrent();
    },

    openCompare() { this.tab = "Compare"; this.renderCurrent(); },

    async _renderCompare() {
      const Q = this._qch(); if (!Q) return;
      if (this.cmpSel.length < 2) { this.cmpRuns = null; Q.dispose(); return; }
      const key = this.cmpSel.join(",");
      if (key !== this.cmpKey || !this.cmpRuns) {
        /* fetched once per selection, not once per re-render */
        const out = await this._json(`/api/compare?ids=${encodeURIComponent(key)}`);
        this.cmpRuns = out?.runs || [];
        this.cmpKey = key;
      }
      const items = (this.cmpRuns || []).map(r => ({
        label: r.label || r.meta?.strategy_key || String(r.run_id || "").slice(0, 8),
        equity: r.equity || [],
      }));
      Q.compare(items);
      /* the metrics table appearing below shrinks .chart-wrap AFTER this render —
         nudge ECharts to re-measure the container once the DOM settles */
      this.$nextTick(() => window.dispatchEvent(new Event("resize")));
    },

    get cmpMetricKeys() { return ["sharpe", "cagr", "max_dd", "turnover_ann"]; },

    /* ============================================================== charts */
    _qch() {
      const Q = (typeof window !== "undefined") ? window.QCH : null;
      if (!Q) { this.error = this.error || "charts.js failed to load"; return null; }
      return Q;
    },

    renderCurrent() {
      this.$nextTick(async () => {
        const Q = this._qch(); if (!Q) return;
        const t = this.tab, r = this.result;
        try {
          if (t === "Compare") { await this._renderCompare(); return; }
          if (t === "Chart") { await this._candles(); return; }
          if (t === "Sweep") {
            if (this.sweepRows && this.sweepRows.length) {
              const p = this.sweepMeta?.params || [];
              Q.heatmap(this.sweepRows, p[0], p[1] || null, this.sweepMetric);
            } else Q.dispose();
            return;
          }
          if (!r) { Q.dispose(); return; }
          if (t === "Equity") Q.equity(r, { log: !!this.eqLog, gross: !!this.eqGross });
          else if (t === "Drawdown") Q.drawdown(r);
          else if (t === "Monthly") Q.monthly(r);
          else if (t === "Rolling") Q.rolling(r, this.rollWhich);
          else if (t === "Exposure") Q.exposure(r);
        } catch (e) { this._setError(e); }
      });
    },

    setTab(t) { this.tab = t; this.renderCurrent(); },

    setRTab(t) {
      this.rtab = t;
      if (t === "Data" && !this.health.length && !this.coverage.length) this.loadData();
    },

    /* --- Chart tab ------------------------------------------------------- */
    get chartSymbols() {
      const attr = (this.result?.attribution || []).map(a => a.symbol).filter(Boolean);
      if (attr.length) return attr;
      const fromTrades = [...new Set((this.trades || []).map(t => t.symbol).filter(Boolean))];
      if (fromTrades.length) return fromTrades;
      return ["MOEX:IMOEX"];
    },

    _syncSymbol() {
      const syms = this.chartSymbols;
      if (!this.chartSymbol || !syms.includes(this.chartSymbol)) this.chartSymbol = syms[0];
    },

    async _candles() {
      const Q = this._qch(); if (!Q) return;
      this._syncSymbol();
      const symbol = this.chartSymbol || "MOEX:IMOEX";
      const qs = `symbol=${encodeURIComponent(symbol)}&freq=1d` +
                 `&start=${encodeURIComponent(this.form.start)}&end=${encodeURIComponent(this.form.end)}`;
      try {
        const bars = await this._json(`/api/bars?${qs}`);
        Q.candles(bars || [], (this.trades || []).filter(t => t.symbol === symbol), symbol);
      } catch (e) { this._setError(e); }
    },

    /* --- empty states ---------------------------------------------------- */
    get chartEmpty() {
      const r = this.result;
      switch (this.tab) {
        case "Sweep": return !(this.sweepRows && this.sweepRows.length);
        case "Compare": return this.cmpSel.length < 2;
        case "Chart": return false;
        case "Monthly": return !r || !r.monthly;
        case "Rolling": return !r || !r.rolling;
        case "Exposure": return !r || !r.exposure;
        default: return !r;
      }
    },

    get emptyMsg() {
      switch (this.tab) {
        case "Sweep": return "No sweep loaded. Open “parameter sweep” in the left pane, enter e.g. lookback=10:60:10 and run it.";
        case "Compare": return `Select 2–6 finished runs in history (checkbox on the left of each row) to overlay their equity curves. ${this.cmpSel.length} selected.`;
        case "Monthly": return "This run has no monthly table — re-run it to pick up the v2 report fields.";
        case "Rolling": return "This run has no rolling statistics — re-run it to pick up the v2 report fields.";
        case "Exposure": return "No exposure series in this run.";
        default: return "No result loaded. Configure a strategy on the left and hit RUN BACKTEST (Ctrl+Enter), or pick a finished run from history.";
      }
    },

    get rollingHasBeta() { return this.result?.rolling?.beta != null; },

    /* ================================================================ data */
    async loadData() {
      try {
        this.health = await this._json("/api/data/health") || [];
        this.coverage = await this._json("/api/data/status") || [];
      } catch (e) { this._setError(e); }
    },

    async ensure() {
      this.ensureStatus = "submitting…";
      try {
        const { run_id } = await this._json("/api/data/ensure", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ universe: this.ensureCfg.universe, start: this.ensureCfg.start }),
        });
        await this._poll(run_id, "run");
        this.ensureStatus = "done";
        this.loadData();
      } catch (e) { this.ensureStatus = "error: " + (e.message || e); }
    },

    /* ============================================================= summary */
    get summaryGroups() {
      const m = this.result?.metrics || {};
      const defs = [
        ["returns", ["cagr", "best_year", "worst_year", "avg_gross", "avg_net"]],
        ["risk", ["sharpe", "sortino", "ann_vol", "max_dd", "dd_duration_days", "calmar", "skew", "t_stat"]],
        ["trading", ["turnover_ann", "hit_rate", "cost_drag_bps_ann", "n_trades", "n_obs"]],
      ];
      return defs
        .map(([title, keys]) => ({ title, rows: keys.filter(k => k in m).map(k => [k, m[k]]) }))
        .filter(g => g.rows.length);
    },

    get benchRows() {
      const b = this.result?.benchmark_stats;
      if (!b) return [];
      return [
        ["alpha_ann", b.alpha_ann], ["beta", b.beta], ["corr", b.corr],
        ["ir", b.ir], ["te_ann", b.te_ann],
        ["bench sharpe", b.sharpe], ["bench cagr", b.cagr], ["bench max_dd", b.max_dd],
      ];
    },

    get tradeChips() {
      const t = this.result?.trade_stats;
      if (!t) return [];
      return [
        ["n", this.fmt("n", t.n)],
        ["win", this.pct(t.win_rate)],
        ["pf", this.num(t.profit_factor)],
        ["avg win", this.pct(t.avg_win)],
        ["avg loss", this.pct(t.avg_loss)],
        ["expectancy", this.pct(t.expectancy)],
        ["hold d", this.num(t.avg_hold_days)],
        ["best", this.pct(t.best)],
        ["worst", this.pct(t.worst)],
      ];
    },

    sortTrades(k) {
      this._sortAsc = this._sortKey === k ? !this._sortAsc : false;
      this._sortKey = k;
      const dir = this._sortAsc ? 1 : -1;
      this.trades = [...this.trades].sort((a, b) => {
        const x = a[k], y = b[k];
        if (x === y) return 0;
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        return x > y ? dir : -dir;
      });
    },

    sortMark(k) { return this._sortKey === k ? (this._sortAsc ? " ▲" : " ▼") : ""; },

    exportTrades() {
      const cols = ["ts", "symbol", "side", "qty", "price", "notional", "cost_bps", "reason", "tag", "pnl"];
      const csv = [cols.join(",")].concat(
        (this.trades || []).map(t => cols.map(c => t[c] ?? "").join(","))).join("\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
      a.download = `trades_${this.currentRunId || "run"}.csv`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    },

    /* ============================================================== errors */
    _setError(e) {
      this.error = String((e && e.message) || e || "error");
      this.errorTrace = (e && e.trace) || "";
    },

    clearError() { this.error = ""; this.errorTrace = ""; },

    async _json(url, opts) {
      const r = await fetch(url, opts);
      if (!r.ok) throw await this._httpError(r, url);
      if (r.status === 204) return null;
      return await r.json();
    },

    async _httpError(r, url) {
      let detail = "";
      try {
        const txt = await r.text();
        try {
          const j = JSON.parse(txt);
          detail = typeof j.detail === "string" ? j.detail
            : (j.detail !== undefined ? JSON.stringify(j.detail) : txt);
        } catch (_) { detail = txt; }
      } catch (_) { /* body unreadable */ }
      const short = String(detail || r.statusText || "").slice(0, 600);
      return new Error(`${r.status} ${url.split("?")[0]} — ${short}`);
    },

    /* =========================================================== formatting */
    fmt(k, v) {
      if (v === null || v === undefined || v === "") return "—";
      if (k === "cost_drag_bps_ann") return isFinite(v) ? Math.round(v) + " bps" : "—";
      if (PCT_KEYS.has(k)) return this.pct(v);
      if (INT_KEYS.has(k)) return isFinite(v) ? String(Math.round(v)) : "—";
      return this.num(v);
    },
    pct(v) {
      if (v === null || v === undefined || !isFinite(v)) return "—";
      return (100 * v).toFixed(1) + "%";
    },
    num(v) {
      if (v === null || v === undefined || !isFinite(v)) return "—";
      return (+v).toFixed(2);
    },
    int(v) {
      if (v === null || v === undefined || !isFinite(v)) return "—";
      return String(Math.round(v));
    },
    day(s) { return String(s || "").slice(0, 10) || "—"; },
    short(s) { return String(s || "").replace("MOEX:", "").replace("CRYPTO:", ""); },
    sign(v) { return (v === null || v === undefined || !isFinite(v)) ? "" : (v >= 0 ? "pos" : "neg"); },
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
