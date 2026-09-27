import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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
import { fetchImpactMap, fetchRiskContext, useRiskIdParam } from '@/lib/riskReports';

function Column({ title, items }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-xs font-medium text-foreground">{title}</p>
      <ul className="mt-1.5 space-y-1">
        {items.map((item) => (
          <li key={item} className="text-sm leading-relaxed text-muted-foreground">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Supply Chain Impact for one risk.
 *
 * The mapping is the existing deterministic result. Every field below is a
 * potential exposure area derived from configured dependencies; nothing here
 * claims a confirmed business impact.
 */
export default function RiskSupplyChainImpactPage() {
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

  const impact = useQuery({
    queryKey: ['riskImpactMap', riskId],
    queryFn: () => fetchImpactMap(riskId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  const data = impact.data;
  const mappings = data?.mappings || [];

  if (!enabled) return <InvalidRiskRoute />;

  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <RiskPageHeader
        title="Supply Chain Impact"
        subtitle="Potential supply-chain areas affected by this risk."
        onBack={() => navigate(`/risks/${riskId}`)}
      />
      <RiskTargetBanner risk={context.data?.risk} event={context.data?.event} />

      {impact.isLoading ? (
        <PageLoading message="Mapping potential supply-chain impact..." />
      ) : impact.isError ? (
        <PageError message="Unable to load supply-chain impact." onRetry={() => impact.refetch()} />
      ) : !data || !mappings.length ? (
        <PageEmpty>
          {data?.summary || 'No company-specific supply-chain impact was identified.'}
        </PageEmpty>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{data.summary}</p>
          <div className="space-y-3">
            {mappings.map((mapping, index) => (
              <article
                key={mapping.dependency}
                className="ss-stagger rounded-xl border border-border/60 bg-card p-5"
                style={{ '--ss-i': index }}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
                    {mapping.dependency}
                  </h2>
                  <Badge
                    variant={mapping.relevance === 'direct' ? 'default' : 'secondary'}
                    className="text-[10px] uppercase tracking-wide"
                  >
                    {mapping.relevance}
                  </Badge>
                </div>
                <div className="mt-4 grid gap-5 sm:grid-cols-3">
                  <Column title="Supply-chain areas" items={mapping.supply_chain_areas} />
                  <Column title="Potential impacts" items={mapping.potential_impacts} />
                  <Column title="Areas to verify" items={mapping.verification_checks} />
                </div>
              </article>
            ))}
          </div>
        </>
      )}

      {data?.data_limitations?.length > 0 && (
        <div className="space-y-1">
          {data.data_limitations.map((limitation) => (
            <p key={limitation} className="text-xs leading-relaxed text-muted-foreground">
              {limitation}
            </p>
          ))}
        </div>
      )}

      <PageFootnote>
        Impact mapping identifies potential exposure areas from available intelligence and configured company
        dependencies. It does not quantify actual business impact.
      </PageFootnote>
    </div>
  );
}
