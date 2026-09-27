import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { AlertTriangle, Link2, LoaderCircle } from 'lucide-react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  CORRELATION_LEVEL_VARIANTS,
  correlationLevelLabel,
} from '@/lib/riskInvestigation';

const fetchCorrelations = async (riskId) => {
  const response = await api.get(`/investigations/risk/${riskId}/correlations`);
  return response.data;
};

/**
 * Risk Correlation: deterministic, read-only similarity between this risk and
 * other stored SupplySentry risks. Scores describe similarity within monitored
 * data and never imply that two risks share a cause.
 */
export default function RiskCorrelationPanel({ riskId }) {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['riskCorrelations', riskId],
    queryFn: () => fetchCorrelations(riskId),
    enabled: riskId != null,
    staleTime: 5 * 60 * 1000,
  });

  if (riskId == null) return null;

  const correlations = data?.correlations || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Link2 className="h-5 w-5 text-primary" /> Risk Correlation
        </CardTitle>
        <CardDescription>
          Related risk signals identified from SupplySentry&apos;s monitored intelligence.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <LoaderCircle className="h-4 w-4 animate-spin" />
            Finding related risk signals…
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
            <div className="flex items-start gap-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Risk correlation unavailable.</p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="mt-2 underline underline-offset-2"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        ) : correlations.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {data?.message || 'No strongly related risk signals identified in the current monitoring window.'}
          </p>
        ) : (
          <>
            <p className="text-xs text-muted-foreground">
              {data.total_candidates_considered} candidate risk(s) considered within a{' '}
              {data.analysis_window_days}-day window. Scores describe similarity, not a shared cause.
            </p>
            <ul className="space-y-3">
              {correlations.map((item) => (
                <li
                  key={item.risk_id}
                  className="rounded-lg border border-border/60 bg-muted/10 p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={CORRELATION_LEVEL_VARIANTS[item.relationship_level] || 'outline'}>
                      {item.relationship_label || correlationLevelLabel(item.relationship_level)}
                    </Badge>
                    <span className="text-xs font-medium text-muted-foreground">
                      Correlation score: {item.correlation_score} / 100
                    </span>
                  </div>
                  <p className="mt-2 text-sm font-semibold text-foreground">{item.event_title}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    {item.severity && <span>{item.severity}</span>}
                    {item.risk_type && <span>{item.risk_type}</span>}
                    {item.location && <span>{item.location}</span>}
                    {item.event_category && <span>{item.event_category}</span>}
                    {item.days_apart != null && <span>{item.days_apart} days apart</span>}
                  </div>
                  {(item.reasons || []).length > 0 && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Related because: {(item.reasons || []).join('; ')}.
                    </p>
                  )}
                  {(item.shared_company_dependencies || []).length > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Shared company dependencies: {(item.shared_company_dependencies || []).join(', ')}.
                    </p>
                  )}
                  <Link
                    to={`/risks/${item.risk_id}`}
                    className="mt-2 inline-block text-xs font-medium text-primary underline underline-offset-2"
                  >
                    View related risk
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
        {!isLoading && data?.disclaimer && (
          <p className="border-t border-border/60 pt-3 text-xs text-muted-foreground">
            {data.disclaimer}
          </p>
        )}
        {isFetching && !isLoading && (
          <p className="text-xs text-muted-foreground">Refreshing correlations…</p>
        )}
      </CardContent>
    </Card>
  );
}
