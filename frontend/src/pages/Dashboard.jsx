import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Building2,
  CloudRain,
  MapPin,
  RefreshCcw,
  ShieldAlert,
} from 'lucide-react';
import api from '@/services/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import WeatherRiskMap from '@/components/WeatherRiskMap';
import {
  buildWeatherCityStates,
  filterEventsByWorkspace,
  getWeatherLocationsForScope,
  matchesWorkspaceLocation,
  normalizeWorkspaceLocation,
  refreshWeatherLocations,
  WORKSPACE_LOCATIONS,
} from '@/lib/locationWorkspace';
import { companyRelevanceLevel } from '@/lib/riskInvestigation';
import { fetchCurrentRisks, recentParams } from '@/lib/riskReports';

const fetchDashboardData = async () => {
  const [eventsRes, risksRes, locationsRes, companyRes] = await Promise.all([
    api.get('/events/', { params: recentParams() }),
    api.get('/risks/', { params: recentParams() }),
    api.get('/locations/'),
    api.get('/company-profile/relevance').catch(() => null),
  ]);
  return {
    events: eventsRes.data,
    risks: risksRes.data,
    locations: locationsRes.data,
    companyRelevance: companyRes?.data || null,
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
  const [weatherScope] = useState('global');
  const autoWeatherLoaded = useRef(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['dashboardWorkspace'],
    queryFn: fetchDashboardData,
    refetchInterval: 30000,
  });
  const { data: currentRiskData } = useQuery({
    queryKey: ['currentRisks'],
    queryFn: fetchCurrentRisks,
    staleTime: 60 * 1000,
  });

  const weatherMutation = useMutation({
    mutationFn: (locations) => refreshWeatherLocations(
      locations,
      (location) => api.post(`/events/weather/store?location=${encodeURIComponent(location)}`),
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboardWorkspace'] }),
  });

  useEffect(() => {
    if (autoWeatherLoaded.current || isLoading || !data?.locations) return;
    autoWeatherLoaded.current = true;
    const locations = getWeatherLocationsForScope(data.locations, weatherScope);
    if (locations.length) weatherMutation.mutate(locations);
  }, [isLoading, data?.locations, weatherScope, weatherMutation]);

  const selectedDefinition =
    WORKSPACE_LOCATIONS.find((l) => l.id === selectedLocation) || WORKSPACE_LOCATIONS[0];
  const filteredEvents = useMemo(
    () => filterEventsByWorkspace(data?.events, selectedLocation, data?.locations),
    [data?.events, data?.locations, selectedLocation],
  );
  const filteredEventIds = useMemo(
    () => new Set(filteredEvents.map((event) => event.id)), [filteredEvents]);
  const filteredRisks = useMemo(
    () => (data?.risks || []).filter((risk) => filteredEventIds.has(risk.event_id)),
    [data?.risks, filteredEventIds],
  );
  const selectedWeatherLocations = useMemo(
    () => getWeatherLocationsForScope(data?.locations, weatherScope),
    [data?.locations, weatherScope],
  );
  const scopedWeatherCityStates = useMemo(
    () => buildWeatherCityStates(data?.locations, data?.events, data?.risks)
      .filter((s) => selectedWeatherLocations.some((l) => l.id === s.location.id)),
    [data?.locations, data?.events, data?.risks, selectedWeatherLocations],
  );

  // Risks currently surfaced for the selected workspace. SupplySentry detects a
  // very large event stream, but only a smaller classified set is actionable.
  const currentRisks = useMemo(() => {
    const scoped = (currentRiskData?.items || []).filter((item) =>
      matchesWorkspaceLocation(item.location, selectedLocation, data?.locations));
    return scoped.sort((a, b) => (
      (SEVERITY_RANK[String(a.severity || '').toLowerCase()] ?? 4)
      - (SEVERITY_RANK[String(b.severity || '').toLowerCase()] ?? 4)
    ) || Number(b.risk_score || 0) - Number(a.risk_score || 0));
  }, [currentRiskData, selectedLocation, data?.locations]);

  // Bounded subset keeps the dashboard readable; Risks page has the full list.
  const highlightedRisks = useMemo(() => currentRisks.slice(0, 8), [currentRisks]);
  const highCriticalCount = useMemo(
    () => currentRisks.filter((r) => ['high', 'critical'].includes(String(r.severity || '').toLowerCase())).length,
    [currentRisks],
  );

  const companyRelevance = data?.companyRelevance || null;
  const workspaceEventIds = useMemo(
    () => new Set(filteredEvents.map((event) => event.id)), [filteredEvents]);
  const companyRelevantRows = useMemo(
    () => (companyRelevance?.events || []).filter((row) => {
      const level = companyRelevanceLevel(row);
      return (level === 'direct' || level === 'indirect') && workspaceEventIds.has(row.event_id);
    }),
    [companyRelevance, workspaceEventIds],
  );

  const changeLocation = (value) => {
    setSelectedLocation(value);
    localStorage.setItem('supplysentry-location', value);
  };

  if (isError) return <WorkspaceMessage title="Dashboard unavailable" message={error.message} />;
  const weatherRefreshSummary = weatherMutation.data || [];

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
            <ShieldAlert className="h-4 w-4 text-destructive" /> Company-relevant risks
          </CardTitle>
          <CardDescription>
            Highest-priority company-relevant risks in this workspace, ordered by severity and risk score.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CurrentRiskCards
            risks={highlightedRisks}
            isLoading={isLoading || !currentRiskData}
            onOpen={(riskId) => navigate(`/risks/${riskId}`)}
          />
        </CardContent>
      </Card>

      {companyRelevance ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4 text-primary" /> Company relevant intelligence
            </CardTitle>
            <CardDescription>
              {companyRelevance.company_name
                ? `${companyRelevance.company_name} - ${companyRelevance.industry}`
                : 'Matches against your configured company dependencies.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {companyRelevantRows.length ? (
              companyRelevantRows.slice(0, 6).map((row) => {
                const risk = filteredRisks.find((r) => r.event_id === row.event_id);
                return (
                  <div key={row.event_id} className="rounded-lg border border-border/60 bg-muted/10 p-3">
                    <p className="text-sm font-medium text-foreground">
                      {row.title || `Event ${row.event_id}`}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {companyRelevanceLevel(row)} relevance
                      {row.reason ? ` - ${row.reason}` : ''}
                    </p>
                    {risk && (
                      <Button size="sm" variant="outline" className="mt-2" onClick={() => navigate(`/risks/${risk.id}`)}>
                        View Risk
                      </Button>
                    )}
                  </div>
                );
              })
            ) : (
              <EmptyState text="No company-relevant risks are currently identified for this workspace. General intelligence remains available in the Events view." />
            )}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CloudRain className="h-4 w-4 text-primary" /> Weather monitoring
          </CardTitle>
          <CardDescription>
            {selectedWeatherLocations.length} monitoring{' '}
            {selectedWeatherLocations.length === 1 ? 'location' : 'locations'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-[420px] w-full" /> : <WeatherRiskMap cityStates={scopedWeatherCityStates} />}
          {weatherRefreshSummary.length > 0 && (
            <div className="mt-3 text-xs text-muted-foreground">
              {weatherRefreshSummary.filter((i) => i.status === 'success').length} updated;{' '}
              {weatherRefreshSummary.filter((i) => i.status === 'error').length} failed.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CurrentRiskCards({ risks, isLoading, onOpen }) {
  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (!risks.length) {
    return <EmptyState text="No company-relevant risks are currently identified for this workspace. General intelligence remains available in the Events view." />;
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
