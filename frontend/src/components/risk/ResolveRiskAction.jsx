import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  RESOLVE_RISK_TEXT,
  canShowResolveAction,
} from '@/lib/riskInvestigation';
import { resolveRisk, reopenRisk } from '@/lib/riskReports';

/**
 * Final step of the risk lifecycle: Active -> Investigate -> Response Plan ->
 * Resolve -> Resolved.
 *
 * The action only appears once the server confirms the risk is resolvable,
 * which requires both the investigation and the response plan to exist.
 * Resolution never deletes anything, so all historical intelligence remains.
 */
export default function ResolveRiskAction({ riskId, status, resolvable, onResolved, variant = 'default' }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const resolve = useMutation({
    mutationFn: () => resolveRisk(riskId),
    onSuccess: (data) => {
      setConfirming(false);
      // Active lists and counters must drop this risk immediately.
      queryClient.invalidateQueries({ queryKey: ['resolvedRisks'] });
      queryClient.invalidateQueries({ queryKey: ['currentRisks'] });
      queryClient.invalidateQueries({ queryKey: ['riskReportStatus', riskId] });
      queryClient.invalidateQueries({ queryKey: ['risk', riskId] });
      queryClient.invalidateQueries({ queryKey: ['risks'] });
      onResolved?.(data);
    },
  });

  if (!canShowResolveAction({ status, resolvable })) return null;
  if (confirming) {
    return (
      <div
        className="rounded-xl border border-border/60 bg-muted/20 p-4"
        role="dialog"
        aria-label={RESOLVE_RISK_TEXT.confirmTitle}
      >
        <p className="text-sm font-semibold text-foreground">
          {RESOLVE_RISK_TEXT.confirmTitle}
        </p>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
          {RESOLVE_RISK_TEXT.confirmBody}
        </p>
        {resolve.isError && (
          <p className="mt-2 text-sm text-destructive">
            {resolve.error?.response?.data?.detail || 'This risk could not be resolved.'}
          </p>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={resolve.isPending}
            onClick={() => resolve.mutate()}
          >
            <CheckCircle2 className="mr-2 h-4 w-4" />
            {RESOLVE_RISK_TEXT.confirmAction}
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={resolve.isPending}
            onClick={() => setConfirming(false)}
          >
            {RESOLVE_RISK_TEXT.cancel}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {variant === 'card' && (
        <p className="w-full text-xs text-muted-foreground">
          {RESOLVE_RISK_TEXT.readyHint}
        </p>
      )}
      <Button
        variant={variant === 'card' ? 'default' : 'outline'}
        size={variant === 'card' ? 'sm' : 'default'}
        onClick={() => setConfirming(true)}
      >
        <CheckCircle2 className="mr-2 h-4 w-4" />
        {RESOLVE_RISK_TEXT.action}
      </Button>
    </div>
  );
}

export function ReopenRiskButton({ riskId, small = true }) {
  const queryClient = useQueryClient();
  const reopen = useMutation({
    mutationFn: () => reopenRisk(riskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resolvedRisks'] });
      queryClient.invalidateQueries({ queryKey: ['currentRisks'] });
      queryClient.invalidateQueries({ queryKey: ['risk', riskId] });
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });

  return (
    <Button
      variant="outline"
      size={small ? 'sm' : 'default'}
      disabled={reopen.isPending}
      onClick={(event) => {
        event.stopPropagation();
        reopen.mutate();
      }}
    >
      <RotateCcw className="mr-2 h-4 w-4" />
      {RESOLVE_RISK_TEXT.reopen}
    </Button>
  );
}
