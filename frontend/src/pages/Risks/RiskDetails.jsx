import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  ClipboardList,
  Link2,
  MapPin,
  Network,
  Shield,
  Sparkles,
} from 'lucide-react';
import { format } from 'date-fns';
import { formatLocationDisplay } from '@/lib/locationDisplay';
import { CompanyRelevanceContext } from '@/components/CompanyRelevance';
import ResolveRiskAction from '@/components/risk/ResolveRiskAction';
import { RESOLVE_RISK_TEXT } from '@/lib/riskInvestigation';
import { assertRiskId, fetchRiskReportStatus, fetchRiskResolution, useRiskIdParam } from '@/lib/riskReports';

const fetchRiskDetails = async (id) => {
  const riskRes = await api.get(`/risks/${assertRiskId(id)}`);
  const risk = riskRes.data;

  let event = null;
  let companyRelevance = null;
  if (risk.event_id) {
    try {
      const eventRes = await api.get(`/events/${risk.event_id}`);
      event = eventRes.data;
    } catch (err) {
      console.warn('Could not fetch associated event', err);
    }
  }

  if (risk.event_id) {
    try {
      const relevanceRes = await api.get(`/company-profile/relevance/events/${risk.event_id}`);
      companyRelevance = relevanceRes.data;
    } catch (err) {
      console.warn('Could not fetch company relevance', err);
    }
  }

  let prediction = null;
  try {
    const predsRes = await api.get('/predictions/');
    prediction = predsRes.data.find((item) => Number(item.risk_id) === Number(id));
  } catch (err) {
    console.warn('Could not fetch associated predictions', err);
  }

  const eventLocation = formatLocationDisplay(event?.location);
  return { ...risk, event: event ? { ...event, displayLocation: eventLocation.label, displayLocationSecondary: eventLocation.secondary } : null, prediction, companyRelevance };
};

export default function RiskDetails() {
  // The URL is the source of truth for the current risk.
  const riskId = useRiskIdParam();
  const navigate = useNavigate();
  const enabled = riskId != null;

  const { data: risk, isLoading, isError, error } = useQuery({
    queryKey: ['risk', riskId],
    queryFn: () => fetchRiskDetails(riskId),
    enabled,
  });

  // Whether the investigation / response plan already exist is decided by the
  // backend, not by local component state, so the action labels are always
  // correct and nothing is regenerated on a revisit.
  const reportStatus = useQuery({
    queryKey: ['riskReportStatus', riskId],
    queryFn: () => fetchRiskReportStatus(riskId),
    staleTime: 60 * 1000,
    enabled,
  });
  const hasInvestigation = Boolean(reportStatus.data?.investigation_exists);
  const hasResponsePlan = Boolean(reportStatus.data?.response_plan_exists);

  // Resolution readiness is decided by the backend for the signed-in user.
  const resolution = useQuery({
    queryKey: ['riskResolution', riskId],
    queryFn: () => fetchRiskResolution(riskId),
    staleTime: 30 * 1000,
    enabled,
  });

  if (!enabled) {
    return (
      <div className="ss-page ss-enter mx-auto max-w-5xl pb-10">
        <div className="p-8 text-center">
          <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-destructive" />
          <h2 className="text-2xl font-bold text-destructive">Risk not specified</h2>
          <p className="mt-2 text-muted-foreground">This link does not contain a valid risk id.</p>
          <Button variant="outline" className="mt-4" onClick={() => navigate('/risks')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Risks
          </Button>
        </div>
      </div>
    );
  }

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

  const isRiskResolved = String(risk?.status || '').toLowerCase() === 'resolved';

  return (
    <div className="ss-page ss-enter mx-auto max-w-5xl pb-10 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Risk Detail</h2>
            <p className="text-muted-foreground">Detailed assessment for this supply-chain risk.</p>
          </div>
          {/* A resolved risk keeps every piece of its historical intelligence. */}
          {isRiskResolved && (
            <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
              <CheckCircle2 className="mr-1 h-3 w-3" />
              {RESOLVE_RISK_TEXT.resolvedBadge}
            </Badge>
          )}
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
            </CardContent>
          </Card>

          <div className="space-y-6">
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
              </CardContent>
            </Card>
            {risk?.companyRelevance && (
              <CompanyRelevanceContext row={risk.companyRelevance} />
            )}
            <RiskActions
              riskId={riskId}
              hasInvestigation={hasInvestigation}
              hasResponsePlan={hasResponsePlan}
              resolution={resolution}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function RiskActions({ riskId, hasInvestigation, hasResponsePlan, resolution }) {
  const navigate = useNavigate();
  if (riskId == null) return null;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Network className="h-4 w-4 text-primary" /> Risk Intelligence
          </CardTitle>
          <CardDescription>
            Open the analysis for this risk. Nothing is recomputed when you return to it.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button
            variant={hasInvestigation ? 'outline' : 'default'}
            onClick={() => navigate(`/risks/${riskId}/investigation`)}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {hasInvestigation ? 'View Investigation Report' : 'Investigate Risk'}
          </Button>
          <Button variant="outline" onClick={() => navigate(`/risks/${riskId}/correlations`)}>
            <Link2 className="mr-2 h-4 w-4" />
            View Correlations
          </Button>
          <Button variant="outline" onClick={() => navigate(`/risks/${riskId}/impact`)}>
            <Network className="mr-2 h-4 w-4" />
            View Supply Chain Impact
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ClipboardList className="h-4 w-4 text-primary" /> Response
          </CardTitle>
          <CardDescription>
            {hasResponsePlan
              ? 'A response plan has already been prepared for this risk.'
              : hasInvestigation
                ? 'Prepare decision-support options from the stored investigation.'
                : 'Investigate the risk first to prepare a response plan.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasResponsePlan ? (
            <Button onClick={() => navigate(`/risks/${riskId}/response-plan`)}>
              <ClipboardList className="mr-2 h-4 w-4" />
              View Response Plan
            </Button>
          ) : (
            <Button
              variant="outline"
              disabled={!hasInvestigation}
              onClick={() => navigate(`/risks/${riskId}/response-plan`)}
            >
              <ClipboardList className="mr-2 h-4 w-4" />
              Generate Response Plan
            </Button>
          )}
          {/* Final lifecycle step: only offered once both reports exist. */}
          <div className="mt-3 border-t border-border/60 pt-3">
            <ResolveRiskAction
              riskId={riskId}
              status={resolution?.status}
              resolvable={resolution?.resolvable || (hasInvestigation && hasResponsePlan)}
            />
          </div>
        </CardContent>
      </Card>
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
