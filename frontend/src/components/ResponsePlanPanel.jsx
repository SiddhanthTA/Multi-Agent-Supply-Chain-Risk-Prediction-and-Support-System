import { useState } from 'react';
import { AlertTriangle, ClipboardList, LoaderCircle } from 'lucide-react';
import api from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  RESPONSE_PLAN_SECTION_LABELS,
  responsePlanErrorMessage,
} from '@/lib/riskInvestigation';

const PREPARING_LABEL = 'Preparing response options...';

function Bullets({ items, className = 'text-sm text-foreground' }) {
  return (
    <ul className={`space-y-1.5 ${className}`}>
      {(items || []).map((item) => (
        <li key={item} className="flex gap-2">
          <span aria-hidden="true" className="text-primary">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function SectionHeading({ children }) {
  return (
    <h4 className="mb-1.5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
      {children}
    </h4>
  );
}

/**
 * Runtime response-planning panel.
 *
 * The backend builds a fresh plan from the selected risk, event, company
 * dependencies, and existing platform recommendation. It is enabled only
 * after an Agent 1 investigation exists.
 */
export default function ResponsePlanPanel({ riskId, investigationReady }) {
  const [plan, setPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (riskId == null) return null;

  const generatePlan = async () => {
    setIsLoading(true);
    setError('');
    setPlan(null);
    try {
      const response = await api.post(`/investigations/risk/${riskId}/response-plan`);
      setPlan(response.data);
    } catch (requestError) {
      setError(responsePlanErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  if (!investigationReady) {
    return (
      <div className="rounded-xl border border-dashed border-border/60 bg-muted/10 p-4 text-sm text-muted-foreground">
        Investigate the risk first to generate a response plan.
      </div>
    );
  }


  return (
    <Card className="border-green-500/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <ClipboardList className="h-5 w-5 text-green-600" /> Generated Response Plan
        </CardTitle>
        <CardDescription>
          Generated from this risk's event, assessment, company context, and available platform intelligence.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button className="w-full" onClick={generatePlan} disabled={isLoading}>
          {isLoading ? (
            <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <ClipboardList className="mr-2 h-4 w-4" />
          )}
          {isLoading
            ? PREPARING_LABEL
            : plan
              ? 'Regenerate Response Plan'
              : 'Generate Response Plan'}
        </Button>

        {error && (
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
            <div className="flex items-start gap-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Response plan unavailable</p>
                <p className="mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {plan && (
          <div className="space-y-5">
            {plan.company_relevance && plan.company_name && (
              <p className="text-xs text-muted-foreground">
                {plan.company_relevance === 'no_identified_relevance'
                  ? `${plan.company_name}: no identified company dependency match`
                  : `${plan.company_name}: ${plan.company_relevance} relevance · ${(plan.matched_dependencies || []).join(' · ')}`}
              </p>
            )}

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.response_objective}</SectionHeading>
              <p className="text-sm leading-relaxed text-foreground">{plan.response_objective}</p>
            </div>

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.immediate_checks}</SectionHeading>
              <Bullets items={plan.immediate_checks} />
            </div>

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.response_options}</SectionHeading>
              <p className="mb-2 text-xs text-muted-foreground">
                These are options for human review, not commands, and none is ranked above another.
              </p>
              <div className="space-y-3">
                {(plan.response_options || []).map((option) => (
                  <div key={option.name} className="rounded-lg border border-border/60 bg-muted/10 p-3">
                    <p className="text-sm font-semibold">{option.name}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{option.why}</p>
                    {(option.what_to_check || []).length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                        {option.what_to_check.map((item) => (
                          <li key={item}>What to check: {item}</li>
                        ))}
                      </ul>
                    )}
                    {(option.information_required || []).length > 0 && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Information required: {(option.information_required || []).join('; ')}.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.information_required}</SectionHeading>
              <Bullets items={plan.information_required} />
            </div>

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.escalation_conditions}</SectionHeading>
              <Bullets items={plan.escalation_conditions} />
            </div>

            <div>
              <SectionHeading>{RESPONSE_PLAN_SECTION_LABELS.responsible_areas}</SectionHeading>
              <div className="flex flex-wrap gap-2">
                {(plan.responsible_areas || []).map((area) => (
                  <Badge key={area} variant="secondary">{area}</Badge>
                ))}
              </div>
            </div>

            {plan.platform_recommendation && (
              <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-green-600 dark:text-green-400">
                  Existing SupplySentry recommendation
                </p>
                <p className="mt-1 text-sm font-medium text-foreground">
                  {plan.platform_recommendation.title}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {plan.platform_recommendation.text}
                </p>
              </div>
            )}

            <div className="space-y-1 border-t border-border/60 pt-3 text-xs text-muted-foreground">
              {(plan.notes || []).map((note) => <p key={note}>{note}</p>)}
              <p>Decision support only. Review available evidence before taking action.</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

