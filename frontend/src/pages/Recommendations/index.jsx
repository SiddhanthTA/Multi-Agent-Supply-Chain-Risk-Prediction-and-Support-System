import { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';
import { Search, X, ChevronLeft, ChevronRight, Lightbulb, Calendar, AlertTriangle, RefreshCw, Activity, CheckCircle2 } from 'lucide-react';
import { format } from 'date-fns';

const fetchRecommendations = async () => {
  const response = await api.get('/recommendations/');
  return response.data;
};

export default function Recommendations() {
  const navigate = useNavigate();
  const { data: recommendations = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['recommendationsList'],
    queryFn: fetchRecommendations,
  });

  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const priorities = useMemo(() => [...new Set(recommendations.map(r => r.priority).filter(Boolean))], [recommendations]);
  const statuses = useMemo(() => [...new Set(recommendations.map(r => r.status).filter(Boolean))], [recommendations]);

  const kpis = useMemo(() => {
    if (!recommendations.length) return null;
    let active = 0;
    let criticalHigh = 0;
    let resolved = 0;
    
    recommendations.forEach(r => {
      const s = r.status?.toLowerCase();
      if (s && ['implemented', 'resolved', 'completed'].includes(s)) resolved++;
      else if (s && !['dismissed', 'rejected'].includes(s)) active++;
      
      const p = r.priority?.toLowerCase();
      if (p === 'critical' || p === 'high') criticalHigh++;
    });
    
    return {
      total: recommendations.length,
      active,
      criticalHigh,
      resolutionRate: recommendations.length > 0 ? ((resolved / recommendations.length) * 100).toFixed(1) : 0
    };
  }, [recommendations]);

  const highlights = useMemo(() => {
    if (!recommendations.length) return null;
    
    const priorityRank = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
    const topAction = [...recommendations]
      .filter(r => {
        const s = r.status?.toLowerCase();
        return s && !['implemented', 'resolved', 'completed', 'dismissed'].includes(s);
      })
      .sort((a,b) => {
        const pA = priorityRank[a.priority?.toLowerCase()] || 0;
        const pB = priorityRank[b.priority?.toLowerCase()] || 0;
        if (pA !== pB) return pB - pA;
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      })[0];

    const statusCounts = {};
    recommendations.forEach(r => {
      if (r.status) {
        statusCounts[r.status] = (statusCounts[r.status] || 0) + 1;
      }
    });
    const mostCommonStatus = Object.keys(statusCounts).sort((a,b) => statusCounts[b] - statusCounts[a])[0];

    return {
      topAction,
      mostCommonStatus,
      mostCommonStatusCount: mostCommonStatus ? statusCounts[mostCommonStatus] : 0
    };
  }, [recommendations]);

  const filteredRecommendations = useMemo(() => {
    return recommendations.filter(rec => {
      const matchesSearch = search === '' || 
        rec.recommendation_title?.toLowerCase().includes(search.toLowerCase()) ||
        rec.recommendation_text?.toLowerCase().includes(search.toLowerCase());
      
      const matchesPriority = priorityFilter === '' || rec.priority === priorityFilter;
      const matchesStatus = statusFilter === '' || rec.status === statusFilter;

      return matchesSearch && matchesPriority && matchesStatus;
    }).sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  }, [recommendations, search, priorityFilter, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredRecommendations.length / itemsPerPage));
  const paginatedRecommendations = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredRecommendations.slice(start, start + itemsPerPage);
  }, [filteredRecommendations, currentPage]);

  const handleClearFilters = () => {
    setSearch('');
    setPriorityFilter('');
    setStatusFilter('');
    setCurrentPage(1);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [search, priorityFilter, statusFilter]);

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load recommendations</h2>
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
            <Lightbulb className="h-8 w-8 text-primary" />
            Recommendation Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">Actionable AI-driven mitigation strategies and decision support.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Total Recommendations</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <Lightbulb className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.total || 0}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Active/Open</h3>
            <div className="p-2 bg-amber-500/10 rounded-full">
              <Activity className="h-4 w-4 text-amber-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.active || 0}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">High/Critical Priority</h3>
            <div className="p-2 bg-destructive/10 rounded-full">
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-destructive">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.criticalHigh || 0}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Implementation Rate</h3>
            <div className="p-2 bg-green-500/10 rounded-full">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-foreground">
            {isLoading ? <Skeleton className="h-8 w-16" /> : `${kpis?.resolutionRate || 0}%`}
          </div>
        </Card>
      </div>

      {/* Decision Intelligence Highlights */}
      {!isLoading && highlights && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold tracking-tight text-muted-foreground uppercase">Decision Intelligence Highlights</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {highlights.topAction && (
              <Card 
                className="p-4 flex flex-col justify-between cursor-pointer hover:border-primary/50 transition-colors bg-muted/10 border-border/60" 
                onClick={() => navigate(`/recommendations/${highlights.topAction.id}`)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Top Recommended Action</div>
                  <PriorityBadge priority={highlights.topAction.priority} />
                </div>
                <div className="font-medium text-sm line-clamp-2 pr-2 mb-2" title={highlights.topAction.recommendation_title}>
                  {highlights.topAction.recommendation_title}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-auto">
                  <span className="truncate max-w-[200px] font-mono">ID: #{String(highlights.topAction.id).substring(0, 8)}</span>
                  <Badge variant="outline" className="bg-background/50 capitalize">{highlights.topAction.status}</Badge>
                </div>
              </Card>
            )}
            
            {highlights.mostCommonStatus && (
              <Card className="p-4 flex flex-col justify-between bg-muted/10 border-border/60">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Primary Lifecycle State</div>
                  <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 capitalize">{highlights.mostCommonStatus}</Badge>
                </div>
                <div className="font-medium text-lg mb-1 capitalize">
                  {highlights.mostCommonStatus}
                </div>
                <div className="text-xs text-muted-foreground mt-auto">
                  Currently tracking <span className="font-semibold text-foreground">{highlights.mostCommonStatusCount}</span> items in this state
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Filter Portfolio */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-lg">Filter Portfolio</CardTitle>
          <CardDescription>Narrow down recommendations by priority, status, or keyword.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Query</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search titles or content..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Priority</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
              >
                <option value="">All Priorities</option>
                {priorities.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div className="md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Status</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                {statuses.map(stat => <option key={stat} value={stat}>{stat}</option>)}
              </select>
            </div>
            
            <div className="md:col-span-1 flex justify-end">
              <Button 
                variant="ghost" 
                className="h-10 px-3 w-full border border-transparent hover:bg-muted/50 text-muted-foreground disabled:opacity-50" 
                onClick={handleClearFilters}
                disabled={!(search || priorityFilter || statusFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendation Directory */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Recommendations...' : `Recommendation Directory (${filteredRecommendations.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredRecommendations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No matching recommendations</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                We couldn't find any recommendations matching your current filters. Try broadening your search criteria.
              </p>
              <Button variant="outline" className="mt-4" onClick={handleClearFilters}>
                Clear all filters
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="bg-transparent hover:bg-transparent">
                    <TableHead className="w-[50%] pl-6">Recommendation Strategy</TableHead>
                    <TableHead className="w-[15%]">Priority</TableHead>
                    <TableHead className="w-[15%]">Status</TableHead>
                    <TableHead className="w-[20%] pr-6 text-right">Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedRecommendations.map(rec => (
                    <TableRow 
                      key={rec.id} 
                      className="cursor-pointer group"
                      onClick={() => navigate(`/recommendations/${rec.id}`)}
                    >
                      <TableCell className="pl-6">
                        <div className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1" title={rec.recommendation_title}>
                          {rec.recommendation_title}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1" title={rec.recommendation_text}>
                          {rec.recommendation_text || 'No description available'}
                        </div>
                        <div className="text-[10px] text-muted-foreground/70 mt-1 font-mono uppercase">
                          ID: #{String(rec.id).substring(0, 8)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <PriorityBadge priority={rec.priority} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize whitespace-nowrap bg-background/50">
                          {rec.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-6 text-right">
                        <div className="flex items-center justify-end gap-1.5 text-muted-foreground text-sm">
                          <Calendar className="h-3.5 w-3.5 shrink-0" />
                          <span className="whitespace-nowrap">{rec.created_at ? format(new Date(rec.created_at), 'MMM d, yyyy') : 'Unknown'}</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between p-4 border-t border-border/50 bg-muted/10">
                  <p className="text-xs text-muted-foreground">
                    Showing <span className="font-medium text-foreground">{((currentPage - 1) * itemsPerPage) + 1}</span> to <span className="font-medium text-foreground">{Math.min(currentPage * itemsPerPage, filteredRecommendations.length)}</span> of <span className="font-medium text-foreground">{filteredRecommendations.length}</span> results
                  </p>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="h-8"
                      onClick={(e) => { e.stopPropagation(); setCurrentPage(p => Math.max(1, p - 1)); }}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" /> Prev
                    </Button>
                    <div className="text-xs font-medium px-2">
                      {currentPage} / {totalPages}
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="h-8"
                      onClick={(e) => { e.stopPropagation(); setCurrentPage(p => Math.min(totalPages, p + 1)); }}
                      disabled={currentPage === totalPages}
                    >
                      Next <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PriorityBadge({ priority }) {
  if (!priority) return <Badge variant="outline">Unknown</Badge>;
  const lower = priority.toLowerCase();
  if (lower === 'critical') return <Badge variant="destructive" className="whitespace-nowrap">{priority}</Badge>;
  if (lower === 'high') return <Badge variant="high" className="whitespace-nowrap">{priority}</Badge>;
  if (lower === 'medium') return <Badge variant="medium" className="whitespace-nowrap">{priority}</Badge>;
  if (lower === 'low') return <Badge variant="low" className="whitespace-nowrap">{priority}</Badge>;
  return <Badge variant="outline" className="whitespace-nowrap">{priority}</Badge>;
}
