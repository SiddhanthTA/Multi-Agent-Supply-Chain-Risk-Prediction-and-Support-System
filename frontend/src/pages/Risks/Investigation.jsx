import { useEffect, useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  InvalidRiskRoute,
  PageEmpty,
  PageError,
  PageLoading,
  RiskPageHeader,
  RiskTargetBanner,
} from '@/components/risk/RiskPageShell';
import {
  fetchInvestigation,
  fetchRiskContext,
  generateInvestigation,
  isNotGenerated,
  useRiskIdParam,
} from '@/lib/riskReports';

// Only these three sections are user-facing. Supporting Evidence and Related
// Intelligence stay internal: evidence identifiers are an implementation
// detail, and correlation now has its own page.
const SECTION_ORDER = [
  { key: 'investigation_summary', label: 'Investigation Summary' },
  { key: 'why_this_matters', label: 'Why This Matters' },
  { key: 'what_to_investigate_next', label: 'What To Investigate Next', steps: true },
];

/**
 * AI Risk Investigation for one risk.
 *
 * The report is generated once and then stored by the backend, so reopening
 * this page loads the saved report immediately instead of re-running the
 * agent.
 */
export default function RiskInvestigationPage() {
  // The URL is the source of truth for the current risk.
  const riskId = useRiskIdParam();
  const navigate = useNavigate();
  const started = useRef(false);

  // No request is issued until a valid id is present.
  const enabled = riskId != null;

  const context = useQuery({
    queryKey: ['riskContext', riskId],
    queryFn: () => fetchRiskContext(riskId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  // A 404 just means "not investigated yet", which is a normal first-run
  // state rather than an error.
  const report = useQuery({
    queryKey: ['riskInvestigation', riskId],
    queryFn: () => fetchInvestigation(riskId),
    retry: false,
    enabled,
  });

  const generate = useMutation({
    mutationFn: () => generateInvestigation(riskId),
    onSuccess: () => report.refetch(),
  });

  useEffect(() => {
    if (!enabled || started.current || report.isLoading) return;
    if (!isNotGenerated(report.error)) return;
    started.current = true;
    generate.mutate();
  }, [enabled, report.isLoading, report.error, generate]);

  const investigation = report.data;
  const target = context.data;
  const generating = generate.isPending;

  if (!enabled) return <InvalidRiskRoute />;

  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <RiskPageHeader
        title="AI Risk Investigation"
        subtitle="Structured investigation of the selected supply-chain risk."
        onBack={() => navigate(`/risks/${riskId}`)}
      />
      <RiskTargetBanner risk={target?.risk} event={target?.event} />
      <InvestigationBody
        investigation={investigation}
        generating={generating}
        reportLoading={report.isLoading}
        reportError={report.isError && !isNotGenerated(report.error)}
        onRetryReport={() => report.refetch()}
        onRetryGenerate={() => {
          started.current = true;
          generate.mutate();
        }}
        onOpenResponsePlan={() => navigate(`/risks/${riskId}/response-plan`)}
      />
    </div>
  );
}

function InvestigationBody({
  investigation,
  generating,
  reportLoading,
  reportError,
  onRetryReport,
  onRetryGenerate,
  onOpenResponsePlan,
}) {
  if (generating || reportLoading) return <PageLoading message="Investigating this risk..." />;

  if (reportError) {
    return (
      <PageError
        message="Unable to load this investigation."
        onRetry={onRetryReport}
      />
    );
  }

  if (!investigation) {
    return (
      <div className="space-y-3">
        <PageEmpty>No investigation has been generated for this risk yet.</PageEmpty>
        <div className="flex justify-center">
          <Button onClick={onRetryGenerate}>
            <Sparkles className="mr-2 h-4 w-4" />
            Run Investigation
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      <article className="rounded-xl border border-border/60 bg-card p-6">
        {SECTION_ORDER.map((section, sectionIndex) => {
          const statements = investigation.sections?.[section.key] || [];
          if (!statements.length) return null;
          return (
            <section
              key={section.key}
              className={sectionIndex === 0 ? '' : 'mt-6 border-t border-border/60 pt-6'}
            >
              <h2 className="ss-eyebrow">{section.label}</h2>
              {section.steps ? (
                <ol className="mt-3 space-y-2.5">
                  {statements.map((statement, index) => (
                    <li key={index} className="flex gap-3">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/10 text-[11px] font-semibold text-primary">
                        {index + 1}
                      </span>
                      <p className="text-sm leading-relaxed text-foreground">{statement.text}</p>
                    </li>
                  ))}
                </ol>
              ) : (
                <div className="mt-3 space-y-2.5">
                  {statements.map((statement, index) => (
                    <p key={index} className="text-sm leading-relaxed text-foreground">
                      {statement.text}
                    </p>
                  ))}
                </div>
              )}
            </section>
          );
        })}
      </article>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-xs leading-relaxed text-muted-foreground">
          AI investigation provides decision support based on available SupplySentry intelligence. It does not
          quantify actual business exposure.
        </p>
        <Button variant="outline" size="sm" onClick={onOpenResponsePlan}>
          <ClipboardList className="mr-2 h-4 w-4" />
          Response Plan
        </Button>
      </div>
    </>
  );
}
