import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { CheckCircle2, MapPin } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { SeverityBadge } from '@/components/risk/RiskPageShell';
import { ReopenRiskButton } from '@/components/risk/ResolveRiskAction';
import { RESOLVE_RISK_TEXT } from '@/lib/riskInvestigation';
import { fetchResolvedRisks } from '@/lib/riskReports';

/**
 * Resolved Risks.
 *
 * Separate from the active Risks list. Each card shows the risk's original
 * assessment, which is never modified by resolution. Opening a card goes to the
 * normal Risk Details page, where the investigation, response plan,
 * correlations and supply-chain impact all remain available.
 */
export default function ResolvedRisks() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['resolvedRisks'],
    queryFn: fetchResolvedRisks,
    staleTime: 30 * 1000,
  });

  const items = data || [];

  return (
    <div className="ss-page ss-enter mx-auto max-w-6xl space-y-5 pb-10">
      <header className="border-b border-border/70 pb-4">
        <h1 className="text-2xl font-semibold tracking-tight">
          {RESOLVE_RISK_TEXT.pageTitle}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {RESOLVE_RISK_TEXT.pageSubtitle}
        </p>
      </header>

      {isLoading ? (
        <p className="py-10 text-center text-sm text-muted-foreground">Loading resolved risks...</p>
      ) : isError ? (
        <p className="py-10 text-center text-sm text-destructive">
          Unable to load resolved risks.
        </p>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border/60 px-6 py-12 text-center text-sm text-muted-foreground">
          {RESOLVE_RISK_TEXT.empty}
        </div>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            {items.length} resolved risk{items.length === 1 ? '' : 's'}. Original scores and
            severities are unchanged, and all historical intelligence is retained.
          </p>
          <div className="grid gap-3">
            {items.map((item) => (
              <Card
                key={item.risk_id}
                className="cursor-pointer transition-colors duration-150 hover:border-primary/50"
                onClick={() => navigate(`/risks/${item.risk_id}`)}
              >
                <CardContent className="space-y-2.5 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="min-w-0 text-sm font-semibold leading-snug text-foreground">
                      {item.title || `Risk ${item.risk_id}`}
                    </p>
                    <div className="flex shrink-0 items-center gap-2">
                      <SeverityBadge severity={item.severity} />
                      <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        {RESOLVE_RISK_TEXT.resolvedBadge}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    {item.risk_type && <span>Type: {item.risk_type}</span>}
                    {item.category && <span>Category: {item.category}</span>}
                    {item.risk_score != null && (
                      <span>Original score: {Number(item.risk_score).toFixed(1)}</span>
                    )}
                    {item.location && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {item.location}
                      </span>
                    )}
                    {item.created_at && (
                      <span>Event date: {format(new Date(item.created_at), 'MMM d, yyyy')}</span>
                    )}
                  </div>

                  <div className="pt-1" onClick={(event) => event.stopPropagation()}>
                    <ReopenRiskButton riskId={item.risk_id} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
