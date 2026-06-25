"use client";

import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  ChartData,
  ChartOptions,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import {
  BarChart3,
  Download,
  LineChart,
  Plus,
  RotateCcw,
  Trash2,
} from "lucide-react";
import { Chart } from "react-chartjs-2";
import {
  ChangeEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { getApiHealth } from "@/lib/api";
import {
  calculateScenario,
  ChartMode,
  formatMoney,
  formatSigned,
  INITIAL_ROWS,
  Metric,
  nextPeriod,
  PeriodRow,
  PRESETS,
  PresetName,
  ScenarioDrivers,
} from "@/lib/scenario";

ChartJS.register(
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
);

const METRIC_CONFIG: Record<Metric, { label: string; color: string }> = {
  revenue: { label: "Revenue", color: "#2878b5" },
  ebitda: { label: "EBITDA", color: "#2a9d8f" },
  fcf: { label: "Free cash flow", color: "#e2a93b" },
};

const DRIVER_CONFIG: Array<{
  key: keyof ScenarioDrivers;
  label: string;
  min: number;
  max: number;
}> = [
  { key: "revenueGrowth", label: "Revenue growth", min: -15, max: 30 },
  { key: "pricing", label: "Pricing impact", min: -10, max: 15 },
  { key: "volume", label: "Volume impact", min: -15, max: 20 },
  { key: "costInflation", label: "Cost inflation", min: -5, max: 20 },
  { key: "fx", label: "FX impact", min: -10, max: 10 },
];

const copyInitialRows = () => INITIAL_ROWS.map((row) => ({ ...row }));

export function ScenarioWorkbench() {
  const [rows, setRows] = useState<PeriodRow[]>(copyInitialRows);
  const [drivers, setDrivers] = useState<ScenarioDrivers>({ ...PRESETS.base });
  const [preset, setPresetName] = useState<PresetName>("base");
  const [chartMode, setChartMode] = useState<ChartMode>("line");
  const [activeTab, setActiveTab] = useState<"drivers" | "data">("drivers");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [metrics, setMetrics] = useState<Record<Metric, boolean>>({
    revenue: true,
    ebitda: true,
    fcf: false,
  });
  const chartRef =
    useRef<ChartJS<ChartMode, number[], string> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getApiHealth(controller.signal).then(setApiOnline);
    return () => controller.abort();
  }, []);

  const scenarioRows = useMemo(
    () => calculateScenario(rows, drivers),
    [rows, drivers],
  );

  const finalBase = rows.at(-1) ?? INITIAL_ROWS.at(-1)!;
  const finalScenario = scenarioRows.at(-1) ?? finalBase;
  const baseMargin = (finalBase.ebitda / finalBase.revenue) * 100;
  const scenarioMargin =
    (finalScenario.ebitda / finalScenario.revenue) * 100;

  const revenueEffect =
    drivers.revenueGrowth + drivers.pricing + drivers.volume + drivers.fx;
  const marginEffect =
    drivers.pricing + drivers.volume + drivers.fx - drivers.costInflation;

  const chartData = useMemo<ChartData<ChartMode, number[], string>>(() => {
    const datasets = (Object.keys(metrics) as Metric[]).flatMap((metric) => {
      if (!metrics[metric]) return [];
      const config = METRIC_CONFIG[metric];
      return [
        {
          label: `${config.label} - Base`,
          data: rows.map((row) => row[metric]),
          borderColor: `${config.color}70`,
          backgroundColor: `${config.color}26`,
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: chartMode === "line" ? 2 : 0,
          tension: 0.28,
        },
        {
          label: `${config.label} - Scenario`,
          data: scenarioRows.map((row) => row[metric]),
          borderColor: config.color,
          backgroundColor: `${config.color}c9`,
          borderWidth: 2.5,
          pointRadius: chartMode === "line" ? 4 : 0,
          pointBackgroundColor: "#ffffff",
          pointBorderWidth: 2,
          tension: 0.28,
        },
      ];
    });

    return {
      labels: rows.map((row) => row.period),
      datasets,
    };
  }, [chartMode, metrics, rows, scenarioRows]);

  const chartOptions = useMemo<ChartOptions<ChartMode>>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 220 },
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: { color: "#64748b", font: { size: 11, weight: 600 } },
        },
        y: {
          beginAtZero: true,
          border: { display: false },
          grid: { color: "#e2e8f0" },
          ticks: {
            color: "#64748b",
            callback: (value) => `$${value}M`,
          },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          align: "start",
          labels: {
            color: "#475569",
            boxWidth: 18,
            boxHeight: 2,
            padding: 18,
            font: { size: 10, weight: 600 },
          },
        },
        tooltip: {
          backgroundColor: "#15253d",
          padding: 11,
          displayColors: true,
          callbacks: {
            label: (context) =>
              `${context.dataset.label}: ${formatMoney(Number(context.raw))}`,
          },
        },
      },
    }),
    [],
  );

  const sensitivity = useMemo(() => {
    const growthValues = [
      drivers.revenueGrowth - 10,
      drivers.revenueGrowth - 5,
      drivers.revenueGrowth,
      drivers.revenueGrowth + 5,
      drivers.revenueGrowth + 10,
    ];
    const costValues = [
      Math.max(drivers.costInflation - 6, -5),
      Math.max(drivers.costInflation - 3, -5),
      drivers.costInflation,
      drivers.costInflation + 3,
      drivers.costInflation + 6,
    ];
    const values = costValues.map((costInflation) =>
      growthValues.map((revenueGrowth) => {
        const scenario = calculateScenario(rows, {
          ...drivers,
          revenueGrowth,
          costInflation,
        }).at(-1)!;
        return (scenario.ebitda / scenario.revenue) * 100;
      }),
    );
    const flat = values.flat();

    return {
      growthValues,
      costValues,
      values,
      min: Math.min(...flat),
      max: Math.max(...flat),
    };
  }, [drivers, rows]);

  const selectPreset = useCallback(
    (name: Exclude<PresetName, "custom">) => {
      setDrivers({ ...PRESETS[name] });
      setPresetName(name);
    },
    [],
  );

  const updateDriver = (
    key: keyof ScenarioDrivers,
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    setDrivers((current) => ({
      ...current,
      [key]: Number(event.target.value),
    }));
    setPresetName("custom");
  };

  const toggleMetric = (metric: Metric) => {
    setMetrics((current) => {
      const next = { ...current, [metric]: !current[metric] };
      return Object.values(next).some(Boolean) ? next : current;
    });
  };

  const updateRow = (
    index: number,
    field: keyof PeriodRow,
    value: string,
  ) => {
    setRows((current) =>
      current.map((row, rowIndex) => {
        if (rowIndex !== index) return row;
        return {
          ...row,
          [field]:
            field === "period" ? value : Math.max(Number(value) || 0, 0),
        };
      }),
    );
    setPresetName("custom");
  };

  const resetModel = () => {
    setRows(copyInitialRows());
    setDrivers({ ...PRESETS.base });
    setPresetName("base");
    setChartMode("line");
    setMetrics({ revenue: true, ebitda: true, fcf: false });
  };

  const exportChart = () => {
    const image = chartRef.current?.toBase64Image("image/png", 1);
    if (!image) return;
    const link = document.createElement("a");
    link.download = `kapexai-${preset}-scenario.png`;
    link.href = image;
    link.click();
  };

  const kpis = [
    {
      label: "Revenue",
      value: formatMoney(finalScenario.revenue),
      delta: ((finalScenario.revenue / finalBase.revenue) - 1) * 100,
      suffix: "% vs base",
    },
    {
      label: "EBITDA",
      value: formatMoney(finalScenario.ebitda),
      delta: ((finalScenario.ebitda / finalBase.ebitda) - 1) * 100,
      suffix: "% vs base",
    },
    {
      label: "EBITDA margin",
      value: `${scenarioMargin.toFixed(1)}%`,
      delta: scenarioMargin - baseMargin,
      suffix: " pts vs base",
    },
    {
      label: "Free cash flow",
      value: formatMoney(finalScenario.fcf),
      delta: ((finalScenario.fcf / finalBase.fcf) - 1) * 100,
      suffix: "% vs base",
    },
  ];

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">K</span>
          <div>
            <strong>KapexAI</strong>
            <span>Scenario Workbench</span>
          </div>
          <span
            className={`api-status ${
              apiOnline === true
                ? "online"
                : apiOnline === false
                  ? "offline"
                  : ""
            }`}
          >
            {apiOnline === null
              ? "API checking"
              : apiOnline
                ? "API online"
                : "API offline"}
          </span>
        </div>

        <div className="topbar-actions">
          <div className="segmented" aria-label="Scenario preset">
            {(["base", "upside", "downside"] as const).map((name) => (
              <button
                className={`segment ${preset === name ? "active" : ""}`}
                key={name}
                type="button"
                onClick={() => selectPreset(name)}
              >
                {name.charAt(0).toUpperCase() + name.slice(1)}
              </button>
            ))}
            <button
              className={`segment ${preset === "custom" ? "active" : ""}`}
              type="button"
              onClick={() => setPresetName("custom")}
            >
              Custom
            </button>
          </div>
          <button
            className="button secondary"
            type="button"
            onClick={resetModel}
          >
            <RotateCcw size={15} />
            Reset
          </button>
          <button
            className="button primary"
            type="button"
            onClick={exportChart}
          >
            <Download size={15} />
            Export PNG
          </button>
        </div>
      </header>

      <main className="workspace">
        <section className="analysis-pane">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Five-year operating model</p>
              <h1>Financial outlook</h1>
            </div>
            <div className="segmented compact" aria-label="Chart type">
              <button
                className={`segment ${chartMode === "line" ? "active" : ""}`}
                type="button"
                onClick={() => setChartMode("line")}
              >
                <LineChart size={14} />
                Trend
              </button>
              <button
                className={`segment ${chartMode === "bar" ? "active" : ""}`}
                type="button"
                onClick={() => setChartMode("bar")}
              >
                <BarChart3 size={14} />
                Columns
              </button>
            </div>
          </div>

          <section className="kpi-strip" aria-label="Scenario summary">
            {kpis.map((kpi) => (
              <div className="kpi" key={kpi.label}>
                <span>{kpi.label}</span>
                <strong>{kpi.value}</strong>
                <small
                  className={
                    kpi.delta > 0
                      ? "positive"
                      : kpi.delta < 0
                        ? "negative"
                        : ""
                  }
                >
                  {formatSigned(kpi.delta, kpi.suffix)}
                </small>
              </div>
            ))}
          </section>

          <section className="chart-panel">
            <div className="chart-toolbar">
              <div className="metric-toggles" aria-label="Visible metrics">
                {(Object.keys(METRIC_CONFIG) as Metric[]).map((metric) => (
                  <label key={metric}>
                    <input
                      type="checkbox"
                      checked={metrics[metric]}
                      onChange={() => toggleMetric(metric)}
                    />
                    {METRIC_CONFIG[metric].label}
                  </label>
                ))}
              </div>
              <span className="scenario-name">
                {preset.charAt(0).toUpperCase() + preset.slice(1)} scenario
              </span>
            </div>
            <div className="chart-frame">
              <Chart
                key={chartMode}
                ref={chartRef}
                type={chartMode}
                data={chartData}
                options={chartOptions}
                aria-label="Financial scenario chart"
              />
            </div>
          </section>

          <section className="sensitivity-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Sensitivity</p>
                <h2>EBITDA margin matrix</h2>
              </div>
              <span>Revenue growth x cost inflation</span>
            </div>
            <div className="sensitivity-layout">
              <div className="sensitivity-axis">
                <span>Cost inflation</span>
              </div>
              <div className="sensitivity-table-wrap">
                <table className="sensitivity-table">
                  <thead>
                    <tr>
                      <th aria-label="Cost inflation" />
                      {sensitivity.growthValues.map((value) => (
                        <th key={value}>{value.toFixed(0)}%</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sensitivity.values.map((valueRow, rowIndex) => (
                      <tr key={sensitivity.costValues[rowIndex]}>
                        <th>{sensitivity.costValues[rowIndex].toFixed(0)}%</th>
                        {valueRow.map((margin, columnIndex) => {
                          const normalized =
                            (margin - sensitivity.min) /
                            Math.max(sensitivity.max - sensitivity.min, 0.01);
                          const hue = 2 + normalized * 156;
                          return (
                            <td
                              className={
                                rowIndex === 2 && columnIndex === 2
                                  ? "current"
                                  : ""
                              }
                              key={`${rowIndex}-${columnIndex}`}
                              style={{
                                backgroundColor: `hsl(${hue} 52% 43%)`,
                              }}
                            >
                              {margin.toFixed(1)}%
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <span className="horizontal-axis">Revenue growth</span>
              </div>
            </div>
          </section>
        </section>

        <aside className="control-panel">
          <div className="control-tabs" role="tablist">
            <button
              className={`control-tab ${
                activeTab === "drivers" ? "active" : ""
              }`}
              type="button"
              onClick={() => setActiveTab("drivers")}
            >
              Drivers
            </button>
            <button
              className={`control-tab ${
                activeTab === "data" ? "active" : ""
              }`}
              type="button"
              onClick={() => setActiveTab("data")}
            >
              Period data
            </button>
          </div>

          {activeTab === "drivers" ? (
            <section className="tab-content active">
              <div className="control-heading">
                <h2>Scenario drivers</h2>
                <span>Live</span>
              </div>
              <div className="driver-list">
                {DRIVER_CONFIG.map((driver) => (
                  <label className="driver" key={driver.key}>
                    <span>
                      <b>{driver.label}</b>
                      <output>{drivers[driver.key].toFixed(1)}%</output>
                    </span>
                    <input
                      type="range"
                      min={driver.min}
                      max={driver.max}
                      step="0.5"
                      value={drivers[driver.key]}
                      onChange={(event) => updateDriver(driver.key, event)}
                    />
                  </label>
                ))}
              </div>
              <div className="driver-summary">
                <div>
                  <span>Revenue effect</span>
                  <strong>{formatSigned(revenueEffect)}</strong>
                </div>
                <div>
                  <span>Margin effect</span>
                  <strong>{formatSigned(marginEffect, " pts")}</strong>
                </div>
              </div>
            </section>
          ) : (
            <section className="tab-content active">
              <div className="control-heading">
                <h2>Base-period data</h2>
                <button
                  className="button secondary small"
                  type="button"
                  onClick={() => {
                    setRows((current) => [...current, nextPeriod(current)]);
                    setPresetName("custom");
                  }}
                >
                  <Plus size={14} />
                  Add period
                </button>
              </div>
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Revenue</th>
                      <th>EBITDA</th>
                      <th>FCF</th>
                      <th aria-label="Actions" />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, index) => (
                      <tr key={`${row.period}-${index}`}>
                        <td>
                          <input
                            className="period-input"
                            aria-label={`${row.period} period`}
                            value={row.period}
                            onChange={(event) =>
                              updateRow(index, "period", event.target.value)
                            }
                          />
                        </td>
                        {(["revenue", "ebitda", "fcf"] as const).map(
                          (field) => (
                            <td key={field}>
                              <input
                                aria-label={`${row.period} ${field}`}
                                type="number"
                                min="0"
                                step="0.5"
                                value={row[field]}
                                onChange={(event) =>
                                  updateRow(index, field, event.target.value)
                                }
                              />
                            </td>
                          ),
                        )}
                        <td>
                          <button
                            className="icon-button danger"
                            type="button"
                            title="Remove period"
                            aria-label={`Remove ${row.period}`}
                            disabled={rows.length <= 2}
                            onClick={() => {
                              setRows((current) =>
                                current.filter(
                                  (_, rowIndex) => rowIndex !== index,
                                ),
                              );
                              setPresetName("custom");
                            }}
                          >
                            <Trash2 size={15} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </aside>
      </main>
    </>
  );
}
