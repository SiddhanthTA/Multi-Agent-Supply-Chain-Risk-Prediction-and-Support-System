import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Bar,
  BarChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AlertTriangle, BarChart3, LoaderCircle, TrendingUp } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

const RANGE_OPTIONS = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
];

const SEVERITY_SERIES = [
  { key: 'critical', label: 'Critical', color: '#dc2626' },
  { key: 'high', label: 'High', color: '#f97316' },
  { key: 'medium', label: 'Medium', color: '#eab308' },
  { key: 'low', label: 'Low', color: '#22c55e' },
];

/**
 * SupplySentry's monitored intelligence begins here. Days before this date are
 * genuinely zero rather than a data gap, so the chart marks the boundary
 * instead of hiding it.
 */
const DATA_COLLECTION_START = '2026-09-21';

const CHART_AXIS = { fontSize: 11, fill: 'hsl(var(--muted-foreground))' };
const HIDE_NATIVE_TOOLTIP = { contentStyle: { display: 'none' } };

const shortDate = (value) => {
  try {
    return format(parseISO(value), 'MMM d');
  } catch {
    return value;
  }
};

const fetchTrends = async (days) => {
  const response = await api.get('/risks/trends', { params: { days } });
  return response.data;
};

function SummaryCard({ label, value, hint, valueClass = '' }) {
  return (
    <div className="ss-metric">
      <div className="ss-metric-label">{label}</div>
      <div className={`ss-metric-value ${valueClass}`}>{value}</div>
      {hint && <div className="mt-1.5 text-[11px] leading-snug text-muted-foreground">{hint}</div>}
    </div>
  );
}

/**
 * Day-over-day change, derived from the actual daily series.
 *
 * An absolute count is used instead of a percentage because the collection
 * history is still short, where a percentage produces meaningless magnitudes.
 * When the previous day has no activity there is simply no baseline.
 */
function dailyChange(daily) {
  if (!Array.isArray(daily) || daily.length < 2) {
    return { value: null, previous: null, hasBaseline: false };
  }
  const current = Number(daily[daily.length - 1]?.total ?? 0);
  const previous = Number(daily[daily.length - 2]?.total ?? 0);
  return { value: current - previous, previous, hasBaseline: previous > 0 };
}

/** Label for the data-collection marker, or null when it is out of range. */
function dataStartMarkerLabel(daily, isoDate) {
  return daily.some((row) => row.date === isoDate) ? shortDate(isoDate) : null;
}

/**
 * Risk Trends: deterministic historical analytics over stored Risks.
 * Values come from the API and are never smoothed, forecast, or invented.
 */
