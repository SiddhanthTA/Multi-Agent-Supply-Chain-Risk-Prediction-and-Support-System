import { useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ClipboardList } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  InvalidRiskRoute,
  PageEmpty,
  PageFootnote,
  PageLoading,
  RiskPageHeader,
  RiskTargetBanner,
} from '@/components/risk/RiskPageShell';
import {
  fetchResponsePlan,
  fetchRiskContext,
  fetchRiskResolution,
  generateResponsePlan,
  useRiskIdParam,
} from '@/lib/riskReports';
import ResolveRiskAction from '@/components/risk/ResolveRiskAction';
import {
  RESPONSE_PLAN_TEXT,
  claimGeneration,
  formatResponseOptionTitle,
  isCompleteResponsePlan,
  isGenerationInFlight,
  releaseGeneration,
  responsePlanErrorMessage,
  responsePlanRetry,
  shouldStartGeneration,
} from '@/lib/riskInvestigation';

function Bullets({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-2 space-y-1.5">
      {items.map((item) => (
        <li key={item} className="flex gap-2 text-sm text-muted-foreground">
          <span aria-hidden="true" className="text-primary">&bull;</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function Section({ title, children }) {
  if (!children) return null;
  return (
    <section className="border-t border-border/60 pt-5 first:border-t-0 first:pt-0">
      <h2 className="ss-eyebrow">{title}</h2>
      <div className="mt-2.5">{children}</div>
    </section>
  );
}


/**
 * Response Plan for one risk.
 *
 * The plan itself is deterministic decision-support content produced by the
 * existing backend service; nothing here claims a model generated it. It is
 * generated once, stored, and shown immediately on later visits.
 */
export default function RiskResponsePlanPage() {
  // The URL is the source of truth for the current risk.
  const riskId = useRiskIdParam();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const enabled = riskId != null;

  // Survives rerenders within this mount. The module-level in-flight set in
  // riskInvestigation additionally protects across remounts and StrictMode.
  const started = useRef(false);

  const context = useQuery({
    queryKey: ['riskContext', riskId],
    queryFn: () => fetchRiskContext(riskId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  const planQuery = useQuery({
    queryKey: ['riskResponsePlan', riskId],
    queryFn: () => fetchResponsePlan(riskId),
    // 404 is the expected "not generated yet" state and is never retried.
    retry: responsePlanRetry,
    // Nothing here should re-trigger a request behind the user's back.
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    enabled,
  });

  const generate = useMutation({
    mutationFn: () => generateResponsePlan(riskId),
    onSuccess: (data) => {
      // The POST body is the stored plan, so use it directly. Only fall back
      // to a single GET when the body was not a complete plan.
      if (isCompleteResponsePlan(data)) {
        queryClient.setQueryData(['riskResponsePlan', riskId], data);
        return;
      }
      queryClient.invalidateQueries({ queryKey: ['riskResponsePlan', riskId] });
    },
    onSettled: () => {
      releaseGeneration(riskId);
    },
  });

  const plan = planQuery.data;
  const target = context.data;
  // The mutation is the single reactive source of the generating state, so
  // there is no separate flag that could disagree with it.
  const generating = generate.isPending;
  const loadError = planQuery.isError ? planQuery.error : null;
  const generationError = generate.isError ? generate.error : null;

  // Resolution readiness comes from the backend for the signed-in user.
  const resolution = useQuery({
    queryKey: ['riskResolution', riskId],
    queryFn: () => fetchRiskResolution(riskId),
    staleTime: 30 * 1000,
    enabled,
  });

  // Start generation only once the GET has settled into a 404.
  useEffect(() => {
    if (
      !shouldStartGeneration({
        enabled,
        querySettled: planQuery.isFetched,
        plan,
        error: loadError,
        alreadyStarted: started.current,
        isPending: generate.isPending || isGenerationInFlight(riskId),
      })
    ) {
      return;
    }
    if (!claimGeneration(riskId)) return;
    started.current = true;
    generate.mutate();
  }, [enabled, planQuery.isFetched, plan, loadError, riskId, generate]);

  // Leaving the page mid-generation must not leave the risk locked.
  useEffect(
    () => () => {
      releaseGeneration(riskId);
    },
    [riskId],
  );

  if (!enabled) return <InvalidRiskRoute />;

  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <RiskPageHeader
        title={RESPONSE_PLAN_TEXT.title}
        subtitle={RESPONSE_PLAN_TEXT.subtitle}
        onBack={() => navigate(`/risks/${riskId}`)}
      />
      <RiskTargetBanner risk={target?.risk} event={target?.event} />

      {generationError ? (
        <PlanError
          message={responsePlanErrorMessage(generationError)}
          onRetry={() => {
            if (claimGeneration(riskId)) generate.mutate();
          }}
        />
      ) : generating ? (
        <PlanGenerating />
      ) : planQuery.isLoading ? (
        <PageLoading message={RESPONSE_PLAN_TEXT.loading} />
      ) : loadError ? (
        <PlanError
          message={responsePlanErrorMessage(loadError)}
          onRetry={() => planQuery.refetch()}
        />
      ) : !plan ? (
        <PageEmpty>{RESPONSE_PLAN_TEXT.empty}</PageEmpty>
      ) : (
        <>
          <ResponsePlanBody plan={plan} />
          {/* The response plan is the final step before a risk can be resolved. */}
          <ResolveRiskAction
            riskId={riskId}
            status={resolution?.status}
            resolvable={resolution?.resolvable}
            variant="card"
          />
        </>
      )}
    </div>
  );
}

/** Explicit, non-error state used only while the first plan is produced. */
function PlanGenerating() {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-8">
      <div className="flex flex-col items-center justify-center gap-2 text-center">
        <ClipboardList className="h-6 w-6 text-primary" />
        <p className="text-base font-semibold text-foreground">{RESPONSE_PLAN_TEXT.generatingTitle}</p>
        <p className="text-sm text-muted-foreground">{RESPONSE_PLAN_TEXT.generatingSubtitle}</p>
      </div>
    </div>
  );
}

/** Failure state with an explicit Retry that runs exactly one new POST. */
function PlanError({ message, onRetry }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-5" role="alert">
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
        <div>
          <p className="text-sm font-semibold text-destructive">{message}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
            {RESPONSE_PLAN_TEXT.retry}
          </Button>
        </div>
      </div>
    </div>
  );
}

function ResponsePlanBody({ plan }) {
  const options = plan.response_options || [];
  return (
    <>
      <article className="rounded-xl border border-border/60 bg-card p-6">
        <Section title="Response objective">
          <p className="text-sm leading-relaxed text-foreground">{plan.response_objective}</p>
        </Section>

        {options.length > 0 && (
          <Section title="Response options">
            <p className="mb-3 text-xs text-muted-foreground">
              Options for human review. None is ranked above another.
            </p>
            <div className="space-y-3">
              {options.map((option, index) => (
                <div key={option.name} className="rounded-xl border border-border/60 p-4">
                  <div className="flex items-start gap-3">
                    <span className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      {/* Title is bold and larger than everything beneath it. */}
                      <p className="text-base font-semibold leading-snug text-foreground">
                        {formatResponseOptionTitle(option.name, index)}
                      </p>
                      <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                        {option.why}
                      </p>
                      {option.what_to_check?.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium uppercase tracking-wide text-foreground">
                            Checks
                          </p>
                          <Bullets items={option.what_to_check} />
                        </div>
                      )}
                      {option.information_required?.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium uppercase tracking-wide text-foreground">
                            Information required
                          </p>
                          <Bullets items={option.information_required} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        <Section title="Immediate checks">
          <Bullets items={plan.immediate_checks} />
        </Section>

        <Section title="Information required">
          <Bullets items={plan.information_required} />
        </Section>

        <Section title="Escalation conditions">
          <Bullets items={plan.escalation_conditions} />
        </Section>

        {plan.responsible_areas?.length > 0 && (
          <Section title="Responsible areas">
            <div className="flex flex-wrap gap-2">
              {plan.responsible_areas.map((area) => (
                <Badge key={area} variant="secondary">
                  {area}
                </Badge>
              ))}
            </div>
          </Section>
        )}

        {plan.platform_recommendation && (
          <Section title="Existing SupplySentry recommendation">
            <p className="text-sm font-medium text-foreground">
              {plan.platform_recommendation.title}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              {plan.platform_recommendation.text}
            </p>
          </Section>
        )}
      </article>

      <PageFootnote>
        Decision-support template based on available SupplySentry intelligence. Options are provided for human
        review and do not constitute an automated business decision.
      </PageFootnote>
    </>
  );
}
