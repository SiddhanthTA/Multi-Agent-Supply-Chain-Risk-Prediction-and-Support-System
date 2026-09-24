import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ArrowLeft, AlertTriangle, Calendar, MapPin, Lightbulb, Shield } from 'lucide-react';
import { format } from 'date-fns';
import { formatLocationDisplay } from '@/lib/locationDisplay';
import RiskInvestigationPanel from '@/components/RiskInvestigationPanel';

const fetchRiskDetails = async (id) => {
  const riskRes = await api.get(`/risks/${id}`);
  const risk = riskRes.data;

  let event = null;
  if (risk.event_id) {
    try {
      const eventRes = await api.get(`/events/${risk.event_id}`);
      event = eventRes.data;
    } catch (err) {
      console.warn('Could not fetch associated event', err);
    }
  }

  let prediction = null;
  try {
    const predsRes = await api.get('/predictions/');
    prediction = predsRes.data.find((item) => Number(item.risk_id) === Number(id));
  } catch (err) {
    console.warn('Could not fetch associated predictions', err);
  }

  let recommendation = null;
  if (prediction) {
    try {
      const recRes = await api.get('/recommendations/');
      recommendation = recRes.data.find((item) => Number(item.prediction_id) === Number(prediction.id));
    } catch (err) {
      console.warn('Could not fetch associated recommendation', err);
    }
  }

  const eventLocation = formatLocationDisplay(event?.location);
  return { ...risk, event: event ? { ...event, displayLocation: eventLocation.label, displayLocationSecondary: eventLocation.secondary } : null, prediction, recommendation };
};

export default function RiskDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: risk, isLoading, isError, error } = useQuery({
    queryKey: ['risk', id],
    queryFn: () => fetchRiskDetails(id),
  });

  if (isError) {
    return (
      <div className="p-8 text-center max-w-7xl mx-auto">
        <AlertTriangle className="mx-auto h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load risk details</h2>
        <p className="text-muted-foreground mt-2">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard
        </Button>
      </div>
    );
  }

  const riskScore = Number(risk?.risk_score || 0);
  const confidence = Number(risk?.probability ?? risk?.prediction?.confidence_score ?? 0) * 100;
  const isActive = String(risk?.status || '').toLowerCase() === 'active';

  return (
    <div className="max-w-5xl mx-auto pb-10 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Risk Detail</h2>
          <p className="text-muted-foreground">Detailed assessment for this supply-chain risk signal.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-[1.5fr_0.9fr]">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4 text-primary" />
                    {risk?.event?.displayLocation || 'Global'}
                    {risk?.event?.displayLocationSecondary && (
                      <span className="text-xs text-muted-foreground">({risk.event.displayLocationSecondary})</span>
                    )}
                    <span>•</span>
                    <Calendar className="h-4 w-4 text-primary" />
                    {risk?.created_at ? format(new Date(risk.created_at), 'MMM d, yyyy h:mm a') : 'Unknown date'}
                  </div>
                  <CardTitle className="text-2xl font-bold leading-tight">{risk?.event?.title || risk?.risk_name || 'Risk Event'}</CardTitle>
                </div>
                <SeverityBadge severity={risk?.severity} />
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">What happened?</h3>
                <div className="rounded-2xl border border-border/60 bg-muted/10 p-4 text-sm leading-relaxed text-muted-foreground">
                  {risk?.event?.description || 'No event details are currently attached to this record.'}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <MetricCard label="Risk Status" value={isActive ? 'Active' : 'Inactive'} tone={isActive ? 'destructive' : 'low'} />
                <MetricCard label="Risk Score" value={`${riskScore.toFixed(0)} / 100`} tone="default" />
                <MetricCard label="Confidence" value={`${confidence.toFixed(0)}%`} tone="info" />
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">Where?</h3>
                <div className="rounded-2xl border border-border/60 bg-muted/10 p-4">
                  <div className="flex items-center gap-2 font-medium text-foreground">
                    <MapPin className="h-4 w-4 text-primary" />
                    {risk?.event?.displayLocation || 'Global'}
                    {risk?.event?.displayLocationSecondary && (
                      <span className="text-xs text-muted-foreground block">{risk.event.displayLocationSecondary}</span>
                    )}
                  </div>
                  <div className="mt-2 text-sm text-muted-foreground">{risk?.event?.source || 'Source unavailable'}</div>
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">Assessment</h3>
                <div className="rounded-2xl border border-border/60 bg-muted/10 p-4 text-sm leading-relaxed text-muted-foreground">
                  {isActive
                    ? `This signal is currently active and should be reviewed as a ${risk?.severity || 'unknown'} severity ${risk?.risk_name || 'risk'} event.`
                    : 'Normal conditions are being tracked as context only. No active disruption is currently flagged for this weather observation.'}
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg"><Lightbulb className="h-5 w-5 text-purple-500" /> Current Recommendation</CardTitle>
                <CardDescription>Rule-based operating guidance currently attached to this event.</CardDescription>
              </CardHeader>
              <CardContent>
                {risk?.recommendation ? (
                  <div className="space-y-4">
                    <div className="font-semibold text-base">{risk.recommendation.recommendation_title}</div>
                    <p className="text-sm leading-relaxed text-muted-foreground">{risk.recommendation.recommendation_text}</p>
                    <div className="flex items-center justify-between border-t border-border/60 pt-3 text-xs text-muted-foreground">
                      <span>Priority: {risk.recommendation.priority}</span>
                      <span>{risk.recommendation.status}</span>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-border/60 bg-muted/10 p-4 text-sm text-muted-foreground">
                    No recommendation is attached to this record yet.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg"><Shield className="h-5 w-5 text-primary" /> Source Event</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center justify-between gap-3">
                  <span>Type</span>
                  <span className="font-medium text-foreground">{risk?.event?.event_type || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Source</span>
                  <span className="font-medium text-foreground">{risk?.event?.source || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Risk Type</span>
                  <span className="font-medium text-foreground">{risk?.risk_type || risk?.risk_name || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Prediction Model</span>
                  <span className="font-medium text-foreground">{risk?.prediction?.prediction_model || 'Rule-based'}</span>
                </div>
              </CardContent>
            </Card>
            <RiskInvestigationPanel riskId={risk?.id} />
          </div>
        </div>
      )}
    </div>
  );
}

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline">Unknown</Badge>;
  const normalized = String(severity).toLowerCase();

  if (normalized === 'critical') return <Badge variant="critical">Critical</Badge>;
  if (normalized === 'high') return <Badge variant="high">High</Badge>;
  if (normalized === 'medium') return <Badge variant="medium">Medium</Badge>;
  if (normalized === 'low') return <Badge variant="low">Low</Badge>;

  return <Badge variant="outline">{severity}</Badge>;
}

function MetricCard({ label, value, tone = 'default' }) {
  const toneStyles = {
    default: 'border-border/60 bg-muted/10 text-foreground',
    destructive: 'border-destructive/30 bg-destructive/10 text-destructive',
    low: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
    info: 'border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400',
  };

  return (
    <div className={`rounded-2xl border p-4 ${toneStyles[tone]}`}>
      <div className="text-xs uppercase tracking-[0.15em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-xl font-bold">{value}</div>
    </div>
  );
}
