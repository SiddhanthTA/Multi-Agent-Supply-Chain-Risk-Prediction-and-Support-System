import { useReducer } from 'react';
import { AlertTriangle, Bot, LoaderCircle, RefreshCw } from 'lucide-react';
import api from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  INVESTIGATION_SECTION_LABELS,
  INVESTIGATION_TYPE_LABELS,
  initialInvestigationState,
  investigationErrorMessage,
  investigationReducer,
} from '@/lib/riskInvestigation';

const SECTION_ORDER = Object.keys(INVESTIGATION_SECTION_LABELS);

export default function RiskInvestigationPanel({ riskId, buttonLabel = 'Investigate Risk' }) {
  const [{ investigation, isLoading, error }, dispatch] = useReducer(
    investigationReducer,
    initialInvestigationState,
  );

  if (riskId == null) {
    return (
      <div className="rounded-xl border border-dashed border-border/60 bg-muted/10 p-4 text-sm text-muted-foreground">
        No associated risk is available to investigate.
      </div>
    );
  }

  const runInvestigation = async () => {
    dispatch({ type: 'start' });
    try {
      const response = await api.post(`/investigations/risk/${riskId}`);
      dispatch({ type: 'success', investigation: response.data });
    } catch (requestError) {
      dispatch({ type: 'error', error: investigationErrorMessage(requestError) });
    }
  };

  return (
    <div className="space-y-4">
      <Button className="w-full" onClick={runInvestigation} disabled={isLoading}>
        {isLoading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Bot className="mr-2 h-4 w-4" />}
        {isLoading ? 'Investigating…' : buttonLabel}
      </Button>

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
          <div className="flex items-start gap-2 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-medium">Investigation unavailable</p>
              <p className="mt-1">{error}</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={runInvestigation} disabled={isLoading}>
                <RefreshCw className="mr-2 h-3 w-3" /> Retry
              </Button>
            </div>
          </div>
        </div>
      )}

      {investigation && (
        <Card className="border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bot className="h-5 w-5 text-primary" /> AI Risk Investigation
            </CardTitle>
            <CardDescription>
              Generated from {investigation.evidence?.length || 0} bounded platform evidence records. Decision support only.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {SECTION_ORDER.map((key) => {
              const statements = investigation.sections?.[key] || [];
              return (
                <section key={key} aria-labelledby={`investigation-${key}`}>
                  <h4 id={`investigation-${key}`} className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    {INVESTIGATION_SECTION_LABELS[key]}
                  </h4>
                  {statements.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No related platform evidence was found.</p>
                  ) : (
                    <ul className="space-y-3">
                      {statements.map((statement, index) => (
                        <li key={`${key}-${index}`} className="rounded-lg border border-border/60 bg-muted/10 p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
                              {INVESTIGATION_TYPE_LABELS[statement.statement_type] || statement.statement_type}
                            </Badge>
                            {statement.evidence_refs?.map((ref) => (
                              <Badge key={ref} variant="secondary" className="text-[10px]">{ref}</Badge>
                            ))}
                          </div>
                          <p className="text-sm leading-relaxed text-foreground">{statement.text}</p>
                          {statement.evidence_quotes?.map((quote) => (
                            <blockquote key={quote} className="mt-2 border-l-2 border-primary/40 pl-3 text-xs italic text-muted-foreground">
                              “{quote}”
                            </blockquote>
                          ))}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              );
            })}
            {investigation.warnings?.map((warning) => (
              <p key={warning} className="border-t border-border/60 pt-3 text-xs text-muted-foreground">{warning}</p>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
