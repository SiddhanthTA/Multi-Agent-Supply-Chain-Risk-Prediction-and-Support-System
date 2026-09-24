import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ArrowLeft, MapPin, Calendar, Globe, AlertTriangle, Activity } from 'lucide-react';
import { format } from 'date-fns';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { formatLocationDisplay } from '@/lib/locationDisplay';
import RiskInvestigationPanel from '@/components/RiskInvestigationPanel';

// Fix leaflet default icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const fetchEventDetails = async (id) => {
  const [eventRes, risksRes] = await Promise.all([
    api.get(`/events/${id}`),
    api.get('/risks/')
  ]);
  
  const event = eventRes.data;
  // Find associated risks for this event
  const relatedRisks = risksRes.data.filter(r => r.event_id === parseInt(id));
  
  const highestSeverityRisk = relatedRisks.length > 0 
    ? relatedRisks.reduce((prev, current) => {
        const scores = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
        const prevScore = scores[prev.severity?.toLowerCase()] || 0;
        const currScore = scores[current.severity?.toLowerCase()] || 0;
        return currScore > prevScore ? current : prev;
      })
    : null;
  
  const displayLocation = formatLocationDisplay(event.location);

  return {
    ...event,
    displaySeverity: highestSeverityRisk?.severity || 'Unknown',
    displayLocation: displayLocation.label,
    displayLocationSecondary: displayLocation.secondary,
    relatedRisks,
    highestSeverityRisk
  };
};

export default function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: event, isLoading, isError, error } = useQuery({
    queryKey: ['event', id],
    queryFn: () => fetchEventDetails(id),
  });

  if (isError) {
    return (
      <div className="p-8 text-center">
        <Activity className="mx-auto h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load event details</h2>
        <p className="text-muted-foreground mt-2">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/events')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Events
        </Button>
      </div>
    );
  }

  const hasValidCoordinates = event && typeof event.latitude === 'number' && typeof event.longitude === 'number' && !isNaN(event.latitude) && !isNaN(event.longitude);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/events')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Event Details</h2>
          <p className="text-muted-foreground">Comprehensive information and associated risks.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Event Info */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl">
                    {isLoading ? <Skeleton className="h-8 w-[300px]" /> : event?.title}
                  </CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-4">
                    {isLoading ? (
                      <Skeleton className="h-4 w-[200px]" />
                    ) : (
                      <>
                        <span className="flex items-center gap-1"><Activity className="h-4 w-4" /> {event?.event_type}</span>
                        <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {event?.displayLocation}</span>
                        {event?.displayLocationSecondary && (
                          <span className="text-xs text-muted-foreground">({event.displayLocationSecondary})</span>
                        )}
                      </>
                    )}
                  </CardDescription>
                </div>
                {!isLoading && <SeverityBadge severity={event?.displaySeverity} />}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-[80%]" />
                  </div>
                ) : (
                  <p className="text-muted-foreground whitespace-pre-wrap">{event?.description || 'No description provided.'}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 border-t pt-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Status</h4>
                  {isLoading ? <Skeleton className="h-5 w-20" /> : <Badge variant="outline">{event?.status}</Badge>}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Event Time</h4>
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    {isLoading ? <Skeleton className="h-5 w-32" /> : (event?.event_time ? format(new Date(event.event_time), 'PPpp') : 'Unknown')}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Source</h4>
                  <div className="text-sm">
                    {isLoading ? <Skeleton className="h-5 w-24" /> : (event?.source || 'Manual/Unknown')}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">External Link</h4>
                  {isLoading ? <Skeleton className="h-5 w-24" /> : (
                    event?.url ? (
                      <a href={event.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-primary hover:underline">
                        <Globe className="h-4 w-4" /> View Source
                      </a>
                    ) : <span className="text-sm text-muted-foreground">Not available</span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Related Risks */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Associated AI Risks</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : event?.relatedRisks?.length > 0 ? (
                <div className="space-y-4">
                  {event.relatedRisks.map(risk => (
                    <div key={risk.id} className="flex justify-between items-center p-3 rounded-lg border bg-muted/20">
                      <div>
                        <p className="font-medium">{risk.risk_name}</p>
                        <p className="text-sm text-muted-foreground">Type: {risk.risk_type} • Score: {risk.risk_score != null ? `${Number(risk.risk_score).toFixed(2)}%` : '0%'}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <SeverityBadge severity={risk.severity} />
                        <Badge variant="outline" className="text-[10px] uppercase tracking-wider">{risk.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No specific AI risks have been associated with this event yet.</p>
              )}
            </CardContent>
          </Card>

          {!isLoading && (
            <RiskInvestigationPanel
              riskId={event?.highestSeverityRisk?.id}
              buttonLabel="Investigate Highest-Priority Risk"
            />
          )}
        </div>

        {/* Sidebar / Map */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Geospatial Location</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[250px] w-full rounded-md" />
              ) : hasValidCoordinates ? (
                <div className="h-[250px] w-full rounded-md overflow-hidden border">
                  <MapContainer 
                    center={[event.latitude, event.longitude]} 
                    zoom={5} 
                    scrollWheelZoom={false}
                    className="h-full w-full"
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={[event.latitude, event.longitude]}>
                      <Popup>
                        {event.displayLocation !== 'Not specified' ? event.displayLocation : event.title}
                      </Popup>
                    </Marker>
                  </MapContainer>
                </div>
              ) : (
                <div className="h-[250px] w-full rounded-md border border-dashed flex flex-col items-center justify-center bg-muted/10 text-muted-foreground p-6 text-center">
                  <MapPin className="h-10 w-10 mb-2 opacity-20" />
                  <p className="font-medium text-sm">Location coordinates unavailable</p>
                  <p className="text-xs mt-1">This event does not contain valid latitude/longitude data for map rendering.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline">Unknown</Badge>;
  const lower = severity.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="high">{severity}</Badge>;
  if (lower === 'medium') return <Badge variant="medium">{severity}</Badge>;
  if (lower === 'low') return <Badge variant="low">{severity}</Badge>;
  return <Badge variant="outline">{severity}</Badge>;
}
