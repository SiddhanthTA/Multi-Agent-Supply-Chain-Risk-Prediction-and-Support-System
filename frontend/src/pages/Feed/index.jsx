import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Activity, AlertTriangle, BrainCircuit, Lightbulb, Rss, Search, X, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

const fetchFeedData = async () => {
  const [eventsRes, risksRes, predictionsRes, recsRes] = await Promise.all([
    api.get('/events/'),
    api.get('/risks/'),
    api.get('/predictions/'),
    api.get('/recommendations/'),
  ]);

  const feed = [];

  eventsRes.data.forEach(item => {
    feed.push({ ...item, type: 'Event', timestamp: item.created_at ? new Date(item.created_at) : new Date(0) });
  });
  risksRes.data.forEach(item => {
    feed.push({ ...item, type: 'Risk', timestamp: item.created_at ? new Date(item.created_at) : new Date(0) });
  });
  predictionsRes.data.forEach(item => {
    feed.push({ ...item, type: 'Prediction', timestamp: item.created_at ? new Date(item.created_at) : new Date(0) });
  });
  recsRes.data.forEach(item => {
    feed.push({ ...item, type: 'Recommendation', timestamp: item.created_at ? new Date(item.created_at) : new Date(0) });
  });

  return {
    items: feed.sort((a, b) => b.timestamp - a.timestamp),
    counts: {
      total: feed.length,
      events: eventsRes.data.length,
      risks: risksRes.data.length,
      predictions: predictionsRes.data.length,
      recommendations: recsRes.data.length
    }
  };
};

