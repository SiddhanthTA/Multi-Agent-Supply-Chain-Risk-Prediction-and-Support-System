import { Badge } from '@/components/ui/Badge';
import {
  COMPANY_RELEVANCE_LABELS,
  companyRelevanceLevel,
  companyRelevanceSentence,
} from '@/lib/riskInvestigation';

const LEVEL_VARIANTS = {
  direct: 'default',
  indirect: 'secondary',
  no_identified_relevance: 'outline',
};

export function CompanyRelevanceBadge({ row, showLevel = true }) {
  if (!row) return null;
  const level = companyRelevanceLevel(row);
  return (
    <Badge variant={LEVEL_VARIANTS[level] || 'outline'} className="text-[10px] uppercase tracking-wide">
      {COMPANY_RELEVANCE_LABELS[level] || level}
      {showLevel && level !== 'no_identified_relevance' ? ` · ${level}` : ''}
    </Badge>
  );
}

/**
 * User-facing relevance explanation.
 *
 * Deliberately does not expose matcher internals ("configured dependency",
 * "matched terms", categories). It renders one grounded sentence built from
 * the relevance level and the de-duplicated matched values.
 */
export function CompanyRelevanceMatches({ row, className = '' }) {
  if (!row) return null;
  return (
    <p className={`text-xs leading-relaxed text-muted-foreground ${className}`}>
      {companyRelevanceSentence(row)}
    </p>
  );
}

export function CompanyRelevanceContext({ row, title = 'Company Relevance' }) {
  if (!row) return null;
  const level = companyRelevanceLevel(row);
  return (
    <div className="rounded-xl border border-border/60 bg-muted/10 p-4 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {title}
        </h3>
        <CompanyRelevanceBadge row={row} />
      </div>
      <CompanyRelevanceMatches row={row} />
      {level === 'no_identified_relevance' && (
        <p className="text-xs text-muted-foreground">
          This does not mean the event cannot affect the company. It means no configured
          dependency matches it.
        </p>
      )}
    </div>
  );
}
