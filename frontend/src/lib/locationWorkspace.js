export const WORKSPACE_LOCATIONS = [
  { id: 'all', label: 'All Locations', kind: 'all' },
  { id: 'global', label: 'Global', kind: 'global' },
  { id: 'India', label: 'India', kind: 'specific' },
  { id: 'United States', label: 'United States', kind: 'specific' },
];

/** Regions with their own workspace view; everything else reads as Global. */
const MONITORED_REGIONS = new Set(['india', 'united states']);

export function normalizeWorkspaceLocation(value) {
  const candidate = String(value || 'all');
  return WORKSPACE_LOCATIONS.some((location) => location.id === candidate)
    ? candidate
    : 'all';
}

export function getStoredLocationValue(locationRecords, label) {
  const record = (locationRecords || []).find((location) => {
    const name = String(location.name || '').trim();
    return name === label || name.split(',')[0].trim() === label;
  });

  return record?.name || label;
}

export function matchesWorkspaceLocation(value, selectedLocation, locationRecords = []) {
  const selected = WORKSPACE_LOCATIONS.find((location) => location.id === selectedLocation) || WORKSPACE_LOCATIONS[0];
  const normalizedValue = value === null || value === undefined ? '' : String(value).trim();

  if (selected.kind === 'all') return true;
  if (selected.kind === 'specific') {
    return normalizedValue === getStoredLocationValue(locationRecords, selected.label);
  }

  // Global: intelligence that is not specific to either monitored region, i.e.
  // locationless events and events attributed to any other country.
  return (
    !normalizedValue
    || normalizedValue.toLowerCase() === 'unknown'
    || !MONITORED_REGIONS.has(normalizedValue.toLowerCase())
  );
}

export function filterEventsByWorkspace(events, selectedLocation, locationRecords) {
  return (events || []).filter((event) => matchesWorkspaceLocation(event.location, selectedLocation, locationRecords));
}

export const WEATHER_MONITORING_COUNTRIES = ['India', 'United States'];

export const WEATHER_SCOPES = Object.freeze([
  { id: 'global', label: 'Global', countries: WEATHER_MONITORING_COUNTRIES },
  { id: 'India', label: 'India', countries: ['India'] },
  { id: 'United States', label: 'United States', countries: ['United States'] },
]);

export function normalizeWeatherScope(value) {
  const candidate = String(value || 'global');
  return WEATHER_SCOPES.some((scope) => scope.id === candidate) ? candidate : 'global';
}

export function getWeatherScopeCountries(scope) {
  const selected = WEATHER_SCOPES.find((item) => item.id === normalizeWeatherScope(scope));
  return selected ? selected.countries : WEATHER_MONITORING_COUNTRIES;
}

function canonicalWeatherLocation(location) {
  const name = String(location?.name || '').trim();
  const country = String(location?.country || '').trim();
  return name && country ? `${name}, ${country}` : name;
}

export function getWeatherMonitoringLocations(locationRecords = []) {
  return (locationRecords || []).filter((location) => {
    const name = String(location?.name || '').trim();
    const country = String(location?.country || '').trim();
    return WEATHER_MONITORING_COUNTRIES.includes(country) && name !== country;
  });
}

export function getWeatherLocationsForScope(locationRecords = [], scope = 'global') {
  const countries = getWeatherScopeCountries(scope);
  return getWeatherMonitoringLocations(locationRecords).filter(
    (location) => countries.includes(String(location?.country || '').trim()),
  );
}

export function getWeatherLocationsForWorkspace(locationRecords = [], selectedLocation = 'all') {
  if (selectedLocation === 'India' || selectedLocation === 'United States') {
    return getWeatherLocationsForScope(locationRecords, selectedLocation);
  }
  return getWeatherLocationsForScope(locationRecords, 'global');
}

function eventMatchesWeatherLocation(event, location) {
  const eventLocation = String(event?.location || '').trim().toLowerCase();
  const city = String(location?.name || '').trim().toLowerCase();
  const canonical = canonicalWeatherLocation(location).toLowerCase();
  return eventLocation === canonical || eventLocation.startsWith(`${city},`);
}

function highestRiskForEvent(eventId, risks) {
  const rank = { critical: 4, high: 3, medium: 2, low: 1 };
  return (risks || [])
    .filter((risk) => risk?.event_id === eventId)
    .sort((left, right) => {
      const severityDelta = (rank[String(right?.severity || '').toLowerCase()] || 0)
        - (rank[String(left?.severity || '').toLowerCase()] || 0);
      return severityDelta || Number(right?.risk_score || 0) - Number(left?.risk_score || 0);
    })[0] || null;
}

export function buildWeatherCityStates(locationRecords = [], events = [], risks = []) {
  const weatherEvents = (events || []).filter((event) => event?.event_type === 'Weather');

  return getWeatherMonitoringLocations(locationRecords).map((location) => {
    const weatherEvent = weatherEvents
      .filter((event) => eventMatchesWeatherLocation(event, location))
      .sort((left, right) => new Date(getEventTimestamp(right)) - new Date(getEventTimestamp(left)))[0] || null;
    const risk = weatherEvent ? highestRiskForEvent(weatherEvent.id, risks) : null;

    return {
      location,
      canonicalLocation: canonicalWeatherLocation(location),
      weatherEvent,
      risk,
    };
  });
}

function getEventTimestamp(event) {
  return event?.event_time || event?.received_at || event?.created_at || 0;
}

export async function refreshWeatherLocations(locations, requestWeather) {
  const results = [];
  for (const location of locations || []) {
    try {
      const response = await requestWeather(canonicalWeatherLocation(location));
      results.push({ location: location.name, status: 'success', response });
    } catch (error) {
      results.push({
        location: location.name,
        status: 'error',
        error: error?.message || 'Weather request failed.',
      });
    }
  }
  return results;
}
