import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildWeatherCityStates,
  getWeatherLocationsForWorkspace,
  getWeatherMonitoringLocations,
  normalizeWorkspaceLocation,
  refreshWeatherLocations,
  WORKSPACE_LOCATIONS,
} from './locationWorkspace.js';

test('location workspace exposes only the supported selector options', () => {
  assert.deepEqual(
    WORKSPACE_LOCATIONS.map(({ id, label }) => ({ id, label })),
    [
      { id: 'all', label: 'All Locations' },
      { id: 'global', label: 'Global' },
      { id: 'India', label: 'India' },
      { id: 'United States', label: 'United States' },
    ],
  );
});

test('location workspace preserves supported persisted values and migrates stale ones', () => {
  for (const location of WORKSPACE_LOCATIONS) {
    assert.equal(normalizeWorkspaceLocation(location.id), location.id);
  }

  assert.equal(normalizeWorkspaceLocation('Singapore'), 'all');
  assert.equal(normalizeWorkspaceLocation('Dubai'), 'all');
  assert.equal(normalizeWorkspaceLocation('Rotterdam'), 'all');
  assert.equal(normalizeWorkspaceLocation(null), 'all');
});

const locationRecords = [
  { id: 1, name: 'India', country: 'India', latitude: 20.5937, longitude: 78.9629 },
  { id: 2, name: 'United States', country: 'United States', latitude: 39.8283, longitude: -98.5795 },
  { id: 3, name: 'Mumbai', country: 'India', latitude: 19.076, longitude: 72.8777 },
  { id: 4, name: 'Delhi', country: 'India', latitude: 28.6139, longitude: 77.209 },
  { id: 5, name: 'Chennai', country: 'India', latitude: 13.0827, longitude: 80.2707 },
  { id: 6, name: 'Kolkata', country: 'India', latitude: 22.5726, longitude: 88.3639 },
  { id: 7, name: 'Los Angeles', country: 'United States', latitude: 34.0522, longitude: -118.2437 },
  { id: 8, name: 'Houston', country: 'United States', latitude: 29.7604, longitude: -95.3698 },
  { id: 9, name: 'Chicago', country: 'United States', latitude: 41.8781, longitude: -87.6298 },
  { id: 10, name: 'New York', country: 'United States', latitude: 40.7128, longitude: -74.006 },
];

test('weather cities exclude primary countries and group by workspace', () => {
  const weatherLocations = getWeatherMonitoringLocations(locationRecords);
  assert.equal(weatherLocations.length, 8);
  assert.deepEqual(
    getWeatherLocationsForWorkspace(locationRecords, 'India').map((location) => location.name),
    ['Mumbai', 'Delhi', 'Chennai', 'Kolkata'],
  );
  assert.deepEqual(
    getWeatherLocationsForWorkspace(locationRecords, 'United States').map((location) => location.name),
    ['Los Angeles', 'Houston', 'Chicago', 'New York'],
  );
  assert.equal(getWeatherLocationsForWorkspace(locationRecords, 'all').length, 8);
  assert.equal(getWeatherLocationsForWorkspace(locationRecords, 'global').length, 8);
});

test('weather city states join the latest Event to its highest-priority Risk', () => {
  const events = [
    {
      id: 50,
      event_type: 'Weather',
      location: 'Mumbai, India',
      title: 'Heavy rain',
      event_time: '2026-09-24T10:00:00Z',
    },
    {
      id: 51,
      event_type: 'Weather',
      location: 'Chennai, India',
      title: 'Clear',
      event_time: '2026-09-24T09:00:00Z',
    },
  ];
  const risks = [
    { id: 90, event_id: 50, risk_type: 'Severe Weather', severity: 'High', risk_score: 85, status: 'Active' },
    { id: 91, event_id: 50, risk_type: 'Natural Disaster', severity: 'Critical', risk_score: 100, status: 'Active' },
  ];

  const states = buildWeatherCityStates(locationRecords, events, risks);
  const mumbai = states.find((state) => state.location.name === 'Mumbai');
  const houston = states.find((state) => state.location.name === 'Houston');

  assert.equal(mumbai.weatherEvent.id, 50);
  assert.equal(mumbai.risk.id, 91);
  assert.equal(houston.weatherEvent, null);
  assert.equal(houston.risk, null);
});

test('weather refresh is sequential and continues after a city failure', async () => {
  const calls = [];
  const results = await refreshWeatherLocations(
    locationRecords.slice(2, 5),
    async (location) => {
      calls.push(location);
      if (location.startsWith('Delhi')) throw new Error('Weather unavailable');
      return { status: 200, data: { location } };
    },
  );

  assert.deepEqual(calls, ['Mumbai, India', 'Delhi, India', 'Chennai, India']);
  assert.deepEqual(results.map((result) => result.status), ['success', 'error', 'success']);
  assert.match(results[1].error, /Weather unavailable/);
});