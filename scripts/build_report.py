"""Generate the qbt results artifact page from the real run JSON."""
import json
from pathlib import Path

D = json.load(open("/tmp/qbt_results.json"))
OUT = Path("/tmp/claude-0/-home-user-Trading-strategies/2de6131c-b701-5025-b4ca-b6f49c39bb74/scratchpad/qbt-moex-report.html")

NAMES = {
    "xs_equity_momentum": "Кросс-секционный моментум 12-1",
    "residual_momentum": "Остаточный моментум",
    "industry_factor_momentum": "Отраслевой моментум",
    "week52_high_momentum": "Близость к 52-нед. максимуму",
    "low_vol_bab": "Низкая волатильность",
    "fundamental_seasonality": "Сезонность (Heston-Sadka)",
    "pairs_trading": "Парный трейдинг",
    "stat_arb_residual": "Стат-арбитраж остатков",
    "short_term_reversal": "Краткосрочный разворот",
    "turn_of_month": "Оборот месяца",
    "vol_target_overlay": "Vol-таргетинг индекса",
    "dual_momentum": "Двойной моментум",
    "index_panic_reversion": "Возврат после паники",
    "overnight_intraday": "Ночная премия",
}
FAMILY = {
    "xs_equity_momentum": "momentum", "residual_momentum": "momentum",
    "industry_factor_momentum": "momentum", "week52_high_momentum": "momentum",
    "dual_momentum": "momentum", "low_vol_bab": "factor",
    "fundamental_seasonality": "flow", "turn_of_month": "flow",
    "pairs_trading": "rv", "stat_arb_residual": "rv",
    "short_term_reversal": "reversion", "index_panic_reversion": "reversion",
    "overnight_intraday": "reversion", "vol_target_overlay": "overlay",
}
FAMILY_RU = {"momentum": "моментум", "factor": "фактор", "flow": "потоки",
             "rv": "relative value", "reversion": "разворот", "overlay": "оверлей"}
# Sharpe range the research corpus predicts (SUMMARY.md master table)
CORPUS = {
    "xs_equity_momentum": (0.3, 0.6), "residual_momentum": (0.5, 0.8),
    "industry_factor_momentum": (0.3, 0.7), "week52_high_momentum": (0.3, 0.5),
    "dual_momentum": (0.5, 0.7), "low_vol_bab": (0.3, 0.5),
    "fundamental_seasonality": (0.2, 0.4), "turn_of_month": (0.3, 0.6),
    "pairs_trading": (0.3, 0.7), "stat_arb_residual": (0.5, 1.0),
    "short_term_reversal": (0.3, 0.7), "index_panic_reversion": (0.4, 0.7),
    "overnight_intraday": (0.2, 0.5), "vol_target_overlay": (0.4, 0.7),
}

for s in D["strategies"]:
    s["name"] = NAMES.get(s["key"], s["key"])
    s["family"] = FAMILY.get(s["key"], "")
    s["family_ru"] = FAMILY_RU.get(FAMILY.get(s["key"], ""), "")
    s["corpus"] = CORPUS.get(s["key"])

D["benchmark"] = {"name": "IMOEX", "final": 4.14, "cagr": 0.144, "vol": 0.333,
                  "sharpe": 0.59, "max_dd": -0.714}
payload = json.dumps(D, ensure_ascii=False, separators=(",", ":"))

