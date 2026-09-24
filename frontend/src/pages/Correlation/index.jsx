import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';
import { Network, MapPin, AlertTriangle, Search, X, Globe, RefreshCw, BarChart3, Target, Crosshair } from 'lucide-react';

const fetchCorrelation = async () => {
  const response = await api.get('/correlation/summary');
  return response.data?.results || [];
};

// Simple deterministic coordinates fallback map for major supply chain hubs
const getDeterministicPosition = (location, index) => {
  const locStr = (location || '').toLowerCase();
  // Rough visual percentages (x: left-to-right, y: top-to-bottom)
  if (locStr.includes('frankfurt') || locStr.includes('germany') || locStr.includes('europe')) return { x: '52%', y: '35%' };
  if (locStr.includes('london') || locStr.includes('uk')) return { x: '48%', y: '32%' };
  if (locStr.includes('são paulo') || locStr.includes('brazil') || locStr.includes('saopaulo')) return { x: '35%', y: '75%' };
  if (locStr.includes('mumbai') || locStr.includes('india')) return { x: '70%', y: '48%' };
  if (locStr.includes('new york') || locStr.includes('usa') || locStr.includes('america')) return { x: '25%', y: '38%' };
  if (locStr.includes('tokyo') || locStr.includes('japan')) return { x: '88%', y: '38%' };
  if (locStr.includes('shanghai') || locStr.includes('china')) return { x: '82%', y: '42%' };
  if (locStr.includes('singapore')) return { x: '78%', y: '60%' };
  if (locStr.includes('sydney') || locStr.includes('australia')) return { x: '90%', y: '80%' };
  if (locStr.includes('dubai') || locStr.includes('uae')) return { x: '62%', y: '45%' };
  if (locStr.includes('global') || locStr.includes('unknown')) return { x: '15%', y: '85%' };
  
  // Pseudo-random but deterministic placement based on index if location doesn't match
  const pseudoRandX = 20 + ((index * 37) % 60); // Spread between 20% and 80%
  const pseudoRandY = 20 + ((index * 23) % 60); // Spread between 20% and 80%
  
  return { x: `${pseudoRandX}%`, y: `${pseudoRandY}%` };
};

