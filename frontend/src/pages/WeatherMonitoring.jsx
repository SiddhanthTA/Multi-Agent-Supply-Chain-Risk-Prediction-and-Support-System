import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CloudRain, MapPin, RefreshCcw, Thermometer, Wind } from 'lucide-react';
import api from '@/services/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import WeatherRiskMap from '@/components/WeatherRiskMap';
import {
  buildWeatherCityStates,
  getWeatherLocationsForScope,
  normalizeWeatherScope,
  refreshWeatherLocations,
  WEATHER_SCOPES,
} from '@/lib/locationWorkspace';

function temperatureFromDescription(description) {
  const match = String(description || '').match(/Temperature:\s*([^\s°]+)/i);
  return match ? `${match[1]}°C` : 'Unavailable';
}

function weatherText(state) {
  const title = state.weatherEvent?.title || state.weatherEvent?.description || '';
  return title.replace(/^Weather:\s*/i, '').trim() || 'Weather data not collected yet';
}

export default function WeatherMonitoring() {
  const queryClient = useQueryClient();
  const [scope, setScope] = useState(() => normalizeWeatherScope(localStorage.getItem('supplysentry-weather-scope') || 'United States'));

  const { data, isLoading } = useQuery({
    queryKey: ['weatherMonitoring', scope],
    queryFn: async () => {
      const [locationsRes, eventsRes, risksRes] = await Promise.all([
        api.get('/locations/'),
        api.get('/events/', { params: { days: 7 } }),
        api.get('/risks/', { params: { days: 7 } }),
      ]);
      return { locations: locationsRes.data || [], events: eventsRes.data || [], risks: risksRes.data || [] };
    },
    staleTime: 30 * 1000,
  });

  const locations = useMemo(
    () => getWeatherLocationsForScope(data?.locations || [], scope),
    [data?.locations, scope],
  );
  const cityStates = useMemo(
    () => buildWeatherCityStates(data?.locations || [], data?.events || [], data?.risks || [])
      .filter((state) => locations.some((location) => location.id === state.location.id)),
    [data?.locations, data?.events, data?.risks, locations],
  );

  const refresh = useMutation({
    mutationFn: () => refreshWeatherLocations(
      locations,
      (location) => api.post(`/events/weather/store?location=${encodeURIComponent(location)}`),
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['weatherMonitoring', scope] }),
  });

  const changeScope = (value) => {
    setScope(value);
    localStorage.setItem('supplysentry-weather-scope', value);
  };

  return (
    <div className="ss-page ss-enter space-y-5 pb-10">
      <header className="border-b border-border/70 pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="ss-eyebrow text-primary">Environmental intelligence</p>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-tight">Weather Monitoring</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Live weather conditions for SupplySentry's designated monitoring locations.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={scope}
              onChange={(event) => changeScope(event.target.value)}
              className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
              aria-label="Weather region"
            >
              {WEATHER_SCOPES.filter((item) => item.id !== 'global').map((item) => (
                <option key={item.id} value={item.id}>{item.label}</option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              disabled={refresh.isPending || !locations.length}
              onClick={() => refresh.mutate()}
            >
              <RefreshCcw className={`mr-2 h-4 w-4 ${refresh.isPending ? 'animate-spin' : ''}`} />
              Refresh Weather
            </Button>
          </div>
        </div>
      </header>

      {isLoading ? (
        <Skeleton className="h-[520px] w-full" />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CloudRain className="h-4 w-4 text-primary" />
                {scope} monitoring map
              </CardTitle>
              <CardDescription>
                {locations.length} designated monitoring locations. Select a marker for the latest stored observation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WeatherRiskMap cityStates={cityStates} country={scope} />
            </CardContent>
          </Card>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold">Location conditions</h2>
                <p className="text-xs text-muted-foreground">Latest available observation for each monitored city.</p>
              </div>
              <Badge variant="outline">{locations.length} locations</Badge>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {cityStates.map((state) => (
                <WeatherCard key={state.location.id} state={state} />
              ))}
            </div>
          </section>
        </>
      )}

      <p className="text-xs text-muted-foreground">
        Weather is shown only for India and United States workspaces. All Locations and Global intentionally omit weather monitoring.
      </p>
    </div>
  );
}

function WeatherCard({ state }) {
  const { location, weatherEvent, risk } = state;
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-semibold">{location.name}</p>
            <p className="text-xs text-muted-foreground">{location.country}</p>
          </div>
          <MapPin className="h-4 w-4 text-primary" />
        </div>
        <div className="flex items-center gap-2">
          <Thermometer className="h-4 w-4 text-muted-foreground" />
          <span className="text-xl font-semibold">{temperatureFromDescription(weatherEvent?.description)}</span>
        </div>
        <p className="min-h-10 text-sm text-muted-foreground">{weatherText(state)}</p>
        <div className="flex flex-wrap items-center gap-2">
          {risk?.severity && <Badge variant={String(risk.severity).toLowerCase()}>{risk.severity}</Badge>}
          {risk?.risk_type && <Badge variant="outline">{risk.risk_type}</Badge>}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Wind className="h-3 w-3" />
          {weatherEvent?.created_at ? new Date(weatherEvent.created_at).toLocaleString() : 'No observation yet'}
        </div>
      </CardContent>
    </Card>
  );
}
