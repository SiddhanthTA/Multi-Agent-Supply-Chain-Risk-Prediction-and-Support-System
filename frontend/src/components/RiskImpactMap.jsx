import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, LoaderCircle, Network, ShieldQuestion } from 'lucide-react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

const RELEVANCE_VARIANTS = { direct: 'default', indirect: 'secondary' };

const fetchImpactMap = async (riskId) => {
  const response = await api.get(`/investigations/risk/${riskId}/impact-map`);
  return response.data;
};

function Stage({ label, values }) {
  if (!values || values.length === 0) return null;
  return (
    <div className="mt-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {values.map((value) => (
          <Badge key={value} variant="secondary" className="text-[11px] font-normal">
            {value}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function FlowArrow() {
  return <div aria-hidden="true" className="my-1 text-muted-foreground/60">&#8595;</div>
}

/**
 * Supply Chain Impact Map: potential exposure areas derived from the
 * user's configured company dependencies via the existing relevance engine.
 * Every impact is explicitly potential; no actual exposure is asserted.
 */
export default function RiskImpactMap({ riskId }) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['riskImpactMap', riskId],
    queryFn: () => fetchImpactMap(riskId),
    enabled: riskId != null,
    staleTime: 5 * 60 * 1000,
  });


  const mappings = data?.mappings || [];
  const isLoading_ = isLoading;

  if (isLoading_) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Network className="h-5 w-5 text-primary" /> Supply Chain Impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <LoaderCircle className="h-4 w-4 animate-spin" /> Mapping potential supply-chain impact...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Network className="h-5 w-5 text-primary" /> Supply Chain Impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
            <div className="flex items-start gap-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Impact mapping unavailable</p>
                <button type="button" onClick={() => refetch()} className="mt-2 underline underline-offset-2">
                  Retry
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data?.company_available) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Network className="h-5 w-5 text-primary" /> Supply Chain Impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Complete your company profile to see company-specific impact mapping.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Network className="h-5 w-5 text-primary" /> Supply Chain Impact
        </CardTitle>
        <CardDescription>
          Potential supply-chain areas affected by this risk, based on configured company dependencies.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-foreground">{data.summary}</p>

        {mappings.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No company-specific impact was identified for this risk.
          </p>
        ) : (
          <ul className="space-y-3">
            {mappings.map((item) => (
              <li
                key={`${item.category}-${item.dependency}`}
                className="rounded-xl border border-border/60 bg-muted/10 p-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={RELEVANCE_VARIANTS[item.relevance] || 'outline'} className="text-[10px] uppercase tracking-wide">
                    {item.dependency}
                  </Badge>
                  <Badge variant="secondary" className="text-[10px] uppercase tracking-wide">
                    Potential {item.relevance} exposure
                  </Badge>
                </div>

                <FlowArrow />
                <Stage label="Supply-chain areas" values={item.supply_chain_areas} />

                <FlowArrow />
                <Stage label="Potential impacts" values={item.potential_impacts} />

                <FlowArrow />
                <Stage label="Information needed to confirm" values={item.verification_checks} />
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-start gap-2 border-t border-border/60 pt-3 text-xs text-muted-foreground">
          <ShieldQuestion className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p>
            Impact mapping identifies potential exposure areas from available intelligence and
            configured dependencies. It does not quantify actual business impact.
            {(data.data_limitations || []).map((item) => (
              <span key={item} className="block">- {item}</span>
            ))}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
