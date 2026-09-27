import RiskTrendsPanel from '@/components/RiskTrendsPanel';

export default function RiskTrends() {
  return (
    <div className="ss-page ss-enter space-y-4 pb-10">
      <header className="border-b border-border/70 pb-4">
        <p className="ss-eyebrow text-primary">Analytics</p>
        <h1 className="mt-1.5 text-2xl font-semibold tracking-tight">Risk Trends</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Historical risk activity from SupplySentry&apos;s monitored intelligence.
        </p>
      </header>
      <RiskTrendsPanel variant="page" />
    </div>
  );
}