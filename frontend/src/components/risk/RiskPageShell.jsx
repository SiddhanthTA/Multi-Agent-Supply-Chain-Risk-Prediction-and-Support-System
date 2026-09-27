import { AlertTriangle, ArrowLeft, LoaderCircle, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

/** Consistent header for every risk-scoped page. */
export function RiskPageHeader({ title, subtitle, onBack }) {
  return (
    <header className="border-b border-border/70 pb-4">
      <div className="flex items-start gap-3">
        <Button variant="outline" size="icon" onClick={onBack} title="Back to risk detail">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
        </div>
      </div>
    </header>
  );
}

/** Identifies the risk every sub-page is about. */
export function RiskTargetBanner({ risk, event, relevanceLabel }) {
  if (!risk) return null;
  return (
    <div className="rounded-xl border border-border/60 bg-muted/10 p-4">
      <p className="ss-eyebrow">Target risk</p>
      <p className="mt-1.5 text-sm font-medium leading-snug text-foreground">
        {event?.title || risk.risk_name || 'Risk detail'}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {risk.severity && <SeverityBadge severity={risk.severity} />}
        {(risk.risk_type || risk.risk_name) && (
          <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
            {risk.risk_type || risk.risk_name}
          </Badge>
        )}
        {event?.location && (
          <span className="text-xs text-muted-foreground">{event.location}</span>
        )}
        {relevanceLabel && (
          <Badge variant="secondary" className="text-[10px] uppercase tracking-wide">
            {relevanceLabel}
          </Badge>
        )}
      </div>
    </div>
  );
}

export function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline">Unknown</Badge>;
  const normalized = String(severity).toLowerCase();
  if (normalized === 'critical') return <Badge variant="critical">Critical</Badge>;
  if (normalized === 'high') return <Badge variant="high">High</Badge>;
  if (normalized === 'medium') return <Badge variant="medium">Medium</Badge>;
  if (normalized === 'low') return <Badge variant="low">Low</Badge>;
  return <Badge variant="outline">{severity}</Badge>;
}

/**
 * Rendered when a risk-scoped URL has no usable id. No request is issued in
 * this state, so the API can never be called with "undefined".
 */
export function InvalidRiskRoute() {
  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <RiskPageHeader
        title="Risk not specified"
        subtitle="This page needs a valid risk in the URL."
        onBack={() => window.history.back()}
      />
      <PageEmpty>This link does not contain a valid risk id. Return to the risk list and open a risk.</PageEmpty>
    </div>
  );
}

/** One loading style shared by every risk page. */
export function PageLoading({ message }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-sm text-muted-foreground">
      <LoaderCircle className="h-6 w-6 animate-spin text-primary" />
      <p>{message}</p>
    </div>
  );
}

/** One error style shared by every risk page. */
export function PageError({ message, onRetry, retryLabel = 'Retry' }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4" role="alert">
      <div className="flex items-start gap-2 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <div>
          <p className="font-medium">{message}</p>
          {onRetry && (
            <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              {retryLabel}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

/** One empty style shared by every risk page. */
export function PageEmpty({ children }) {
  return (
    <div className="rounded-xl border border-dashed border-border/60 px-6 py-12 text-center text-sm text-muted-foreground">
      {children}
    </div>
  );
}

/** Small muted closing note used for every disclaimer on these pages. */
export function PageFootnote({ children }) {
  return (
    <p className="border-t border-border/60 pt-3 text-xs leading-relaxed text-muted-foreground">
      {children}
    </p>
  );
}