HTML = """<title>qbt — прогон стратегий на MOEX, 2015–2025</title>
<style>
:root {
  color-scheme: light;
  --paper: #f2f3f0;
  --card: #fafbf9;
  --ink: #171b19;
  --ink-2: #5c6360;
  --ink-3: #868d89;
  --rule: #d6dad5;
  --rule-soft: #e6e9e4;
  --accent: #175f6e;
  --pos: #2a78d6;
  --neg: #e34948;
  --ref: #8b918e;
  --seq-1: #cde2fb; --seq-2: #9ec5f4; --seq-3: #5598e7; --seq-4: #2a78d6; --seq-5: #1c5cab;
  --shadow: 0 1px 2px rgba(20,30,28,.06), 0 8px 24px -18px rgba(20,30,28,.5);
  --serif: ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: ui-sans-serif, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --paper: #14181a; --card: #191e20; --ink: #e7eae8; --ink-2: #98a19d; --ink-3: #6f7975;
    --rule: #272d2f; --rule-soft: #202628; --accent: #63b3c4;
    --pos: #3987e5; --neg: #e66767; --ref: #79817e;
    --seq-1: #184f95; --seq-2: #256abf; --seq-3: #2a78d6; --seq-4: #5598e7; --seq-5: #9ec5f4;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 10px 30px -20px rgba(0,0,0,.9);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --paper: #14181a; --card: #191e20; --ink: #e7eae8; --ink-2: #98a19d; --ink-3: #6f7975;
  --rule: #272d2f; --rule-soft: #202628; --accent: #63b3c4;
  --pos: #3987e5; --neg: #e66767; --ref: #79817e;
  --seq-1: #184f95; --seq-2: #256abf; --seq-3: #2a78d6; --seq-4: #5598e7; --seq-5: #9ec5f4;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 10px 30px -20px rgba(0,0,0,.9);
}

* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: var(--sans); font-size: 16px; line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 1120px; margin: 0 auto; padding: 0 24px 96px; }
.col { max-width: 68ch; }
h1, h2, h3 { font-family: var(--serif); font-weight: 600; text-wrap: balance; letter-spacing: -.01em; }
h1 { font-size: clamp(30px, 4.4vw, 44px); line-height: 1.12; margin: 0 0 12px; }
h2 { font-size: clamp(22px, 2.6vw, 28px); line-height: 1.2; margin: 0 0 10px; }
h3 { font-size: 18px; margin: 0 0 6px; }
p { margin: 0 0 14px; }
a { color: var(--accent); text-underline-offset: 3px; }
a:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }
strong { font-weight: 650; }
.num { font-family: var(--mono); font-variant-numeric: tabular-nums; }

/* masthead */
header.mast { border-bottom: 1px solid var(--rule); padding: 56px 0 24px; margin-bottom: 40px; }
.eyebrow {
  font-family: var(--mono); font-size: 11px; letter-spacing: .16em; text-transform: uppercase;
  color: var(--ink-3); margin: 0 0 18px;
}
.lede { font-size: 18px; color: var(--ink-2); max-width: 62ch; }
.prov {
  display: flex; flex-wrap: wrap; gap: 0 32px; margin-top: 26px;
  padding-top: 18px; border-top: 1px solid var(--rule-soft);
}
.prov div { padding: 4px 0; }
.prov dt { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-3); }
.prov dd { margin: 2px 0 0; font-family: var(--mono); font-size: 14px; font-variant-numeric: tabular-nums; }

section { margin: 0 0 56px; }
section > .head { margin-bottom: 22px; }
.sec-label {
  font-family: var(--mono); font-size: 11px; letter-spacing: .16em; text-transform: uppercase;
  color: var(--accent); margin: 0 0 8px;
}
.note { font-size: 14px; color: var(--ink-2); max-width: 66ch; }

/* panels */
.panel {
  background: var(--card); border: 1px solid var(--rule); border-radius: 4px;
  padding: 20px; box-shadow: var(--shadow);
}
.grid-2 { display: grid; grid-template-columns: minmax(0,1.35fr) minmax(0,1fr); gap: 20px; align-items: start; }
@media (max-width: 860px) { .grid-2 { grid-template-columns: 1fr; } }

/* spine chart */
.spine { display: grid; gap: 3px; }
.spine-row {
  display: grid; grid-template-columns: 232px 1fr 62px; align-items: center; gap: 12px;
  padding: 3px 4px; border-radius: 3px; cursor: default;
}
.spine-row:hover { background: var(--rule-soft); }
.spine-name { font-size: 13.5px; line-height: 1.25; }
.spine-name .fam { display: block; font-family: var(--mono); font-size: 10px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--ink-3); }
.spine-track { position: relative; height: 22px; }
.spine-zero { position: absolute; top: -1px; bottom: -1px; width: 1px; background: var(--ink-3); opacity: .55; }
.spine-bench { position: absolute; top: -2px; bottom: -2px; width: 2px; background: var(--accent); opacity: .75; }
.spine-bar { position: absolute; top: 5px; height: 12px; border-radius: 0; }
.spine-bar.pos { background: var(--pos); border-radius: 0 3px 3px 0; }
.spine-bar.neg { background: var(--neg); border-radius: 3px 0 0 3px; }
.spine-corpus { position: absolute; top: 2px; height: 18px; border: 1px dashed var(--ink-3); opacity: .5; border-radius: 2px; }
.spine-val { font-family: var(--mono); font-size: 13px; text-align: right; font-variant-numeric: tabular-nums; }
.axis-row { display: grid; grid-template-columns: 232px 1fr 62px; gap: 12px; margin-top: 8px; }
.axis-ticks { position: relative; height: 16px; font-family: var(--mono); font-size: 10px; color: var(--ink-3); }
.axis-ticks span { position: absolute; transform: translateX(-50%); }
.legend { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 14px; font-size: 12.5px; color: var(--ink-2); }
.legend i { display: inline-block; width: 12px; height: 8px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.legend .dash { width: 14px; height: 0; border-top: 1px dashed var(--ink-3); }

/* svg charts */
figure { margin: 0; }
figcaption { font-size: 12.5px; color: var(--ink-2); margin-top: 10px; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
.grid-line { stroke: var(--rule-soft); stroke-width: 1; }
.axis-txt { font-family: var(--mono); font-size: 10px; fill: var(--ink-3); }
.series-line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.crosshair { stroke: var(--ink-3); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0; }

/* tables */
.tbl-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: right; padding: 6px 8px; border-bottom: 1px solid var(--rule-soft); white-space: nowrap; }
th { font-family: var(--mono); font-size: 10.5px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 500; border-bottom: 1px solid var(--rule); }
td:first-child, th:first-child { text-align: left; }
td.n { font-family: var(--mono); font-variant-numeric: tabular-nums; }
tr.split td { background: color-mix(in srgb, var(--accent) 8%, transparent); font-weight: 600; }
tr.split td:first-child { color: var(--accent); }
.pos-t { color: var(--pos); } .neg-t { color: var(--neg); }
.minibar { position: relative; display: block; width: 52px; height: 9px; }
.mb-zero { position: absolute; left: 50%; top: -1px; bottom: -1px; width: 1px; background: var(--ink-3); opacity: .5; }
.mb-fill { position: absolute; top: 1px; height: 7px; border-radius: 2px; }

/* heatmap */
.heat { display: grid; gap: 2px; }
.heat-cell {
  aspect-ratio: 2.4 / 1; display: grid; place-items: center; border-radius: 3px;
  font-family: var(--mono); font-size: 13px; font-variant-numeric: tabular-nums; cursor: default;
}
.heat-cell:hover { outline: 2px solid var(--ink); outline-offset: -2px; }
.heat-lbl { font-family: var(--mono); font-size: 11px; color: var(--ink-3); display: grid; place-items: center; }

/* stat tiles */
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px;
  background: var(--rule); border: 1px solid var(--rule); border-radius: 4px; overflow: hidden; }
.tile { background: var(--card); padding: 14px 16px; }
.tile dt { font-size: 11px; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); }
.tile dd { margin: 6px 0 0; font-family: var(--mono); font-size: 24px; font-variant-numeric: tabular-nums;
  letter-spacing: -.02em; }
.tile .sub { font-family: var(--sans); font-size: 12px; color: var(--ink-2); margin-top: 3px; }

/* callout */
.callout {
  border-left: 3px solid var(--accent); background: var(--card);
  padding: 16px 18px; border-radius: 0 4px 4px 0; margin: 22px 0;
}
.callout h3 { margin-bottom: 4px; }
.callout p:last-child { margin-bottom: 0; }
.callout p { font-size: 14.5px; color: var(--ink-2); }

/* tooltip */
#tip {
  position: fixed; z-index: 50; pointer-events: none; opacity: 0; transition: opacity .12s;
  background: var(--ink); color: var(--paper); border-radius: 4px; padding: 8px 10px;
  font-size: 12px; line-height: 1.45; max-width: 260px; box-shadow: 0 6px 24px -8px rgba(0,0,0,.55);
}
#tip .t-h { font-weight: 650; margin-bottom: 3px; }
#tip .t-r { display: flex; justify-content: space-between; gap: 14px; font-family: var(--mono);
  font-variant-numeric: tabular-nums; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
ul.clean { margin: 0 0 14px; padding-left: 18px; }
ul.clean li { margin-bottom: 7px; }
footer { border-top: 1px solid var(--rule); padding-top: 20px; font-size: 13px; color: var(--ink-2); }
</style>

<div class="wrap">
<header class="mast">
  <p class="eyebrow">qbt · бэктест-терминал · прогон на живых данных</p>
  <h1>14 стратегий из корпуса, проверенные на MOEX 2015–2025</h1>
  <p class="lede">Данные скачаны с MOEX ISS, косты и лаг исполнения включены, каждая стратегия
  прошла проверку на подглядывание в будущее. Главный вывод неудобный: по коэффициенту Шарпа
  тринадцать из четырнадцати проиграли простой покупке индекса, а одна теряет деньги ровно так,
  как предсказывает исследовательский корпус.</p>
  <dl class="prov">
    <div><dt>Источник</dt><dd>MOEX ISS</dd></div>
    <div><dt>Инструменты</dt><dd>28 акций + IMOEX</dd></div>
    <div><dt>Баров на бумагу</dt><dd>2 778</dd></div>
    <div><dt>Период</dt><dd>2015-06 → 2025-12</dd></div>
    <div><dt>Косты</dt><dd>4 бп + 3 бп спред</dd></div>
    <div><dt>Лаг исполнения</dt><dd>1 бар</dd></div>
  </dl>
</header>

<section>
  <div class="head">
    <p class="sec-label">Итог прогона</p>
    <h2>Планка — не ноль, а индекс</h2>
    <p class="note">Сплошная полоса — фактический нетто-Sharpe на MOEX. Пунктирная рамка — диапазон,
    который корпус предсказывал для этой стратегии (SUMMARY.md). Вертикальная линия — Sharpe самого
    IMOEX за тот же период: <span class="num">0,59</span>. Её пересекает только одна стратегия.
    Наведите на строку, чтобы увидеть полный набор метрик.</p>
  </div>
  <div class="panel">
    <div class="spine" id="spine"></div>
    <div class="axis-row"><div></div><div class="axis-ticks" id="spine-axis"></div><div></div></div>
    <div class="legend">
      <span><i style="background:var(--pos)"></i>Sharpe &gt; 0</span>
      <span><i style="background:var(--neg)"></i>Sharpe &lt; 0</span>
      <span><i class="dash"></i>прогноз корпуса</span>
      <span><i style="width:2px;height:12px;background:var(--accent)"></i>IMOEX, Sharpe 0,59</span>
    </div>
  </div>
</section>

<section>
  <div class="head">
    <p class="sec-label">Лучшая по Шарпу среди акций</p>
    <h2>Кросс-секционный моментум против «просто купи индекс»</h2>
    <p class="note">Стратегия глаже — просадка на 19 пунктов мельче. Но по конечному
    капиталу и по Шарпу она уступает индексу: премия за отбор бумаг не перекрыла того, что
    лонг-онли книга держит меньше рыночного риска.</p>
  </div>
  <div class="grid-2">
    <div class="panel">
      <figure>
        <svg id="eq-chart" viewBox="0 0 720 340" role="img"
             aria-label="Кривая капитала стратегии против индекса IMOEX, 2015–2025"></svg>
        <figcaption>Нетто-капитал стратегии против IMOEX (обе линии от 1,00 на старте).
        Ниже — просадка стратегии на той же оси времени.</figcaption>
      </figure>
      <div class="legend">
        <span><i style="background:var(--pos)"></i>моментум, нетто</span>
        <span><i style="background:var(--ref)"></i>IMOEX (ориентир)</span>
      </div>
    </div>
    <div class="panel">
      <div class="tbl-wrap">
        <table>
          <caption class="sr-only" style="position:absolute;left:-9999px">Доходность по годам</caption>
          <thead><tr><th>Период</th><th>Нетто</th><th style="width:60px"></th><th>Sharpe</th><th>Просадка</th></tr></thead>
          <tbody id="year-body"></tbody>
        </table>
      </div>
      <dl class="tiles" id="bench-tiles" style="margin-top:16px"></dl>
      <p class="note" style="margin-top:12px">Две последние строки таблицы — режимный сплит вокруг
      остановки торгов 24 февраля 2022; он встроен в отчёт движка, а не досчитан вручную.</p>
    </div>
  </div>
</section>

<section>
  <div class="head">
    <p class="sec-label">Устойчивость параметров</p>
    <h2>Свип: 12 комбинаций окна формирования и доли портфеля</h2>
    <p class="note">Ровная поверхность значит, что результат не держится на одной удачной ячейке.
    Здесь она ровная по строкам, но заметно проседает к длинным окнам — это сигнал о режиме рынка,
    а не приглашение выбрать лучшую клетку.</p>
  </div>
  <div class="grid-2">
    <div class="panel"><div class="heat" id="heat"></div>
      <div class="legend"><span>Нетто-Sharpe: <span class="num" id="heat-min"></span> → <span class="num" id="heat-max"></span></span></div>
    </div>
    <div>
      <div class="callout">
        <h3>Соблазн переподгонки</h3>
        <p>Лучшая ячейка даёт Sharpe на 55&nbsp;% выше дефолтной. Это ровно тот эффект, о котором
        предупреждает <em>research/04-critique.md</em>: при 12 испытаниях максимум смещён вверх.
        Правильное чтение — вся поверхность, а не её максимум.</p>
      </div>
      <dl class="tiles" id="cost-tiles"></dl>
      <p class="note" style="margin-top:12px">Издержки за 10,5 лет для моментума: комиссия и спред
      съедают часть доходности, но не переворачивают знак — в отличие от разворотных стратегий.</p>
    </div>
  </div>
</section>

<section>
  <div class="head">
    <p class="sec-label">Обратный пример</p>
    <h2>Краткосрочный разворот: как издержки переворачивают знак</h2>
  </div>
  <div class="grid-2">
    <div class="panel">
      <figure>
        <svg id="rev-chart" viewBox="0 0 720 220" role="img"
             aria-label="Брутто- и нетто-капитал стратегии краткосрочного разворота"></svg>
        <figcaption>Нетто-капитал стратегии от 1,00. Оборот — 39× в год: каждая сделка платит спред, и за 10,5 лет от рубля остаётся 10 копеек.</figcaption>
      </figure>

    </div>
    <div>
      <p>Корпус отводит этой стратегии Sharpe 0,3–0,7 — но с оговоркой, что «издержки решают знак».
      На MOEX с реалистичными 7 базисными пунктами за сделку знак оказался отрицательным:
      <strong class="num neg-t">−0,73</strong>.</p>
      <p class="note">Это и есть главная ценность прогона. Стратегия не «сломалась» —
      она работает ровно так, как описано, и именно поэтому её нельзя торговать на этих издержках.
      Чтобы вытащить её в плюс, нужны либо мид-квоты вместо цен сделок, либо комиссии
      институционального уровня.</p>
    </div>
  </div>
</section>

<section>
  <div class="head">
    <p class="sec-label">Оговорки</p>
    <h2>Чего эти числа не доказывают</h2>
  </div>
  <div class="col">
    <ul class="clean">
      <li><strong>Выживший юниверс.</strong> Список из 28 бумаг — сегодняшние ликвидные имена.
      Компании, ушедшие с биржи за десять лет, в выборке отсутствуют, и это смещает результаты
      вверх — тот самый survivorship bias, который корпус называет фатальным для кросс-секционных
      тестов. Точные PIT-составы индекса из ISS доступны, но в этот прогон не подключены.</li>
      <li><strong>Один рынок, 10,5 лет.</strong> Для моментума корпус требует 20+ лет и несколько
      режимов. Здесь один рынок и один структурный разлом (2022), так что доверительные интервалы
      широкие: t-статистика лучшей стратегии — <span class="num">1,61</span>.</li>
      <li><strong>Без деления на длинную и короткую ногу.</strong> Шорт российских акций после 2022
      ограничен, поэтому кросс-секционные стратегии считались лонг-онли — это ближе к реальности,
      но убирает часть теоретической премии.</li>
      <li><strong>Дивиденды учтены, налоги — нет.</strong> Total-return ряды строятся из дивидендов
      ISS; налог и проскальзывание сверх спреда в модель не заложены.</li>
    </ul>
    <p>Всё, что нужно, чтобы это исправить, в терминале уже есть: PIT-составы индекса, история
    делистингов и калибровка спреда по ALGOPACK — вопрос следующего прогона, а не переписывания движка.</p>
  </div>
</section>

<footer>
  <p>Сгенерировано из результатов qbt · ветка <span class="num">claude/trading-strategies-research-qhrq6q</span> ·
  каждая стратегия проходит харнесс на подглядывание в будущее и проверку монотонности по издержкам
  (103 теста). Метрики — нетто, после комиссии, спреда и лага исполнения в один бар.</p>
</footer>
</div>

<div id="tip" role="tooltip"></div>

<script>
const DATA = __PAYLOAD__;
const $ = (s, r) => (r || document).querySelector(s);
const fmt = (v, d) => v === null || v === undefined || !isFinite(v) ? "—" : v.toFixed(d === undefined ? 2 : d);
const pct = v => v === null || v === undefined || !isFinite(v) ? "—" : (100 * v).toFixed(1) + "%";
const tip = $("#tip");

function showTip(html, ev) {
  tip.innerHTML = html; tip.style.opacity = "1";
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
const hideTip = () => { tip.style.opacity = "0"; };

/* ---------- Sharpe spine ---------- */
(function () {
  const rows = [...DATA.strategies].sort((a, b) => b.sharpe - a.sharpe);
  const lo = Math.min(-0.9, ...rows.map(r => r.sharpe));
  const hi = Math.max(0.9, ...rows.map(r => r.sharpe));
  const span = hi - lo;
  const x = v => ((v - lo) / span) * 100;
  const host = $("#spine");
  const bench = DATA.benchmark.sharpe;
  rows.forEach(r => {
    const el = document.createElement("div");
    el.className = "spine-row";
    const zero = x(0), val = x(r.sharpe);
    const barL = Math.min(zero, val), barW = Math.abs(val - zero);
    let corpus = "";
    if (r.corpus) {
      const cl = x(r.corpus[0]), cw = x(r.corpus[1]) - cl;
      corpus = `<div class="spine-corpus" style="left:${cl}%;width:${cw}%"></div>`;
    }
    el.innerHTML =
      `<div class="spine-name">${r.name}<span class="fam">${r.family_ru}</span></div>
       <div class="spine-track">
         ${corpus}
         <div class="spine-zero" style="left:${zero}%"></div>
         <div class="spine-bench" style="left:${x(bench)}%"></div>
         <div class="spine-bar ${r.sharpe >= 0 ? "pos" : "neg"}" style="left:${barL}%;width:${barW}%"></div>
       </div>
       <div class="spine-val">${fmt(r.sharpe)}</div>`;
    el.addEventListener("mousemove", ev => showTip(
      `<div class="t-h">${r.name}</div>
       <div class="t-r"><span>Sharpe</span><span>${fmt(r.sharpe)}</span></div>
       <div class="t-r"><span>CAGR</span><span>${pct(r.cagr)}</span></div>
       <div class="t-r"><span>Волатильность</span><span>${pct(r.ann_vol)}</span></div>
       <div class="t-r"><span>Макс. просадка</span><span>${pct(r.max_dd)}</span></div>
       <div class="t-r"><span>Оборот, ×/год</span><span>${fmt(r.turnover, 1)}</span></div>
       <div class="t-r"><span>Издержки, бп/год</span><span>${fmt(r.cost_bps, 0)}</span></div>
       <div class="t-r"><span>Прогноз корпуса</span><span>${r.corpus ? r.corpus[0].toFixed(1) + "–" + r.corpus[1].toFixed(1) : "—"}</span></div>
       <div class="t-r"><span>Док</span><span>${r.doc}</span></div>`, ev));
    el.addEventListener("mouseleave", hideTip);
    host.appendChild(el);
  });
  const ax = $("#spine-axis");
  [-0.8, -0.4, 0, 0.4, 0.8].forEach(t => {
    if (t < lo || t > hi) return;
    const s = document.createElement("span");
    s.style.left = x(t) + "%"; s.textContent = t.toFixed(1);
    ax.appendChild(s);
  });
})();

/* ---------- shared line-chart builder ---------- */
function lineChart(svgId, cfg) {
  const svg = document.getElementById(svgId);
  const W = cfg.w, H = cfg.h, m = cfg.m;
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const all = cfg.series.flatMap(s => s.data.map(d => d[1]));
  const ymin = cfg.ymin !== undefined ? cfg.ymin : Math.min(...all);
  const ymax = cfg.ymax !== undefined ? cfg.ymax : Math.max(...all);
  const dates = cfg.series[0].data.map(d => d[0]);
  const X = i => m.l + (i / (dates.length - 1)) * iw;
  const Y = v => m.t + ih - ((v - ymin) / (ymax - ymin)) * ih;
  const NS = "http://www.w3.org/2000/svg";
  const mk = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };

  (cfg.yTicks || []).forEach(t => {
    svg.appendChild(mk("line", { x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t), class: "grid-line" }));
    const lb = mk("text", { x: m.l - 8, y: Y(t) + 3, class: "axis-txt", "text-anchor": "end" });
    lb.textContent = cfg.yFmt ? cfg.yFmt(t) : t;
    svg.appendChild(lb);
  });
  const years = {};
  dates.forEach((d, i) => { const y = d.slice(0, 4); if (!(y in years) && y % 2 === 1) years[y] = i; });
  Object.entries(years).forEach(([y, i]) => {
    const lb = mk("text", { x: X(i), y: H - 4, class: "axis-txt", "text-anchor": "middle" });
    lb.textContent = y; svg.appendChild(lb);
  });

  cfg.series.forEach(s => {
    if (s.area) {
      let d = `M ${X(0)} ${Y(0)}`;
      s.data.forEach((p, i) => { d += ` L ${X(i)} ${Y(p[1])}`; });
      d += ` L ${X(s.data.length - 1)} ${Y(0)} Z`;
      svg.appendChild(mk("path", { d, fill: s.color, "fill-opacity": ".18", stroke: "none" }));
    }
    let d = "";
    s.data.forEach((p, i) => { d += (i ? " L " : "M ") + X(i) + " " + Y(p[1]); });
    svg.appendChild(mk("path", { d, class: "series-line", stroke: s.color,
      "stroke-dasharray": s.dash || "none" }));
    if (s.label) {
      const last = s.data[s.data.length - 1];
      const t = mk("text", { x: X(s.data.length - 1) + 6, y: Y(last[1]) + 4,
        class: "axis-txt", fill: s.color, "font-size": "11" });
      t.textContent = s.label; svg.appendChild(t);
    }
  });

  const ch = mk("line", { class: "crosshair", y1: m.t, y2: m.t + ih });
  svg.appendChild(ch);
  const hit = mk("rect", { x: m.l, y: m.t, width: iw, height: ih, fill: "transparent" });
  svg.appendChild(hit);
  hit.addEventListener("mousemove", ev => {
    const r = svg.getBoundingClientRect();
    const rel = (ev.clientX - r.left) / r.width * W;
    let i = Math.round((rel - m.l) / iw * (dates.length - 1));
    i = Math.max(0, Math.min(dates.length - 1, i));
    ch.setAttribute("x1", X(i)); ch.setAttribute("x2", X(i)); ch.style.opacity = ".8";
    showTip(`<div class="t-h">${dates[i]}</div>` + cfg.series.map(s =>
      `<div class="t-r"><span>${s.name}</span><span>${cfg.tipFmt(s.data[i][1])}</span></div>`).join(""), ev);
  });
  hit.addEventListener("mouseleave", () => { ch.style.opacity = "0"; hideTip(); });
}

/* ---------- equity + drawdown ---------- */
(function () {
  const r = DATA.runs.xs_equity_momentum;
  lineChart("eq-chart", {
    w: 720, h: 340, m: { l: 40, r: 54, t: 10, b: 132 },
    ymin: 0.8, ymax: Math.max(...r.equity.map(d => d[1])) * 1.05,
    yTicks: [1, 2, 3, 4], yFmt: v => v.toFixed(0) + "×",
    tipFmt: v => v.toFixed(2) + "×",
    series: [
      { name: "IMOEX", data: r.benchmark, color: "var(--ref)", dash: "5 4" },
      { name: "Моментум", data: r.equity, color: "var(--pos)", label: "×" + r.equity[r.equity.length - 1][1].toFixed(1) },
    ],
  });
  const svg = document.getElementById("eq-chart");
  const NS = "http://www.w3.org/2000/svg";
  const g = document.createElementNS(NS, "g");
  const top = 250, h = 66, l = 40, w = 720 - 40 - 54;
  const Y = v => top + (-v / 0.6) * h;
  const X = i => l + (i / (r.dd.length - 1)) * w;
  let d = `M ${X(0)} ${Y(0)}`;
  r.dd.forEach((p, i) => { d += ` L ${X(i)} ${Y(Math.max(p[1], -0.6))}`; });
  d += ` L ${X(r.dd.length - 1)} ${Y(0)} Z`;
  const path = document.createElementNS(NS, "path");
  path.setAttribute("d", d); path.setAttribute("fill", "var(--neg)");
  path.setAttribute("fill-opacity", ".2"); path.setAttribute("stroke", "var(--neg)");
  path.setAttribute("stroke-width", "1.5");
  g.appendChild(path);
  [0, -0.25, -0.5].forEach(t => {
    const ln = document.createElementNS(NS, "line");
    ln.setAttribute("x1", l); ln.setAttribute("x2", l + w);
    ln.setAttribute("y1", Y(t)); ln.setAttribute("y2", Y(t));
    ln.setAttribute("class", "grid-line"); g.appendChild(ln);
    const tx = document.createElementNS(NS, "text");
    tx.setAttribute("x", l - 8); tx.setAttribute("y", Y(t) + 3);
    tx.setAttribute("class", "axis-txt"); tx.setAttribute("text-anchor", "end");
    tx.textContent = (t * 100).toFixed(0) + "%"; g.appendChild(tx);
  });
  const lb = document.createElementNS(NS, "text");
  lb.setAttribute("x", l); lb.setAttribute("y", top - 8);
  lb.setAttribute("class", "axis-txt"); lb.textContent = "ПРОСАДКА";
  g.appendChild(lb);
  svg.appendChild(g);
})();

/* ---------- per-year table ---------- */
(function () {
  const rows = DATA.runs.xs_equity_momentum.per_year;
  const body = $("#year-body");
  rows.forEach(r => {
    const isSplit = String(r.period).startsWith("pre") || String(r.period).startsWith("post");
    const label = String(r.period).replace("pre-2022-02-24", "до 24.02.2022")
      .replace("post-2022-03-24", "после 24.03.2022");
    const tr = document.createElement("tr");
    if (isSplit) tr.className = "split";
    const cap = 0.6, half = Math.min(Math.abs(r.net) / cap, 1) * 50;
    const bar = r.net >= 0
      ? `<span class="mb-fill" style="left:50%;width:${half}%;background:var(--pos)"></span>`
      : `<span class="mb-fill" style="right:50%;width:${half}%;background:var(--neg)"></span>`;
    tr.innerHTML =
      `<td>${label}</td>
       <td class="n">${pct(r.net)}</td>
       <td><span class="minibar"><span class="mb-zero"></span>${bar}</span></td>
       <td class="n">${fmt(r.sharpe_net)}</td>
       <td class="n">${pct(r.max_dd)}</td>`;
    body.appendChild(tr);
  });
})();

/* ---------- benchmark tiles ---------- */
(function () {
  const m = DATA.strategies.find(s => s.key === "xs_equity_momentum");
  const b = DATA.benchmark;
  const eq = DATA.runs.xs_equity_momentum.equity;
  const rows = [
    ["Итоговый капитал", eq[eq.length - 1][1].toFixed(2) + "×", b.final.toFixed(2) + "×"],
    ["Sharpe", m.sharpe.toFixed(2), b.sharpe.toFixed(2)],
    ["Волатильность", pct(m.ann_vol), pct(b.vol)],
    ["Макс. просадка", pct(m.max_dd), pct(b.max_dd)],
  ];
  const host = $("#bench-tiles");
  rows.forEach(([k, a, bb]) => {
    const d = document.createElement("div");
    d.className = "tile";
    d.innerHTML = `<dt>${k}</dt><dd>${a}</dd><div class="sub">IMOEX: <span class="num">${bb}</span></div>`;
    host.appendChild(d);
  });
})();

/* ---------- sweep heatmap ---------- */
(function () {
  const rows = DATA.sweep.filter(r => r.sharpe !== null);
  const forms = [...new Set(rows.map(r => r.formation))].sort((a, b) => a - b);
  const tops = [...new Set(rows.map(r => r.top_frac))].sort((a, b) => a - b);
  const vals = rows.map(r => r.sharpe);
  const min = Math.min(...vals), max = Math.max(...vals);
  $("#heat-min").textContent = min.toFixed(2);
  $("#heat-max").textContent = max.toFixed(2);
  const steps = ["--seq-1", "--seq-2", "--seq-3", "--seq-4", "--seq-5"];
  const host = $("#heat");
  host.style.gridTemplateColumns = `54px repeat(${forms.length}, 1fr)`;
  const corner = document.createElement("div");
  corner.className = "heat-lbl"; corner.textContent = "";
  host.appendChild(corner);
  forms.forEach(f => {
    const el = document.createElement("div");
    el.className = "heat-lbl"; el.textContent = f;
    host.appendChild(el);
  });
  tops.forEach(t => {
    const lb = document.createElement("div");
    lb.className = "heat-lbl"; lb.textContent = (100 * t).toFixed(0) + "%";
    host.appendChild(lb);
    forms.forEach(f => {
      const r = rows.find(x => x.formation === f && x.top_frac === t);
      const cell = document.createElement("div");
      cell.className = "heat-cell";
      if (!r) { cell.textContent = "—"; host.appendChild(cell); return; }
      const k = Math.min(steps.length - 1, Math.floor((r.sharpe - min) / (max - min + 1e-9) * steps.length));
      cell.style.background = `var(${steps[k]})`;
      cell.style.color = k >= 3 ? "#fff" : "var(--ink)";
      cell.textContent = r.sharpe.toFixed(2);
      cell.addEventListener("mousemove", ev => showTip(
        `<div class="t-h">окно ${f} баров · доля ${(100 * t).toFixed(0)}%</div>
         <div class="t-r"><span>Sharpe</span><span>${fmt(r.sharpe)}</span></div>
         <div class="t-r"><span>CAGR</span><span>${pct(r.cagr)}</span></div>
         <div class="t-r"><span>Просадка</span><span>${pct(r.max_dd)}</span></div>
         <div class="t-r"><span>Оборот</span><span>${fmt(r.turnover_ann, 1)}×</span></div>`, ev));
      cell.addEventListener("mouseleave", hideTip);
      host.appendChild(cell);
    });
  });
  const cap = document.createElement("p");
  cap.className = "note";
  cap.style.marginTop = "10px";
  cap.textContent = "Столбцы — окно формирования (баров), строки — доля юниверса в лонге.";
  host.parentElement.appendChild(cap);
})();

/* ---------- cost tiles ---------- */
(function () {
  const c = DATA.runs.xs_equity_momentum.costs;
  const m = DATA.strategies.find(s => s.key === "xs_equity_momentum");
  const tiles = [
    ["Комиссия", pct(c.commission), "за 10,5 лет"],
    ["Спред", pct(c.spread), "за 10,5 лет"],
    ["Оборот", m.turnover.toFixed(1) + "×", "в год"],
    ["Итого дрейф", Math.round(m.cost_bps) + " бп", "в год"],
  ];
  const host = $("#cost-tiles");
  tiles.forEach(([k, v, s]) => {
    const d = document.createElement("div");
    d.className = "tile";
    d.innerHTML = `<dt>${k}</dt><dd>${v}</dd><div class="sub">${s}</div>`;
    host.appendChild(d);
  });
})();

/* ---------- reversal chart ---------- */
(function () {
  const r = DATA.runs.short_term_reversal;
  lineChart("rev-chart", {
    w: 720, h: 220, m: { l: 40, r: 54, t: 10, b: 26 },
    ymin: 0, ymax: 1.15,
    yTicks: [0, 0.25, 0.5, 0.75, 1], yFmt: v => v.toFixed(2) + "×",
    tipFmt: v => v.toFixed(3) + "×",
    series: [
      { name: "Разворот, нетто", data: r.equity, color: "var(--neg)", area: true,
        label: "×" + r.equity[r.equity.length - 1][1].toFixed(2) },
    ],
  });
})();
</script>
"""

OUT.write_text(HTML.replace("__PAYLOAD__", payload), encoding="utf-8")
print("written", OUT, OUT.stat().st_size, "bytes")
