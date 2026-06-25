export type Metric = "revenue" | "ebitda" | "fcf";
export type ChartMode = "line" | "bar";
export type PresetName = "base" | "upside" | "downside" | "custom";

export interface PeriodRow {
  period: string;
  revenue: number;
  ebitda: number;
  fcf: number;
}

export interface ScenarioDrivers {
  revenueGrowth: number;
  pricing: number;
  volume: number;
  costInflation: number;
  fx: number;
}

export const INITIAL_ROWS: PeriodRow[] = [
  { period: "FY 2024", revenue: 82, ebitda: 16, fcf: 10 },
  { period: "FY 2025", revenue: 90, ebitda: 19, fcf: 12 },
  { period: "FY 2026E", revenue: 99, ebitda: 22, fcf: 14 },
  { period: "FY 2027E", revenue: 108, ebitda: 25, fcf: 17 },
  { period: "FY 2028E", revenue: 118, ebitda: 29, fcf: 20 },
];

export const PRESETS: Record<Exclude<PresetName, "custom">, ScenarioDrivers> = {
  base: {
    revenueGrowth: 8,
    pricing: 2,
    volume: 3,
    costInflation: 4,
    fx: -1,
  },
  upside: {
    revenueGrowth: 15,
    pricing: 4,
    volume: 7,
    costInflation: 2,
    fx: 1,
  },
  downside: {
    revenueGrowth: -4,
    pricing: -1,
    volume: -6,
    costInflation: 9,
    fx: -4,
  },
};

export function calculateScenario(
  rows: PeriodRow[],
  drivers: ScenarioDrivers,
): PeriodRow[] {
  const revenueEffect =
    drivers.revenueGrowth + drivers.pricing + drivers.volume + drivers.fx;
  const profitEffect =
    drivers.pricing + drivers.volume + drivers.fx - drivers.costInflation;

  return rows.map((row, index) => {
    const phaseIn = 0.45 + (index / Math.max(rows.length - 1, 1)) * 0.55;
    const revenue = row.revenue * (1 + (revenueEffect * phaseIn) / 100);
    const ebitda = row.ebitda + row.revenue * (profitEffect * phaseIn) / 100;
    const fcf = row.fcf + (ebitda - row.ebitda) * 0.68;

    return {
      period: row.period,
      revenue: Math.max(revenue, 0),
      ebitda: Math.max(ebitda, 0),
      fcf: Math.max(fcf, 0),
    };
  });
}

export function nextPeriod(rows: PeriodRow[]): PeriodRow {
  const previous = rows.at(-1) ?? INITIAL_ROWS.at(-1)!;
  const yearMatch = previous.period.match(/\d{4}/);
  const nextYear = yearMatch ? Number(yearMatch[0]) + 1 : rows.length + 1;

  return {
    period: `FY ${nextYear}E`,
    revenue: Number((previous.revenue * 1.08).toFixed(1)),
    ebitda: Number((previous.ebitda * 1.1).toFixed(1)),
    fcf: Number((previous.fcf * 1.1).toFixed(1)),
  };
}

export function formatMoney(value: number): string {
  return `$${value.toFixed(1)}M`;
}

export function formatSigned(value: number, suffix = "%"): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}${suffix}`;
}
