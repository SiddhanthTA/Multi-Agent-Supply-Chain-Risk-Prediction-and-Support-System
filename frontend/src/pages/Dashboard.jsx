import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  CloudRain,
  MapPin,
  RefreshCcw,
  ShieldAlert,
  Thermometer,
  Wind,
} from 'lucide-react';
import api from '@/services/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  buildWeatherCityStates,
  getWeatherLocationsForScope,
  normalizeWorkspaceLocation,
  refreshWeatherLocations,
  WORKSPACE_LOCATIONS,
} from '@/lib/locationWorkspace';

const fetchDashboardData = async (selectedLocation) => {
  const [reviewEventsRes, reviewRisksRes, locationsRes, weatherEventsRes, weatherRisksRes] = await Promise.all([
    api.get('/events/review-set', { params: { location: selectedLocation } }),
    api.get('/risks/review-set', { params: { location: selectedLocation } }),
    api.get('/locations/'),
    api.get('/events/', { params: { days: 7 } }),
    api.get('/risks/', { params: { days: 7 } }),
  ]);
  return {
    events: reviewEventsRes.data,
    risks: reviewRisksRes.data?.items || [],
    locations: locationsRes.data || [],
    weatherEvents: weatherEventsRes.data || [],
    weatherRisks: weatherRisksRes.data || [],
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
  const [weatherCity, setWeatherCity] = useState('');
  const [weatherRefreshError, setWeatherRefreshError] = useState('');

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

  const weatherEnabled = selectedLocation === 'India' || selectedLocation === 'United States';
  const weatherLocations = useMemo(
    () => weatherEnabled ? getWeatherLocationsForScope(data?.locations || [], selectedLocation) : [],
    [data?.locations, selectedLocation, weatherEnabled],
  );
  const weatherStates = useMemo(
    () => buildWeatherCityStates(data?.locations || [], data?.weatherEvents || [], data?.weatherRisks || [])
      .filter((state) => weatherLocations.some((location) => location.id === state.location.id)),
    [data?.locations, data?.weatherEvents, data?.weatherRisks, weatherLocations],
  );

  useEffect(() => {
    if (!weatherEnabled) {
      setWeatherCity('');
      return;
    }
    if (!weatherCity || !weatherLocations.some((location) => location.name === weatherCity)) {
      setWeatherCity(weatherLocations[0]?.name || '');
    }
  }, [weatherEnabled, weatherCity, weatherLocations]);

  const selectedWeather = weatherStates.find((state) => state.location.name === weatherCity) || weatherStates[0] || null;

  const weatherRefresh = useMutation({
    mutationFn: async () => {
      if (!selectedWeather) return null;
      return api.post('/events/weather/store', null, {
        params: { location: `${selectedWeather.location.name}, ${selectedWeather.location.country}` },
      });
    },
    onMutate: () => setWeatherRefreshError(''),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboardWorkspace', selectedLocation] }),
    onError: (err) => setWeatherRefreshError(err?.response?.data?.detail || err?.message || 'Unable to refresh weather.'),
  });

  const changeLocation = (value) => {
    setSelectedLocation(value);
    setWeatherRefreshError('');
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

      {weatherEnabled && (
        <DashboardWeatherCard
          states={weatherStates}
          selected={selectedWeather}
          city={weatherCity}
          onCityChange={setWeatherCity}
          onRefresh={() => weatherRefresh.mutate()}
          isRefreshing={weatherRefresh.isPending}
          error={weatherRefreshError}
        />
      )}

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

function DashboardWeatherCard({ states, selected, city, onCityChange, onRefresh, isRefreshing, error }) {
  const weatherEvent = selected?.weatherEvent;
  const risk = selected?.risk;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <CloudRain className="h-4 w-4 text-primary" /> Weather Monitoring
            </CardTitle>
            <CardDescription>
              Current weather for the selected {states[0]?.location?.country || 'region'} monitoring location.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={city}
              onChange={(event) => onCityChange(event.target.value)}
              className="h-9 min-w-44 rounded-lg border border-input bg-background px-3 text-sm"
              aria-label="Weather city"
            >
              {states.map((state) => (
                <option key={state.location.id} value={state.location.name}>{state.location.name}</option>
              ))}
            </select>
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={!selected || isRefreshing}>
              <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing…' : 'Refresh'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!selected ? (
          <EmptyState text="No monitored weather locations are configured for this workspace." />
        ) : (
          <div className="grid gap-4 md:grid-cols-[1fr_1.5fr]">
            <div className="rounded-xl border border-border/60 bg-muted/10 p-5">
              <p className="text-xs uppercase tracking-[0.15em] text-muted-foreground">{selected.location.name}, {selected.location.country}</p>
              <div className="mt-3 flex items-center gap-3">
                <Thermometer className="h-6 w-6 text-primary" />
                <span className="text-4xl font-semibold tracking-tight">
                  {extractTemperature(weatherEvent?.description)}
                </span>
              </div>
              <p className="mt-2 text-base font-medium">{weatherEvent?.title || 'Weather data not collected yet'}</p>
              <p className="mt-1 text-sm text-muted-foreground">{weatherEvent ? weatherEvent.description : 'Use Refresh to collect the current WeatherAPI observation.'}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <WeatherMetric icon={Wind} label="Wind" value={extractMetric(weatherEvent?.description, 'Wind')} suffix=" kph" />
              <WeatherMetric icon={Activity} label="Humidity" value={extractMetric(weatherEvent?.description, 'Humidity')} suffix="%" />
              <WeatherMetric icon={CloudRain} label="Rain" value={extractMetric(weatherEvent?.description, 'Precipitation')} suffix=" mm" />
            </div>
            <div className="md:col-span-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              {risk?.severity && <Badge variant={String(risk.severity).toLowerCase()}>{risk.severity}</Badge>}
              {risk?.risk_type && <Badge variant="outline">{risk.risk_type}</Badge>}
              <span>
                {weatherEvent?.event_time || weatherEvent?.created_at
                  ? `Observed ${new Date(weatherEvent.event_time || weatherEvent.created_at).toLocaleString()}`
                  : 'No observation yet'}
              </span>
              {error && <span className="text-destructive">{error}</span>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function extractTemperature(description) {
  const match = String(description || '').match(/Temperature:\s*([-+]?\d+(?:\.\d+)?)\s*°?C/i);
  return match ? `${match[1]}°C` : 'Unavailable';
}

function extractMetric(description, label) {
  const match = String(description || '').match(new RegExp(`${label}:\\s*([-+]?\\d+(?:\\.\\d+)?)`, 'i'));
  return match ? match[1] : '—';
}

function WeatherMetric({ icon: Icon, label, value, suffix = '' }) {
  return (
    <div className="rounded-xl border border-border/60 bg-muted/10 p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <p className="mt-2 text-lg font-semibold">{value}{value !== '—' ? suffix : ''}</p>
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