export default function CorrelationIntelligence() {
  const { data: correlations = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['correlationSummary'],
    queryFn: fetchCorrelation,
  });

  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Extract unique severities
  const severities = useMemo(() => {
    return [...new Set(correlations.map(c => c.overall_risk).filter(Boolean))];
  }, [correlations]);

  const kpis = useMemo(() => {
    if (!correlations.length) return null;
    let totalEvents = 0;
    let highCriticalZones = 0;
    let totalScore = 0;
    let scoredZones = 0;

    correlations.forEach(c => {
      if (c.active_events != null) totalEvents += Number(c.active_events);
      const risk = c.overall_risk?.toLowerCase();
      if (risk === 'high' || risk === 'critical') highCriticalZones++;
      if (c.overall_score != null) {
        totalScore += Number(c.overall_score);
        scoredZones++;
      }
    });

    return {
      hubs: correlations.length,
      events: totalEvents,
      highCriticalZones,
      avgScore: scoredZones > 0 ? totalScore / scoredZones : 0
    };
  }, [correlations]);

  // Derived Priority Signals (Top 3)
  const prioritySignals = useMemo(() => {
    const priorityRank = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
    return [...correlations]
      .sort((a, b) => {
        const pA = priorityRank[a.overall_risk?.toLowerCase()] || 0;
        const pB = priorityRank[b.overall_risk?.toLowerCase()] || 0;
        if (pA !== pB) return pB - pA;
        return (Number(b.overall_score) || 0) - (Number(a.overall_score) || 0);
      })
      .slice(0, 3);
  }, [correlations]);

  const filteredCorrelations = useMemo(() => {
    return correlations.filter(c => {
      const matchesSearch = search === '' || 
        c.location?.toLowerCase().includes(search.toLowerCase());
      const matchesSeverity = severityFilter === '' || c.overall_risk === severityFilter;
      return matchesSearch && matchesSeverity;
    }).sort((a, b) => (Number(b.overall_score) || 0) - (Number(a.overall_score) || 0));
  }, [correlations, search, severityFilter]);

  const handleClearFilters = () => {
    setSearch('');
    setSeverityFilter('');
  };

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <Network className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load correlation data</h2>
        <p className="text-muted-foreground mt-2 max-w-md">{error.message}</p>
        <Button variant="outline" className="mt-6" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Network className="h-8 w-8 text-primary" />
            Correlation Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">Identify geographic clusters, overlapping disruptions, and connected supply chain risks.</p>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Risk Hubs / Clusters</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <Network className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.hubs || 0}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Correlated Risk Events</h3>
            <div className="p-2 bg-amber-500/10 rounded-full">
              <Target className="h-4 w-4 text-amber-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.events || 0}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">High/Critical Zones</h3>
            <div className="p-2 bg-destructive/10 rounded-full">
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-destructive">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.highCriticalZones || 0}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Avg Regional Score</h3>
            <div className="p-2 bg-blue-500/10 rounded-full">
              <BarChart3 className="h-4 w-4 text-blue-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-foreground">
            {isLoading ? <Skeleton className="h-8 w-16" /> : `${(kpis?.avgScore || 0).toFixed(1)}%`}
          </div>
        </Card>
      </div>

      {/* Visual Correlation Analytics */}
      <div className="grid md:grid-cols-12 gap-6">
        {/* Geospatial Map Area */}
        <Card className="overflow-hidden md:col-span-8 flex flex-col border-border/50 shadow-sm">
          <CardHeader className="bg-muted/10 border-b border-border/50 pb-4">
            <CardTitle className="text-lg flex items-center gap-2"><Globe className="h-5 w-5 text-muted-foreground" /> Global Risk Correlation Map</CardTitle>
            <CardDescription>Geographic visualization of concentrated supply chain disruptions.</CardDescription>
          </CardHeader>
          <CardContent className="p-0 flex-1 relative">
            <div className="min-h-[400px] h-full w-full bg-[#0a0a0f] relative overflow-hidden flex items-center justify-center">
              {/* Grid Background */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080801a_1px,transparent_1px),linear-gradient(to_bottom,#8080801a_1px,transparent_1px)] bg-[size:32px_32px]"></div>
              
              {/* Soft vignette */}
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(10,10,15,0.8)_100%)] pointer-events-none z-0"></div>

              {isLoading ? (
                <div className="absolute inset-0 flex items-center justify-center z-10"><Skeleton className="h-full w-full opacity-10" /></div>
              ) : correlations.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center z-10">
                  <div className="text-center p-8 bg-background/80 rounded-lg shadow-sm border border-border/50 backdrop-blur-sm">
                    <Globe className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-semibold text-foreground">Geospatial correlation data unavailable</h3>
                    <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                      Valid regional coordinates are not currently provided by the backend API.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="absolute inset-0 z-10">
                  {correlations.map((cluster, i) => {
                    const pos = getDeterministicPosition(cluster.location, i);
                    const score = Number(cluster.overall_score) || 0;
                    // Scale node size from 20px to ~80px based on score
                    const size = Math.max(16, (score / 100) * 60 + 16);
                    const isHigh = score >= 75 || cluster.overall_risk?.toLowerCase() === 'critical';
                    const isMedium = score >= 50 && score < 75;
                    
                    return (
                      <div 
                        key={i} 
                        className="absolute group z-20"
                        style={{ left: pos.x, top: pos.y, transform: 'translate(-50%, -50%)' }}
                      >
                        {/* Glowing Node Component */}
                        <div 
                          className={`rounded-full flex items-center justify-center cursor-pointer transition-transform duration-300 group-hover:scale-125
                            ${isHigh ? 'bg-destructive/90 border border-destructive/50' : 
                              isMedium ? 'bg-amber-500/90 border border-amber-500/50' : 
                              'bg-blue-500/90 border border-blue-500/50'}
                          `}
                          style={{ 
                            width: `${size}px`, 
                            height: `${size}px`,
                            boxShadow: `0 0 ${size * 0.8}px ${isHigh ? 'rgba(239,68,68,0.7)' : isMedium ? 'rgba(245,158,11,0.7)' : 'rgba(59,130,246,0.7)'}`
                          }}
                        >
                          <div className="w-1.5 h-1.5 rounded-full bg-white opacity-90 animate-pulse" />
                        </div>
                        
                        {/* Interactive Tooltip */}
                        <div className="absolute opacity-0 group-hover:opacity-100 transition-opacity bg-card/95 border border-border/50 text-card-foreground text-xs p-3 rounded shadow-xl pointer-events-none z-50 w-52 -top-3 left-1/2 -translate-x-1/2 -translate-y-full backdrop-blur-sm">
                          <div className="font-bold mb-1.5 border-b border-border/50 pb-1.5 flex justify-between items-center">
                            <span className="truncate pr-2">{cluster.location || 'Unknown Hub'}</span>
                            <span className={`font-mono ${isHigh ? 'text-destructive' : isMedium ? 'text-amber-500' : 'text-blue-500'}`}>{score.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between mt-1 text-muted-foreground">
                            <span>Active Triggers:</span>
                            <span className="font-semibold text-foreground">{cluster.active_events || 0}</span>
                          </div>
                          <div className="flex justify-between mt-1 text-muted-foreground">
                            <span>Severity Level:</span>
                            <span className="font-semibold capitalize text-foreground">{cluster.overall_risk || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              
              {/* Map Legend */}
              <div className="absolute bottom-4 left-4 bg-card/80 backdrop-blur-md border border-border/50 rounded-lg p-2.5 text-[10px] flex gap-3.5 text-muted-foreground shadow-sm z-10">
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-destructive shadow-[0_0_6px_rgba(239,68,68,0.8)]"></div> High Risk</div>
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.8)]"></div> Medium Risk</div>
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.8)]"></div> Low Risk</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Regional Distribution Panel */}
        <Card className="md:col-span-4 flex flex-col border-border/50 shadow-sm">
          <CardHeader className="bg-muted/10 border-b border-border/50 pb-4">
            <CardTitle className="text-lg flex items-center gap-2"><BarChart3 className="h-5 w-5 text-muted-foreground" /> Regional Distribution</CardTitle>
            <CardDescription>Risk concentration by designated supply chain hubs.</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex-1 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
            {isLoading ? (
              <div className="space-y-5">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between"><Skeleton className="h-3 w-20" /><Skeleton className="h-3 w-8" /></div>
                    <Skeleton className="h-2 w-full" />
                  </div>
                ))}
              </div>
            ) : correlations.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Globe className="mx-auto h-8 w-8 opacity-20 mb-3" />
                <p className="text-sm">No regional data available.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {[...correlations].sort((a,b) => (Number(b.overall_score)||0) - (Number(a.overall_score)||0)).map((cluster, idx) => {
                  const score = Number(cluster.overall_score) || 0;
                  const isHigh = score >= 75 || cluster.overall_risk?.toLowerCase() === 'critical';
                  const isMedium = score >= 50 && score < 75;
                  
                  return (
                    <div key={idx} className="space-y-1.5 group cursor-default">
                      <div className="flex justify-between text-xs items-end">
                        <span className="font-medium truncate pr-2 group-hover:text-primary transition-colors" title={cluster.location}>{cluster.location || 'Unknown Region'}</span>
                        <span className={`font-mono font-semibold ${isHigh ? 'text-destructive' : isMedium ? 'text-amber-500' : 'text-blue-500'}`}>{score.toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-500 ${isHigh ? 'bg-destructive' : isMedium ? 'bg-amber-500' : 'bg-blue-500'}`} 
                          style={{ width: `${Math.min(100, Math.max(0, score))}%` }} 
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Priority Correlation Signals */}
      {!isLoading && prioritySignals.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold tracking-tight text-muted-foreground uppercase">Critical Risk Clusters</h3>
          <div className="grid gap-4 md:grid-cols-3">
            {prioritySignals.map((signal, idx) => (
              <Card key={idx} className={`p-4 flex flex-col justify-between bg-muted/10 border-border/60 ${idx === 0 ? 'border-destructive/30 bg-destructive/5' : ''}`}>
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <Crosshair className="h-3.5 w-3.5" /> Cluster Signal
                  </div>
                  <SeverityBadge severity={signal.overall_risk} />
                </div>
                <div className="font-medium text-lg mb-2 truncate" title={signal.location || 'Unknown Location'}>
                  {signal.location || 'Unknown Location'}
                </div>
                <div className="text-xs text-muted-foreground mt-auto flex justify-between items-center">
                  <span><strong className="text-foreground">{signal.active_events || 0}</strong> active triggers</span>
                  <span className="font-semibold text-foreground">{(Number(signal.overall_score) || 0).toFixed(1)}% Score</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Filter Portfolio */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-lg">Filter Portfolio</CardTitle>
          <CardDescription>Narrow down regional hubs by location or aggregated severity.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-6">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Location</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search regions..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Aggregated Severity</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All Severities</option>
                {severities.map(sev => <option key={sev} value={sev}>{sev}</option>)}
              </select>
            </div>
            
            <div className="md:col-span-2 flex justify-end">
              <Button 
                variant="ghost" 
                className="h-10 px-3 w-full border border-transparent hover:bg-muted/50 text-muted-foreground disabled:opacity-50" 
                onClick={handleClearFilters}
                disabled={!(search || severityFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Correlation Directory */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Clusters...' : `Regional Correlation Hubs (${filteredCorrelations.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredCorrelations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Network className="h-6 w-6 text-muted-foreground opacity-50" />
              </div>
              <h3 className="text-lg font-semibold">No active risk clusters</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                No regional hubs matched your filters.
              </p>
              <Button variant="outline" className="mt-4" onClick={handleClearFilters}>
                Clear all filters
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-transparent hover:bg-transparent">
                  <TableHead className="pl-6 w-[30%]">Location Hub</TableHead>
                  <TableHead className="w-[15%]">Active Triggers</TableHead>
                  <TableHead className="w-[30%]">Correlated Categories</TableHead>
                  <TableHead className="w-[15%]">Aggregated Score</TableHead>
                  <TableHead className="pr-6 text-right w-[10%]">Overall Risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCorrelations.map((cluster, idx) => {
                  const scorePct = Number(cluster.overall_score) || 0;
                  const categories = cluster.categories || [];
                  return (
                    <TableRow key={idx} className="group">
                      <TableCell className="pl-6 font-medium">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                          <span className="truncate group-hover:text-primary transition-colors">{cluster.location || 'Unknown Location'}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="bg-muted text-muted-foreground font-mono">
                          {cluster.active_events || 0} Events
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1.5">
                          {categories.slice(0, 3).map((cat, i) => (
                            <Badge key={i} variant="outline" className="text-[10px] bg-background/50 text-muted-foreground capitalize">
                              {cat}
                            </Badge>
                          ))}
                          {categories.length > 3 && (
                            <Badge variant="outline" className="text-[10px] bg-background/50 text-muted-foreground">
                              +{categories.length - 3} more
                            </Badge>
                          )}
                          {categories.length === 0 && (
                            <span className="text-xs text-muted-foreground">Uncategorized</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1.5 mt-1">
                          <span className="text-sm font-medium">{scorePct.toFixed(1)}%</span>
                          <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${scorePct >= 75 ? 'bg-destructive' : scorePct >= 50 ? 'bg-amber-500' : 'bg-green-500'}`} 
                              style={{ width: `${Math.min(100, Math.max(0, scorePct))}%` }} 
                            />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="pr-6 text-right">
                        <SeverityBadge severity={cluster.overall_risk} />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline" className="whitespace-nowrap">Unknown</Badge>;
  const lower = severity.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="high" className="whitespace-nowrap">{severity}</Badge>;
  if (lower === 'medium') return <Badge variant="medium" className="whitespace-nowrap">{severity}</Badge>;
  if (lower === 'low') return <Badge variant="low" className="whitespace-nowrap">{severity}</Badge>;
  return <Badge variant="outline" className="whitespace-nowrap">{severity}</Badge>;
}
