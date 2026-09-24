import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function markerColor(risk) {
  const severity = String(risk?.severity || '').toLowerCase();
  if (severity === 'critical' || severity === 'high') return '#dc2626';
  if (severity === 'medium') return '#d97706';
  if (severity === 'low') return '#16a34a';
  return '#64748b';
}

function temperatureFromDescription(description) {
  const match = String(description || '').match(/Temperature:\s*([^\s°]+)/i);
  return match ? `${match[1]}°C` : 'Unavailable';
}

function observationTime(event) {
  return event?.event_time || event?.received_at || event?.created_at || null;
}

export default function WeatherRiskMap({ cityStates = [] }) {
  const grouped = cityStates.reduce((result, state) => {
    const country = String(state.location?.country || 'Unknown');
    (result[country] ||= []).push(state);
    return result;
  }, {});

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {Object.entries(grouped).map(([country, states]) => (
          <span key={country} className="rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-medium">
            {country}: {states.length} cities
          </span>
        ))}
      </div>
      <div className="h-[360px] w-full overflow-hidden rounded-lg border border-border">
        <MapContainer center={[24, -20]} zoom={2} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {cityStates.map((state) => {
            const { location, weatherEvent, risk } = state;
            if (location.latitude == null || location.longitude == null) return null;
            return (
              <CircleMarker
                key={location.id || state.canonicalLocation}
                center={[location.latitude, location.longitude]}
                radius={8}
                pathOptions={{ color: markerColor(risk), fillColor: markerColor(risk), fillOpacity: 0.8 }}
              >
                <Popup>
                  <div className="min-w-48 space-y-1 text-sm">
                    <p className="font-semibold">{location.name}, {location.country}</p>
                    {weatherEvent ? (
                      <>
                        <p>{weatherEvent.title || weatherEvent.description || 'Current conditions'}</p>
                        <p>Temperature: {temperatureFromDescription(weatherEvent.description)}</p>
                        <p>Observed: {observationTime(weatherEvent) || 'Unavailable'}</p>
                        <p>Risk: {risk?.risk_type || risk?.risk_name || 'Not classified'}</p>
                        <p>Severity: {risk?.severity || 'Unrated'}</p>
                        <p>Status: {risk?.status || 'Unavailable'}</p>
                        <p>Risk score: {risk ? Number(risk.risk_score || 0).toFixed(0) : '—'}</p>
                      </>
                    ) : (
                      <p>Weather data not collected yet.</p>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}