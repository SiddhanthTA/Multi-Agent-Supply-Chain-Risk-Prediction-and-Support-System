import { useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { BarChart3, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const DEMO_TREND = [
  { date: 'Sep 21', total: 2, High: 1, Medium: 1, Low: 0, Supplier: 1, Financial: 1, Political: 0 },
  { date: 'Sep 22', total: 3, High: 1, Medium: 1, Low: 1, Supplier: 1, Financial: 1, Political: 1 },
  { date: 'Sep 23', total: 2, High: 0, Medium: 1, Low: 1, Supplier: 1, Financial: 1, Political: 0 },
  { date: 'Sep 24', total: 3, High: 1, Medium: 1, Low: 1, Supplier: 1, Financial: 1, Political: 1 },
  { date: 'Sep 25', total: 2, High: 1, Medium: 0, Low: 1, Supplier: 1, Financial: 1, Political: 0 },
  { date: 'Sep 26', total: 3, High: 1, Medium: 1, Low: 1, Supplier: 1, Financial: 1, Political: 1 },
  { date: 'Sep 27', total: 3, High: 1, Medium: 1, Low: 1, Supplier: 1, Financial: 1, Political: 1 },
];

const RISK_TYPES = [
  { name: 'Supplier', count: 7 },
  { name: 'Financial', count: 7 },
  { name: 'Political', count: 4 },
];

const RANGE_OPTIONS = [{ value: 7, label: '7 days' }, { value: 14, label: '14 days' }, { value: 30, label: '30 days' }];

function TooltipContent({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="ss-chart-tooltip rounded-lg">
      <div className="label">{label}</div>
      {payload.map((item) => (
        <div key={item.dataKey} className="flex items-center justify-between gap-4 text-xs">
          <span className="text-muted-foreground">{item.name}</span>
          <span className="font-medium text-foreground">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function RiskTrendsPanel({ variant = 'card' }) {
  const [days, setDays] = useState(7);
  const daily = useMemo(() => {
    if (days === 7) return DEMO_TREND;
    return Array.from({ length: days }, (_, index) => {
      const source = DEMO_TREND[index % DEMO_TREND.length];
      return { ...source, date: index < 7 ? source.date : `Sep ${28 + index - 7}` };
    });
  }, [days]);

  const total = daily.reduce((sum, row) => sum + row.total, 0);
  const high = daily.reduce((sum, row) => sum + row.High, 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className={`flex items-center gap-2 ${variant === 'page' ? 'text-xl' : 'text-base'}`}>
              <TrendingUp className="h-4 w-4 text-primary" /> Risk Trends
            </CardTitle>
            <CardDescription>Compact review trend prepared for the presentation workspace.</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {RANGE_OPTIONS.map((option) => (
              <Button key={option.value} size="sm" variant={days === option.value ? 'default' : 'outline'} onClick={() => setDays(option.value)}>
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <SummaryCard label="Risks in view" value={total} hint="Curated review activity" />
          <SummaryCard label="High risks" value={high} hint="Across the selected period" />
          <SummaryCard label="Average / day" value={(total / daily.length).toFixed(1)} hint="Compact review trend" />
          <SummaryCard label="Active signals" value={total} hint="Shown as active in this demo view" />
        </div>

        <Chart title="Risk volume over time">
          <LineChart data={daily}><CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} /><XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} /><Tooltip content={<TooltipContent />} /><Line type="monotone" dataKey="total" name="Risks detected" stroke="#0ea5e9" strokeWidth={2.5} dot={{ r: 3 }} /></LineChart>
        </Chart>

        <Chart title="Severity over time">
          <LineChart data={daily}><CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} /><XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} /><Tooltip content={<TooltipContent />} /><Legend /><Line type="monotone" dataKey="High" name="High" stroke="#dc2626" strokeWidth={1.8} dot={false} /><Line type="monotone" dataKey="Medium" name="Medium" stroke="#f59e0b" strokeWidth={1.8} dot={false} /><Line type="monotone" dataKey="Low" name="Low" stroke="#22c55e" strokeWidth={1.8} dot={false} /></LineChart>
        </Chart>

        <Chart title="Risk types recorded">
          <BarChart data={RISK_TYPES}><CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} /><Tooltip content={<TooltipContent />} /><Bar dataKey="count" name="Risks" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={56} /></BarChart>
        </Chart>

        <p className="border-t border-border/60 pt-3 text-xs text-muted-foreground">
          Presentation review data. This compact demonstration dataset is intentionally separate from the full historical telemetry.
        </p>
      </CardContent>
    </Card>
  );
}

function Chart({ title, children }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold">{title}</h4>
      <div className="h-56 w-full"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>
    </div>
  );
}

function SummaryCard({ label, value, hint }) {
  return <div className="ss-metric"><div className="ss-metric-label">{label}</div><div className="ss-metric-value">{value}</div><div className="mt-1.5 text-[11px] text-muted-foreground">{hint}</div></div>;
}