export default function RiskTrendsPanel({ variant = 'card' }) {
  const [days, setDays] = useState(7);
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['riskTrends', days],
    queryFn: () => fetchTrends(days),
    staleTime: 5 * 60 * 1000,
  });

  const summary = data?.summary;
  const daily = (data?.daily || []).map((row) => ({ ...row, label: shortDate(row.date) }));
  const riskTypes = data?.risk_type_breakdown || [];
  const company = data?.company;
  const hasActivity = (summary?.total_risks || 0) > 0;
  const change = dailyChange(data?.daily);
  // Only annotate when the marker actually falls inside the selected range.
  const dataStartMarker = dataStartMarkerLabel(daily, DATA_COLLECTION_START);


  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className={`flex items-center gap-2 ${variant === 'page' ? 'text-xl' : 'text-base'}`}>
              <TrendingUp className="h-4 w-4 text-primary" /> Risk Trends
            </CardTitle>
            <CardDescription>
              Historical risk activity from SupplySentry&apos;s monitored intelligence.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {RANGE_OPTIONS.map((option) => (
              <Button
                key={option.value}
                size="sm"
                variant={days === option.value ? 'default' : 'outline'}
                onClick={() => setDays(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {isLoading ? (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <LoaderCircle className="h-4 w-4 animate-spin" /> Loading risk trends…
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
            <div className="flex items-start gap-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Risk trends unavailable.</p>
                <button type="button" onClick={() => refetch()} className="mt-2 underline underline-offset-2">
                  Retry
                </button>
              </div>
            </div>
          </div>
        ) : !hasActivity ? (
          <p className="py-6 text-sm text-muted-foreground">
            No risk activity found for this period.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <SummaryCard label="Total Risks" value={summary.total_risks} />
              <SummaryCard
                label="High / Critical"
                value={summary.high_critical_risks}
                hint={`of ${summary.total_risks} detected risks`}
              />
              <SummaryCard label="Active Risks" value={summary.active_risks} />
              <SummaryCard
                label="Daily Change"
                value={
                  !change.hasBaseline ? '—' : `${change.value > 0 ? '+' : ''}${change.value}`
                }
                valueClass={
                  !change.hasBaseline || change.value === 0
                    ? ''
                    : change.value > 0
                      ? 'text-destructive'
                      : 'text-emerald-500'
                }
                hint={
                  !change.hasBaseline
                    ? 'No previous-day baseline'
                    : change.value === 0
                      ? 'Unchanged vs previous day'
                      : `${Math.abs(change.value)} ${Math.abs(change.value) === 1 ? 'risk' : 'risks'} vs previous day`
                }
              />
            </div>

            <div>
              <h4 className="ss-section-title mb-2">Risk volume over time</h4>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={daily} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} />
                    <XAxis dataKey="label" tick={CHART_AXIS} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis allowDecimals={false} tick={CHART_AXIS} tickLine={false} axisLine={false} width={44} />
                    <Tooltip
                      cursor={{ stroke: 'hsl(var(--primary))', strokeWidth: 1, strokeOpacity: 0.4 }}
                      contentStyle={HIDE_NATIVE_TOOLTIP}
                      content={<TrendTooltip />}
                    />
                    {dataStartMarker && (
                      <ReferenceLine
                        x={dataStartMarker}
                        stroke="hsl(var(--muted-foreground))"
                        strokeDasharray="4 4"
                        strokeWidth={1}
                        label={{
                          value: 'Data collection started',
                          position: 'insideTopRight',
                          fill: 'hsl(var(--muted-foreground))',
                          fontSize: 10,
                        }}
                      />
                    )}
                    <Line
                      type="monotone"
                      dataKey="total"
                      name="Risks detected"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Days with no detected risks are shown as zero. Days before {shortDate(DATA_COLLECTION_START)}{' '}
                precede the start of monitored collection.
              </p>
            </div>

            <div>
              <h4 className="ss-section-title mb-2">Severity over time</h4>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={daily} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} />
                    <XAxis dataKey="label" tick={CHART_AXIS} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis allowDecimals={false} tick={CHART_AXIS} tickLine={false} axisLine={false} width={44} />
                    <Tooltip
                      cursor={{ stroke: 'hsl(var(--primary))', strokeWidth: 1, strokeOpacity: 0.4 }}
                      contentStyle={HIDE_NATIVE_TOOLTIP}
                      content={<TrendTooltip />}
                    />
                    <Legend
                      verticalAlign="top"
                      align="right"
                      height={24}
                      iconType="plainline"
                      iconSize={12}
                      wrapperStyle={{ fontSize: 11, color: 'hsl(var(--muted-foreground))' }}
                    />
                    {SEVERITY_SERIES.map((series) => (
                      <Line
                        key={series.key}
                        type="monotone"
                        dataKey={series.key}
                        name={series.label}
                        stroke={series.color}
                        strokeWidth={1.75}
                        dot={false}
                        activeDot={{ r: 3 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Severity is used exactly as recorded on each risk.
              </p>
            </div>

            {riskTypes.length > 0 && (
              <div>
                <h4 className="ss-section-title mb-2 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" /> Risk types recorded
                </h4>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={riskTypes} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} />
                      <XAxis dataKey="name" tick={CHART_AXIS} tickLine={false} axisLine={false} interval={0} />
                      <YAxis allowDecimals={false} tick={CHART_AXIS} tickLine={false} axisLine={false} width={44} />
                      <Tooltip
                        cursor={{ fill: 'hsl(var(--primary))', fillOpacity: 0.06 }}
                        contentStyle={HIDE_NATIVE_TOOLTIP}
                        content={<TrendTooltip />}
                      />
                      <Bar dataKey="count" name="Risks" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={48} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">
                  Recorded risk types during the selected period.
                </p>
              </div>
            )}

            {company?.available && (
              <div>
                <h4 className="ss-section-title mb-2">Company-relevant risks</h4>
                {company.total_relevant === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No company-relevant risk signals identified in this period.
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-foreground">
                      {company.total_relevant} risks matched configured company dependencies during this period.
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {company.direct} were directly relevant and {company.indirect} were indirectly relevant. This reflects configured dependencies only and does not indicate financial exposure.
                    </p>
                    {company.dependencies.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {company.dependencies.map((item) => (
                          <Badge key={item.dependency} variant="secondary">
                            {item.dependency} — {item.count}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            <p className="border-t border-border/60 pt-3 text-xs text-muted-foreground">
              Historical analytics only. These figures describe recorded activity and are not a forecast of future risk.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/** Themed tooltip so charts match the rest of the application. */
function TrendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="ss-chart-tooltip rounded-lg">
      <div className="label">{label}</div>
      <ul className="space-y-0.5">
        {payload.map((item) => (
          <li key={item.dataKey} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: item.color || item.stroke || item.fill }}
            />
            <span className="text-muted-foreground">{item.name}</span>
            <span className="ml-auto font-medium tabular-nums text-foreground">{item.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
