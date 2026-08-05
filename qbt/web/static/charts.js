/* qbt chart rendering — ECharts only, dark theme */
"use strict";

const QCH = {
  inst: null,
  el() { return document.getElementById("chart-main"); },
  get() {
    if (!this.inst) { this.inst = echarts.init(this.el(), null, { renderer: "canvas" });
      window.addEventListener("resize", () => this.inst && this.inst.resize()); }
    return this.inst;
  },
  base() {
    return {
      backgroundColor: "transparent", animation: false,
      textStyle: { color: "#8b949e", fontSize: 11 },
      grid: { left: 55, right: 20, top: 30, bottom: 45 },
      tooltip: { trigger: "axis", backgroundColor: "#161b22", borderColor: "#21262d",
                 textStyle: { color: "#c9d1d9", fontSize: 11 } },
      dataZoom: [{ type: "inside" }, { type: "slider", height: 16, bottom: 8,
                  borderColor: "#21262d", backgroundColor: "#0d1117" }],
    };
  },
  ts(series) { return (series || []).map(p => [p.time * 1000, p.value]); },

  equity(result) {
    const opt = this.base();
    opt.xAxis = { type: "time", axisLine: { lineStyle: { color: "#21262d" } } };
    opt.yAxis = { type: "value", scale: true, splitLine: { lineStyle: { color: "#161b22" } } };
    opt.legend = { textStyle: { color: "#8b949e" }, top: 0 };
    opt.series = [
      { name: "net", type: "line", showSymbol: false, data: this.ts(result.equity),
        lineStyle: { width: 1.6, color: "#58a6ff" } },
      { name: "gross", type: "line", showSymbol: false, data: this.ts(result.equity_gross),
        lineStyle: { width: 1, color: "#8b949e", type: "dashed" } },
    ];
    if (result.benchmark) opt.series.push(
      { name: "benchmark", type: "line", showSymbol: false, data: this.ts(result.benchmark),
        lineStyle: { width: 1, color: "#d29922" } });
    this.get().setOption(opt, true);
  },

  drawdown(result) {
    const opt = this.base();
    opt.xAxis = { type: "time" };
    opt.yAxis = { type: "value", axisLabel: { formatter: v => (v * 100).toFixed(0) + "%" },
                  splitLine: { lineStyle: { color: "#161b22" } } };
    opt.series = [{ name: "drawdown", type: "line", showSymbol: false,
      data: this.ts(result.drawdown), lineStyle: { width: 1, color: "#f85149" },
      areaStyle: { color: "rgba(248,81,73,0.25)" } }];
    this.get().setOption(opt, true);
  },

  candles(bars, trades) {
    const opt = this.base();
    const data = (bars || []).map(b => [b.time * 1000, b.open, b.close, b.low, b.high]);
    opt.xAxis = { type: "time" };
    opt.yAxis = { type: "value", scale: true, splitLine: { lineStyle: { color: "#161b22" } } };
    opt.series = [{ type: "candlestick", data,
      itemStyle: { color: "#3fb950", color0: "#f85149", borderColor: "#3fb950", borderColor0: "#f85149" } }];
    if (trades && trades.length) {
      opt.series.push({ type: "scatter", symbolSize: 9,
        data: trades.map(t => ({
          value: [new Date(t.ts).getTime(), t.price],
          itemStyle: { color: t.side > 0 ? "#3fb950" : "#f85149" },
          symbol: t.side > 0 ? "triangle" : "pin",
        })) });
    }
    this.get().setOption(opt, true);
  },

  heatmap(rows, p1, p2, metric) {
    const opt = this.base();
    const xs = [...new Set(rows.map(r => r[p1]))].sort((a, b) => a - b);
    const ys = p2 ? [...new Set(rows.map(r => r[p2]))].sort((a, b) => a - b) : [""];
    const data = rows.map(r => [xs.indexOf(r[p1]), p2 ? ys.indexOf(r[p2]) : 0, r[metric]]);
    const vals = rows.map(r => r[metric]).filter(v => v !== null && isFinite(v));
    opt.grid.bottom = 60;
    opt.xAxis = { type: "category", data: xs, name: p1 };
    opt.yAxis = { type: "category", data: ys, name: p2 || "" };
    opt.tooltip = { formatter: pt => `${p1}=${xs[pt.value[0]]}${p2 ? ", " + p2 + "=" + ys[pt.value[1]] : ""}<br>${metric}=${(+pt.value[2]).toFixed(3)}` };
    opt.visualMap = { min: Math.min(...vals), max: Math.max(...vals), calculable: true,
      orient: "horizontal", left: "center", bottom: 0, textStyle: { color: "#8b949e" },
      inRange: { color: ["#f85149", "#161b22", "#3fb950"] } };
    opt.dataZoom = [];
    opt.series = [{ type: "heatmap", data, label: { show: data.length < 80, color: "#c9d1d9",
      formatter: pt => (+pt.value[2]).toFixed(2) } }];
    this.get().setOption(opt, true);
  },
};
