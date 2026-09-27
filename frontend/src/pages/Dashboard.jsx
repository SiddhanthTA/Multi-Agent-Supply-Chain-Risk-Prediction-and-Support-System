import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  MapPin,
  RefreshCcw,
  ShieldAlert,
} from 'lucide-react';
import api from '@/services/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { normalizeWorkspaceLocation, WORKSPACE_LOCATIONS } from '@/lib/locationWorkspace';
import { recentParams } from '@/lib/riskReports';

const fetchDashboardData = async (selectedLocation) => {
  const [reviewEventsRes, reviewRisksRes, locationsRes] = await Promise.all([
    api.get('/events/review-set', { params: { location: selectedLocation } }),
    api.get('/risks/review-set', { params: { location: selectedLocation } }),
    api.get('/locations/'),
  ]);
  return {
    events: reviewEventsRes.data,
    risks: reviewRisksRes.data?.items || [],
    locations: locationsRes.data,
  };
};

const SEVERITY_RANK = { critical: 0, high: 1, medium: 2, low: 3 };

function SeverityBadge({ severity }) {
  const value = String(severity || '').toLowerCase();
  const variant = ['critical', 'high', 'medium', 'low'].includes(value) ? value : 'outline';
  return <Badge variant={variant}>{severity || 'Unrated'}</Badge>;
}

function EmptyState({ text }) {
  return (
    <div className="rounded-xl border border-dashed border-border/60 px-6 py-8 text-center text-sm text-muted-foreground">
      {text}
    </div>
  );
}

function WorkspaceMessage({ title, message }) {
  return (
    <div className="ss-page flex flex-col items-center justify-center gap-2 py-16 text-center">
      <AlertTriangle className="h-8 w-8 text-destructive" />
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

function KpiCard({ title, value, icon: Icon, valueClass = '' }) {
  return (
    <div className="ss-metric">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{title}</span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className={`mt-2 text-2xl font-semibold tabular-nums ${valueClass}`}>{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedLocation, setSelectedLocation] = useState(() =>
    normalizeWorkspaceLocation(localStorage.getItem('supplysentry-location')));

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['dashboardWorkspace', selectedLocation],
    queryFn: () => fetchDashboardData(selectedLocation),
    refetchInterval: 30000,
  });
  const selectedDefinition =
    WORKSPACE_LOCATIONS.find((l) => l.id === selectedLocation) || WORKSPACE_LOCATIONS[0];
  const currentRisks = useMemo(() => {
    return [...(data?.risks || [])].sort((a, b) => (
      (SEVERITY_RANK[String(a.severity || '').toLowerCase()] ?? 4)
      - (SEVERITY_RANK[String(b.severity || '').toLowerCase()] ?? 4)
    ) || Number(b.risk_score || 0) - Number(a.risk_score || 0));
  }, [data?.risks]);

  const highlightedRisks = useMemo(() => currentRisks.slice(0, 10), [currentRisks]);
  const highCriticalCount = useMemo(
    () => currentRisks.filter((r) => ['high', 'critical'].includes(String(r.severity || '').toLowerCase())).length,
    [currentRisks],
  );

  const changeLocation = (value) => {
    setSelectedLocation(value);
    localStorage.setItem('supplysentry-location', value);
  };

  if (isError) return <WorkspaceMessage title="Dashboard unavailable" message={error.message} />;

  return (
    <div className="ss-page ss-enter space-y-5 pb-10">
      <header className="border-b border-border/70 pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="ss-eyebrow text-primary">SupplySentry workspace</p>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-tight">{selectedDefinition.label}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {selectedDefinition.kind === 'all'
                ? 'Network-wide intelligence across all stored locations.'
                : selectedDefinition.kind === 'global'
                  ? 'Intelligence not specific to a single monitored region.'
                  : `Operational intelligence for ${selectedDefinition.label}.`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm font-medium" htmlFor="workspace-location">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <span className="sr-only">Workspace location</span>
              <select
                id="workspace-location"
                value={selectedLocation}
                onChange={(e) => changeLocation(e.target.value)}
                className="h-9 min-w-40 rounded-lg border border-input bg-background px-3 text-sm shadow-sm"
              >
                {WORKSPACE_LOCATIONS.map((l) => (
                  <option key={l.id} value={l.id}>{l.label}</option>
                ))}
              </select>
            </label>
            <Button
              variant="outline"
              size="icon"
              title="Refresh workspace"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboardWorkspace'] })}
            >
              <RefreshCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-3">
        <KpiCard title="Active Risks" value={isLoading ? <Skeleton className="h-6 w-12" /> : currentRisks.length} icon={ShieldAlert} />
        <KpiCard title="High / Critical" value={isLoading ? <Skeleton className="h-6 w-12" /> : highCriticalCount} icon={AlertTriangle} valueClass="text-destructive" />
        <KpiCard title="Current Risks" value={isLoading ? <Skeleton className="h-6 w-12" /> : currentRisks.length} icon={Activity} />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldAlert className="h-4 w-4 text-destructive" /> Current risks
          </CardTitle>
          <CardDescription>
            Curated risks across the selected workspace, ordered by severity and risk score.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CurrentRiskCards
            risks={highlightedRisks}
            isLoading={isLoading}
            onOpen={(riskId) => navigate(`/risks/${riskId}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function CurrentRiskCards({ risks, isLoading, onOpen }) {
  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (!risks.length) {
    return <EmptyState text="No active risks are currently identified for this workspace." />;
  }
  return (
    <div className="grid gap-2.5">
      {risks.map((risk) => (
        <div key={risk.risk_id} className="rounded-xl border border-border/60 bg-card p-4 transition-colors duration-150 hover:border-primary/50">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-semibold leading-snug text-foreground">
                {risk.title || `Risk ${risk.risk_id}`}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {[risk.location, risk.category].filter(Boolean).join(' / ')}
              </p>
              {risk.risk_type && (
                <p className="mt-1 text-xs text-muted-foreground">Type: {risk.risk_type}</p>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <SeverityBadge severity={risk.severity} />
              <Button size="sm" variant="outline" onClick={() => onOpen(risk.risk_id)}>View Risk</Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