export default function IntelligenceFeed() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['intelligenceFeed'],
    queryFn: fetchFeedData,
    refetchInterval: 30000,
  });

  const counts = data?.counts || { total: 0, events: 0, risks: 0, predictions: 0, recommendations: 0 };

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const filteredFeed = useMemo(() => {
    const feedItems = data?.items || [];
    return feedItems.filter(item => {
      let searchableText = '';
      if (item.type === 'Event') searchableText = `${item.title || ''} ${item.description || ''} ${item.event_type || ''}`;
      else if (item.type === 'Risk') searchableText = `${item.risk_name || ''} ${item.risk_category || ''}`;
      else if (item.type === 'Prediction') searchableText = `${item.predicted_risk || ''} ${item.prediction_model || ''}`;
      else if (item.type === 'Recommendation') searchableText = `${item.recommendation_title || ''} ${item.recommendation_text || ''}`;

      const matchesSearch = search === '' || searchableText.toLowerCase().includes(search.toLowerCase());
      const matchesType = typeFilter === '' || item.type === typeFilter;

      return matchesSearch && matchesType;
    }).slice(0, 100); // Limit to top 100 recent after filtering
  }, [data?.items, search, typeFilter]);

  const handleClearFilters = () => {
    setSearch('');
    setTypeFilter('');
  };

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load intelligence feed</h2>
        <p className="text-muted-foreground mt-2 max-w-md">{error.message}</p>
        <Button variant="outline" className="mt-6" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  const renderFeedItem = (item) => {
    // Safe timestamp formatter
    const safeFormatTime = (ts) => {
      try {
        if (!ts || isNaN(ts.getTime()) || ts.getTime() === 0) return 'Unknown Time';
        return format(ts, 'MMM d, p');
      } catch {
        return 'Unknown Time';
      }
    };

    switch (item.type) {
      case 'Event':
        return (
          <div 
            key={`event-${item.id}`} 
            className="flex gap-4 p-4 rounded-lg border border-border/50 bg-card hover:bg-muted/30 cursor-pointer transition-colors group"
            onClick={() => navigate(`/events/${item.id}`)}
          >
            <div className="mt-0.5 bg-blue-500/10 p-2.5 rounded-full h-fit group-hover:bg-blue-500/20 transition-colors border border-blue-500/20">
              <Activity className="h-5 w-5 text-blue-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] uppercase font-semibold tracking-wider bg-blue-500/5 text-blue-500 border-blue-500/20">Event Signal</Badge>
                  <span className="text-xs text-muted-foreground whitespace-nowrap hidden sm:inline-block">
                    {safeFormatTime(item.timestamp)}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap sm:hidden">
                  {safeFormatTime(item.timestamp)}
                </span>
              </div>
              <h4 className="font-semibold text-base mt-2 group-hover:text-primary transition-colors truncate" title={item.title || 'Unnamed Event'}>
                {item.title || 'Unnamed Event'}
              </h4>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{item.description || 'No description provided.'}</p>
              <div className="flex flex-wrap gap-2 mt-3 items-center">
                {item.event_type && <Badge variant="secondary" className="text-xs bg-muted text-muted-foreground">{item.event_type}</Badge>}
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase ml-auto">ID: #{String(item.id).substring(0, 8)}</div>
              </div>
            </div>
          </div>
        );
      case 'Risk':
        return (
          <div 
            key={`risk-${item.id}`} 
            className="flex gap-4 p-4 rounded-lg border border-border/50 bg-card hover:bg-muted/30 cursor-pointer transition-colors group"
            onClick={() => navigate(`/risks/${item.id}`)}
          >
            <div className="mt-0.5 bg-red-500/10 p-2.5 rounded-full h-fit group-hover:bg-red-500/20 transition-colors border border-red-500/20">
              <AlertTriangle className="h-5 w-5 text-destructive" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] uppercase font-semibold tracking-wider bg-red-500/5 text-destructive border-red-500/20">Risk Detected</Badge>
                  <span className="text-xs text-muted-foreground whitespace-nowrap hidden sm:inline-block">
                    {safeFormatTime(item.timestamp)}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap sm:hidden">
                  {safeFormatTime(item.timestamp)}
                </span>
              </div>
              <h4 className="font-semibold text-base mt-2 group-hover:text-primary transition-colors truncate" title={item.risk_name || 'Unnamed Risk'}>
                {item.risk_name || 'Unnamed Risk'}
              </h4>
              <p className="text-sm text-muted-foreground mt-1">A {item.severity?.toLowerCase() || 'unknown'} severity risk has been identified by the AI engine.</p>
              <div className="flex flex-wrap gap-2 mt-3 items-center">
                <SeverityBadge severity={item.severity} />
                <span className="text-xs font-medium text-muted-foreground">Score: {item.risk_score != null ? `${Number(item.risk_score).toFixed(1)}%` : 'N/A'}</span>
                {item.status && <Badge variant="outline" className="text-[10px] ml-2 capitalize">{item.status}</Badge>}
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase ml-auto">ID: #{String(item.id).substring(0, 8)}</div>
              </div>
            </div>
          </div>
        );
      case 'Prediction':
        return (
          <div 
            key={`pred-${item.id}`} 
            className="flex gap-4 p-4 rounded-lg border border-border/50 bg-card hover:bg-muted/30 cursor-pointer transition-colors group"
            onClick={() => navigate(`/predictions/${item.id}`)}
          >
            <div className="mt-0.5 bg-purple-500/10 p-2.5 rounded-full h-fit group-hover:bg-purple-500/20 transition-colors border border-purple-500/20">
              <BrainCircuit className="h-5 w-5 text-purple-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] uppercase font-semibold tracking-wider bg-purple-500/5 text-purple-500 border-purple-500/20">AI Prediction</Badge>
                  <span className="text-xs text-muted-foreground whitespace-nowrap hidden sm:inline-block">
                    {safeFormatTime(item.timestamp)}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap sm:hidden">
                  {safeFormatTime(item.timestamp)}
                </span>
              </div>
              <h4 className="font-semibold text-base mt-2 group-hover:text-primary transition-colors line-clamp-2" title={item.predicted_risk || 'Unknown Prediction'}>
                {item.predicted_risk || 'Unknown Prediction'}
              </h4>
              <p className="text-sm text-muted-foreground mt-1">Generated by engine: <span className="font-medium text-foreground">{item.prediction_model || 'Unknown Model'}</span></p>
              <div className="flex flex-wrap gap-2 mt-3 items-center">
                <SeverityBadge severity={item.predicted_severity} />
                <span className="text-xs font-medium text-muted-foreground">Confidence: {item.confidence_score != null ? `${(Number(item.confidence_score || 0) * 100).toFixed(1)}%` : 'N/A'}</span>
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase ml-auto">ID: #{String(item.id).substring(0, 8)}</div>
              </div>
            </div>
          </div>
        );
      case 'Recommendation':
        return (
          <div 
            key={`rec-${item.id}`} 
            className="flex gap-4 p-4 rounded-lg border border-border/50 bg-card hover:bg-muted/30 cursor-pointer transition-colors group"
            onClick={() => navigate(`/recommendations/${item.id}`)}
          >
            <div className="mt-0.5 bg-green-500/10 p-2.5 rounded-full h-fit group-hover:bg-green-500/20 transition-colors border border-green-500/20">
              <Lightbulb className="h-5 w-5 text-green-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] uppercase font-semibold tracking-wider bg-green-500/5 text-green-500 border-green-500/20">Decision Support</Badge>
                  <span className="text-xs text-muted-foreground whitespace-nowrap hidden sm:inline-block">
                    {safeFormatTime(item.timestamp)}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap sm:hidden">
                  {safeFormatTime(item.timestamp)}
                </span>
              </div>
              <h4 className="font-semibold text-base mt-2 group-hover:text-primary transition-colors truncate" title={item.recommendation_title || 'Unnamed Action'}>
                {item.recommendation_title || 'Unnamed Action'}
              </h4>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{item.recommendation_text || 'No detailed strategy provided.'}</p>
              <div className="flex flex-wrap gap-2 mt-3 items-center">
                <PriorityBadge priority={item.priority} />
                {item.status && <Badge variant="secondary" className="text-[10px] capitalize bg-muted text-muted-foreground">{item.status}</Badge>}
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase ml-auto">ID: #{String(item.id).substring(0, 8)}</div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Rss className="h-8 w-8 text-primary" />
            Intelligence Feed
          </h2>
          <p className="text-muted-foreground mt-1">Real-time supply chain intelligence, AI analysis, and decision signals in one unified stream.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
        <Card className="p-4 flex flex-col justify-between border-primary/20 bg-primary/5 lg:col-span-1 col-span-2">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Total Signals</h3>
            <Rss className="h-4 w-4 text-primary" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-primary">
            {isLoading ? <Skeleton className="h-8 w-16" /> : counts.total}
          </div>
        </Card>
        
        <Card className="p-4 flex flex-col justify-between bg-card">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Events</h3>
            <Activity className="h-4 w-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-6 w-12" /> : counts.events}
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between bg-card">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Risks</h3>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </div>
          <div className="text-2xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-6 w-12" /> : counts.risks}
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between bg-card">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Predictions</h3>
            <BrainCircuit className="h-4 w-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-6 w-12" /> : counts.predictions}
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between bg-card">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Actions</h3>
            <Lightbulb className="h-4 w-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-6 w-12" /> : counts.recommendations}
          </div>
        </Card>
      </div>

      {/* Feed Controls */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/50 bg-muted/10">
          <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Feed Controls</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-6">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Feed</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search across all intelligence signals..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Intelligence Type</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Signals</option>
                <option value="Event">Events</option>
                <option value="Risk">Risks</option>
                <option value="Prediction">AI Predictions</option>
                <option value="Recommendation">Recommendations</option>
              </select>
            </div>
            
            <div className="md:col-span-2 flex justify-end">
              <Button 
                variant="ghost" 
                className="h-10 px-3 w-full border border-transparent hover:bg-muted/50 text-muted-foreground disabled:opacity-50" 
                onClick={handleClearFilters}
                disabled={!(search || typeFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Intelligence Stream */}
      <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[31px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border/50 before:to-transparent">
        {isLoading ? (
          <div className="space-y-6 relative z-10">
            {[...Array(5)].map((_, i) => (
              <Card key={i} className="p-4 flex gap-4">
                <Skeleton className="h-12 w-12 rounded-full shrink-0" />
                <div className="flex-1 space-y-2 py-1">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-1/4" />
                  <Skeleton className="h-16 w-full" />
                </div>
              </Card>
            ))}
          </div>
        ) : filteredFeed.length === 0 ? (
          <Card className="text-center py-16 text-muted-foreground relative z-10 border-dashed border-2">
            <Search className="mx-auto h-10 w-10 mb-4 opacity-30" />
            <h3 className="text-lg font-medium text-foreground">No intelligence signals match</h3>
            <p className="mt-1 max-w-sm mx-auto text-sm">We couldn't find any signals matching your current filters. Try adjusting your search query or type filter.</p>
            <Button variant="outline" className="mt-6" onClick={handleClearFilters}>Clear all filters</Button>
          </Card>
        ) : (
          <div className="space-y-4 relative z-10">
            {filteredFeed.map(item => renderFeedItem(item))}
            {filteredFeed.length > 0 && (
              <div className="text-center py-6 text-sm text-muted-foreground font-medium">
                End of recent feed. {counts.total > 100 && 'Only showing the top 100 most recent signals.'}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline" className="text-[10px]">UNKNOWN</Badge>;
  const lower = severity.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="high" className="text-[10px] uppercase whitespace-nowrap">{severity}</Badge>;
  if (lower === 'medium') return <Badge variant="medium" className="text-[10px] uppercase whitespace-nowrap">{severity}</Badge>;
  if (lower === 'low') return <Badge variant="low" className="text-[10px] uppercase whitespace-nowrap">{severity}</Badge>;
  return <Badge variant="outline" className="text-[10px] uppercase whitespace-nowrap">{severity}</Badge>;
}

function PriorityBadge({ priority }) {
  if (!priority) return <Badge variant="outline" className="text-[10px]">UNKNOWN</Badge>;
  const lower = priority.toLowerCase();
  if (lower === 'critical') return <Badge variant="destructive" className="text-[10px] uppercase whitespace-nowrap">{priority}</Badge>;
  if (lower === 'high') return <Badge variant="high" className="text-[10px] uppercase whitespace-nowrap">{priority}</Badge>;
  if (lower === 'medium') return <Badge variant="medium" className="text-[10px] uppercase whitespace-nowrap">{priority}</Badge>;
  if (lower === 'low') return <Badge variant="low" className="text-[10px] uppercase whitespace-nowrap">{priority}</Badge>;
  return <Badge variant="outline" className="text-[10px] uppercase whitespace-nowrap">{priority}</Badge>;
}
