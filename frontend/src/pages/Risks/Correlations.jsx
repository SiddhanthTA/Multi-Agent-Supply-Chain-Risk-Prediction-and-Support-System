import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  InvalidRiskRoute,
  PageEmpty,
  PageError,
  PageFootnote,
  PageLoading,
  RiskPageHeader,
  RiskTargetBanner,
} from '@/components/risk/RiskPageShell';
import {
  CORRELATION_LEVEL_VARIANTS,
  correlationLevelLabel,
} from '@/lib/riskInvestigation';
import { fetchCorrelations, fetchRiskContext, useRiskIdParam } from '@/lib/riskReports';

/**
 * Correlation reasons arrive as short sentences from the existing engine. This
 * turns each into a compact chip prefixed with its dimension, without changing
 * any wording the engine produced.
 */
function reasonChips(item) {
  const chips = [];
  for (const reason of item.reasons || []) {
    const text = String(reason);
    const value = text.replace(/:\s*/, ' · ');
    let prefix = 'Signal';
    if (/^same location/i.test(text)) prefix = 'Location';
    else if (/^same risk type/i.test(text)) prefix = 'Risk Type';
    else if (/^same event category/i.test(text)) prefix = 'Category';
    else if (/^within /i.test(text)) prefix = 'Time';
    else if (/^same (source|company)/i.test(text)) prefix = 'Source';
    chips.push({ key: `${prefix}-${value}`, label: `${prefix} · ${value}` });
  }
  for (const dependency of item.shared_company_dependencies || []) {
    chips.push({
      key: `Dependency-${dependency}`,
      label: `Dependency · ${dependency}`,
    });
  }
  return chips;
}

function CorrelationCard({ item }) {
  const navigate = useNavigate();
  const chips = reasonChips(item);
  return (
    <div className="ss-row">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Badge variant={CORRELATION_LEVEL_VARIANTS[item.relationship_level] || 'outline'}>
          {item.relationship_label || correlationLevelLabel(item.relationship_level)}
        </Badge>
        <span className="text-xs font-medium tabular-nums text-muted-foreground">
          {item.correlation_score} / 100
        </span>
      </div>

      <p className="mt-2.5 text-sm font-medium leading-snug text-foreground">{item.event_title}</p>

      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
        {item.severity && <span>{item.severity}</span>}
        {item.risk_type && <span>{item.risk_type}</span>}
        {item.location && <span>{item.location}</span>}
        {item.event_category && <span>{item.event_category}</span>}
        {item.days_apart != null && <span>{item.days_apart} days apart</span>}
      </div>

      {chips.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {chips.map((chip) => (
            <Badge key={chip.key} variant="secondary" className="text-[10px] font-normal">
              {chip.label}
            </Badge>
          ))}
        </div>
      )}

      <Button
        variant="outline"
        size="sm"
        className="mt-3"
        // Guards the related risk's own id, so a malformed card can never
        // navigate to /risks/undefined.
        disabled={item.risk_id == null}
        onClick={() => navigate(`/risks/${item.risk_id}`)}
      >
        View Risk
      </Button>
    </div>
  );
}

/**
 * Risk Correlations for one risk.
 *
 * The scoring itself is unchanged: this page only presents the existing
 * deterministic result, its reasons, and navigation into the related risks.
 */
export default function RiskCorrelationsPage() {
  // The URL is the source of truth for the current risk.
  const riskId = useRiskIdParam();
  const navigate = useNavigate();
  const enabled = riskId != null;

  const context = useQuery({
    queryKey: ['riskContext', riskId],
    queryFn: () => fetchRiskContext(riskId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  const correlations = useQuery({
    queryKey: ['riskCorrelations', riskId],
    queryFn: () => fetchCorrelations(riskId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  const items = correlations.data?.correlations || [];

  if (!enabled) return <InvalidRiskRoute />;

  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <RiskPageHeader
        title="Risk Correlations"
        subtitle="Related risk signals identified from monitored intelligence."
        onBack={() => navigate(`/risks/${riskId}`)}
      />
      <RiskTargetBanner risk={context.data?.risk} event={context.data?.event} />

      {correlations.isLoading ? (
        <PageLoading message="Loading related risks..." />
      ) : correlations.isError ? (
        <PageError message="Unable to load related risks." onRetry={() => correlations.refetch()} />
      ) : items.length === 0 ? (
        <PageEmpty>
          {correlations.data?.message || 'No related risks were identified for this signal.'}
        </PageEmpty>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            {correlations.data.total_candidates_considered} candidate risk(s) considered within a{' '}
            {correlations.data.analysis_window_days}-day window.
          </p>
          <ul className="space-y-3">
            {items.map((item, index) => (
              <li key={item.risk_id} className="ss-stagger" style={{ '--ss-i': index }}>
                <CorrelationCard item={item} />
              </li>
            ))}
          </ul>
        </>
      )}

      {correlations.data?.disclaimer && <PageFootnote>{correlations.data.disclaimer}</PageFootnote>}
    </div>
  );
}
