import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { Activity, AlertTriangle, BrainCircuit, CloudRain, Database, ExternalLink, MapPin, RefreshCcw, ShieldAlert } from 'lucide-react';
import api from '@/services/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import WeatherRiskMap from '@/components/WeatherRiskMap';
import { formatLocationDisplay } from '@/lib/locationDisplay';
import {
  buildWeatherCityStates,
  filterEventsByWorkspace,
  getWeatherLocationsForWorkspace,
  normalizeWorkspaceLocation,
  refreshWeatherLocations,
  WORKSPACE_LOCATIONS,
} from '@/lib/locationWorkspace';
import { composeEventIntelligence, getEventForRisk } from '@/lib/intelligenceComposition';

const fetchDashboardData = async () => {
  const [eventsRes, risksRes, predictionsRes, recommendationsRes, locationsRes] = await Promise.all([
    api.get('/events/'), api.get('/risks/'), api.get('/predictions/'), api.get('/recommendations/'), api.get('/locations/'),
  ]);
  return { events: eventsRes.data, risks: risksRes.data, predictions: predictionsRes.data, recommendations: recommendationsRes.data, locations: locationsRes.data };
};

function relativeTime(value) {
  if (!value) return 'Time unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : formatDistanceToNow(date, { addSuffix: true });
}
function severityVariant(value) {
  const normalized = String(value || '').toLowerCase();
  return ['critical', 'high', 'medium', 'low'].includes(normalized) ? normalized : 'outline';
}
function SeverityBadge({ severity }) { return <Badge variant={severityVariant(severity)}>{severity || 'Unrated'}</Badge>; }

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedLocation, setSelectedLocation] = useState(() => normalizeWorkspaceLocation(localStorage.getItem('supplysentry-location')));
  const { data, isLoading, isError, error } = useQuery({ queryKey: ['dashboardWorkspace'], queryFn: fetchDashboardData, refetchInterval: 30000 });
  const weatherMutation = useMutation({
    mutationFn: (locations) => refreshWeatherLocations(
      locations,
      (location) => api.post(`/events/weather/store?location=${encodeURIComponent(location)}`),
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboardWorkspace'] }),
  });

  const selectedDefinition = WORKSPACE_LOCATIONS.find((location) => location.id === selectedLocation) || WORKSPACE_LOCATIONS[0];
  const filteredEvents = useMemo(() => filterEventsByWorkspace(data?.events, selectedLocation, data?.locations), [data?.events, data?.locations, selectedLocation]);
  const filteredEventIds = useMemo(() => new Set(filteredEvents.map((event) => event.id)), [filteredEvents]);
  const filteredRisks = useMemo(() => (data?.risks || []).filter((risk) => filteredEventIds.has(risk.event_id)), [data?.risks, filteredEventIds]);
  const filteredRiskIds = useMemo(() => new Set(filteredRisks.map((risk) => risk.id)), [filteredRisks]);
  const filteredPredictions = useMemo(() => (data?.predictions || []).filter((prediction) => filteredRiskIds.has(prediction.risk_id)), [data?.predictions, filteredRiskIds]);
  const filteredRecommendations = useMemo(() => (data?.recommendations || []).filter((recommendation) => filteredPredictions.some((prediction) => prediction.id === recommendation.prediction_id)), [data?.recommendations, filteredPredictions]);
  const selectedWeatherLocations = useMemo(
    () => getWeatherLocationsForWorkspace(data?.locations, selectedLocation),
    [data?.locations, selectedLocation],
  );
  const weatherCityStates = useMemo(
    () => buildWeatherCityStates(data?.locations, data?.events, data?.risks)
      .filter((state) => selectedWeatherLocations.some(
        (location) => location.id === state.location.id,
      )),
    [data?.locations, data?.events, data?.risks, selectedWeatherLocations],
  );
  const activeRisks = filteredRisks.filter((risk) => ['active', 'new', 'in progress'].includes(String(risk.status || '').toLowerCase()));
  const highPriorityRisks = filteredRisks.filter((risk) => ['critical', 'high'].includes(String(risk.severity || '').toLowerCase())).sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0)).slice(0, 5);
  const intelligenceItems = useMemo(() => composeEventIntelligence(filteredEvents, filteredRisks, filteredPredictions, filteredRecommendations).sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0)).slice(0, 12), [filteredEvents, filteredPredictions, filteredRecommendations, filteredRisks]);

  const changeLocation = (value) => { setSelectedLocation(value); localStorage.setItem('supplysentry-location', value); };
  if (isError) return <WorkspaceMessage title="Dashboard unavailable" message={error.message} />;
  const weatherRefreshSummary = weatherMutation.data || [];

  return <div className="mx-auto max-w-7xl space-y-6 pb-10">
    <header className="border-b border-border/70 pb-5"><div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">SupplySentry workspace</p><h1 className="mt-2 text-3xl font-bold tracking-tight">{selectedDefinition.label}</h1><p className="mt-1 text-sm text-muted-foreground">{selectedDefinition.kind === 'all' ? 'Network-wide intelligence across all stored locations.' : selectedDefinition.kind === 'global' ? 'Locationless intelligence with no reliable geographic match.' : `Operational intelligence for ${selectedDefinition.label}.`}</p></div><div className="flex items-center gap-3"><label className="flex items-center gap-2 text-sm font-medium" htmlFor="workspace-location"><MapPin className="h-4 w-4 text-primary" /><span className="sr-only">Workspace location</span><select id="workspace-location" value={selectedLocation} onChange={(event) => changeLocation(event.target.value)} className="h-10 min-w-44 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">{WORKSPACE_LOCATIONS.map((location) => <option key={location.id} value={location.id}>{location.label}</option>)}</select></label><Button variant="outline" size="icon" title="Refresh workspace" onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboardWorkspace'] })}><RefreshCcw className="h-4 w-4" /></Button></div></div></header>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><KpiCard title="Active risks" value={isLoading ? <Skeleton className="h-8 w-14" /> : activeRisks.length} icon={ShieldAlert} /><KpiCard title="High / critical" value={isLoading ? <Skeleton className="h-8 w-14" /> : filteredRisks.filter((risk) => ['high', 'critical'].includes(String(risk.severity || '').toLowerCase())).length} icon={AlertTriangle} valueClass="text-destructive" /><KpiCard title="Events" value={isLoading ? <Skeleton className="h-8 w-14" /> : filteredEvents.length} icon={Activity} /><KpiCard title="Predictions" value={isLoading ? <Skeleton className="h-8 w-14" /> : filteredPredictions.length} icon={BrainCircuit} /></section>
    <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2"><CloudRain className="h-5 w-5 text-primary" /> Weather risk map</CardTitle>
              <CardDescription>Weather monitoring is separate from primary intelligence filtering.</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => weatherMutation.mutate(selectedWeatherLocations)}
              disabled={weatherMutation.isPending || selectedWeatherLocations.length === 0}
            >
              <CloudRain className="mr-2 h-4 w-4" />
              {weatherMutation.isPending ? 'Refreshing weather...' : 'Refresh weather'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-[420px] w-full" /> : <WeatherRiskMap cityStates={weatherCityStates} />}
          {weatherRefreshSummary.length > 0 && (
            <div className="mt-3 text-xs text-muted-foreground">
              {weatherRefreshSummary.filter((item) => item.status === 'success').length} updated;
              {' '}{weatherRefreshSummary.filter((item) => item.status === 'error').length} failed.
              {weatherRefreshSummary.some((item) => item.status === 'error') && (
                <span> Failed cities: {weatherRefreshSummary.filter((item) => item.status === 'error').map((item) => item.location).join(', ')}.</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>High-priority risks</CardTitle><CardDescription>Signals requiring the fastest review in this intelligence location context.</CardDescription></CardHeader>
        <CardContent className="space-y-3">{highPriorityRisks.length ? highPriorityRisks.map((risk) => <RiskRow key={risk.id} risk={risk} event={getEventForRisk(risk, filteredEvents)} onOpen={() => navigate(`/risks/${risk.id}`)} />) : <EmptyState text="No high or critical risks in this context." />}</CardContent>
      </Card>
    </section>
    <Card><CardHeader className="flex-row items-center justify-between space-y-0"><div><CardTitle>Unified intelligence feed</CardTitle><CardDescription>Events, risks, and predictions ordered by their most useful available timestamp.</CardDescription></div><Button variant="outline" size="sm" onClick={() => navigate('/feed')}>Open full feed <ExternalLink className="ml-2 h-4 w-4" /></Button></CardHeader><CardContent className="space-y-3">{isLoading ? <Skeleton className="h-48 w-full" /> : intelligenceItems.length ? intelligenceItems.map((item) => <FeedRow key={item.id} item={item} onOpen={() => navigate(item.href)} />) : <EmptyState text="No intelligence is available for this location context." />}</CardContent></Card>
    <div className="flex items-center gap-2 text-xs text-muted-foreground"><Database className="h-3.5 w-3.5" /> Location values are filtered exactly as stored. Global represents Unknown or null locations.</div>
  </div>;
}

function KpiCard({ title, value, icon: Icon, valueClass = '' }) { return <Card className="p-5"><div className="flex items-start justify-between"><div><p className="text-sm text-muted-foreground">{title}</p><div className={`mt-3 text-3xl font-bold tracking-tight ${valueClass}`}>{value}</div></div><Icon className="h-5 w-5 text-primary" /></div></Card>; }
function FeedRow({ item, onOpen }) { const displayLocation = formatLocationDisplay(item.event.location); return <button type="button" onClick={onOpen} className="flex w-full items-start gap-3 rounded-xl border border-border/60 bg-muted/10 p-4 text-left transition-colors hover:bg-muted/30"><div className="mt-0.5 rounded-full border border-primary/20 bg-primary/10 p-2"><Activity className="h-4 w-4 text-primary" /></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="font-semibold">{item.title}</span>{item.primaryRisk && <SeverityBadge severity={item.primaryRisk.severity} />}</div><p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{item.description}</p><div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground"><Badge variant="secondary">{item.category}</Badge><span>{displayLocation.label}</span><span>{item.event.source || 'Source unknown'}</span><span>{relativeTime(item.timestamp)}</span>{item.primaryRisk && <span>{Number(item.primaryRisk.risk_score || 0).toFixed(0)} / 100</span>}{item.primaryPrediction && <span>Prediction {item.primaryPrediction.predicted_severity || 'available'}</span>}</div></div><ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" /></button>; }
function RiskRow({ risk, event, onOpen }) { const displayLocation = formatLocationDisplay(event?.location); return <button type="button" onClick={onOpen} className="flex w-full items-start justify-between gap-3 rounded-xl border border-border/60 bg-muted/10 p-3 text-left hover:bg-muted/30"><div className="min-w-0"><p className="truncate font-medium">{event?.title || 'Event details unavailable'}</p><p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{event?.description || `${risk.risk_type || 'Risk'} associated with this event.`}</p><div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground"><span>{risk.risk_type || 'Risk'}</span><span>{displayLocation.label}</span><span>{event?.source || 'Source unknown'}</span></div></div><div className="flex shrink-0 flex-col items-end gap-2"><SeverityBadge severity={risk.severity} /><span className="text-xs font-medium">{Number(risk.risk_score || 0).toFixed(0)} / 100</span></div></button>; }
function EmptyState({ text }) { return <div className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">{text}</div>; }
function WorkspaceMessage({ title, message }) { return <div className="flex min-h-[50vh] flex-col items-center justify-center text-center"><AlertTriangle className="mb-4 h-10 w-10 text-destructive" /><h2 className="text-2xl font-bold">{title}</h2><p className="mt-2 text-muted-foreground">{message}</p></div>; }
