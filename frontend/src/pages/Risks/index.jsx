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
import { Search, X, ChevronLeft, ChevronRight, ShieldAlert, Calendar, AlertTriangle, RefreshCw, AlertCircle, BarChart3 } from 'lucide-react';
import { format } from 'date-fns';

const fetchRisks = async () => {
  const response = await api.get('/risks/');
  return response.data;
};

const getScoreColor = (score) => {
  const s = Number(score) || 0;
  if (s >= 80) return 'bg-destructive';
  if (s >= 50) return 'bg-amber-500';
  if (s >= 20) return 'bg-yellow-500';
  return 'bg-green-500';
};

export default function Risks() {
  const navigate = useNavigate();
  const { data: risks = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['risksList'],
    queryFn: fetchRisks,
  });

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const riskTypes = useMemo(() => [...new Set(risks.map(r => r.risk_type).filter(Boolean))], [risks]);
  const severities = useMemo(() => [...new Set(risks.map(r => r.severity).filter(Boolean))], [risks]);
  const statuses = useMemo(() => [...new Set(risks.map(r => r.status).filter(Boolean))], [risks]);

  const kpis = useMemo(() => {
    if (!risks.length) return null;
    let active = 0;
    let criticalHigh = 0;
    let totalScore = 0;
    let scoredRisks = 0;
    
    risks.forEach(r => {
      const s = r.status?.toLowerCase();
      if (s === 'active' || s === 'new' || s === 'in progress') active++;
      
      const sev = r.severity?.toLowerCase();
      if (sev === 'critical' || sev === 'high') criticalHigh++;
      
      if (r.risk_score != null) {
        totalScore += Number(r.risk_score);
        scoredRisks++;
      }
    });
    
    return {
      total: risks.length,
      active,
      criticalHigh,
      avgScore: scoredRisks > 0 ? (totalScore / scoredRisks).toFixed(1) : 0
    };
  }, [risks]);

  const priorityRisks = useMemo(() => {
    return risks
      .filter(r => {
        const s = r.status?.toLowerCase();
        return s === 'active' || s === 'new' || s === 'in progress';
      })
      .sort((a,b) => (b.risk_score || 0) - (a.risk_score || 0))
      .slice(0, 3);
  }, [risks]);

  const filteredRisks = useMemo(() => {
    return risks.filter(risk => {
      const matchesSearch = search === '' || 
        risk.risk_name?.toLowerCase().includes(search.toLowerCase());
      
      const matchesType = typeFilter === '' || risk.risk_type === typeFilter;
      const matchesSeverity = severityFilter === '' || risk.severity === severityFilter;
      const matchesStatus = statusFilter === '' || risk.status === statusFilter;

      return matchesSearch && matchesType && matchesSeverity && matchesStatus;
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [risks, search, typeFilter, severityFilter, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredRisks.length / itemsPerPage));
  const paginatedRisks = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredRisks.slice(start, start + itemsPerPage);
  }, [filteredRisks, currentPage]);

  const handleClearFilters = () => {
    setSearch('');
    setTypeFilter('');
    setSeverityFilter('');
    setStatusFilter('');
    setCurrentPage(1);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [search, typeFilter, severityFilter, statusFilter]);

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load risks</h2>
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
            <ShieldAlert className="h-8 w-8 text-primary" />
            Risk Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">Analyze, prioritize, and manage supply chain risks across your network.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Total Identified Risks</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <ShieldAlert className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.total || 0}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Active Risks</h3>
            <div className="p-2 bg-amber-500/10 rounded-full">
              <AlertCircle className="h-4 w-4 text-amber-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.active || 0}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">High/Critical Severity</h3>
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
            <h3 className="text-sm font-medium text-muted-foreground">Average Risk Score</h3>
            <div className="p-2 bg-blue-500/10 rounded-full">
              <BarChart3 className="h-4 w-4 text-blue-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-foreground">
            {isLoading ? <Skeleton className="h-8 w-16" /> : `${kpis?.avgScore || 0}%`}
          </div>
        </Card>
      </div>

      {/* Priority Risk Signals */}
      {priorityRisks?.length > 0 && !isLoading && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold tracking-tight text-muted-foreground uppercase">Priority Risk Signals</h3>
          <div className="grid gap-4 md:grid-cols-3">
            {priorityRisks.map(risk => (
              <Card 
                key={`priority-${risk.id}`} 
                className="p-4 flex flex-col justify-between cursor-pointer hover:border-primary/50 transition-colors bg-muted/10 border-border/60" 
                onClick={() => navigate(`/risks/${risk.id}`)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-sm line-clamp-1 pr-2" title={risk.risk_name}>{risk.risk_name}</div>
                  <SeverityBadge severity={risk.severity} />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
                  <span className="truncate max-w-[120px]">{risk.risk_type}</span>
                  <div className="flex items-center gap-2 font-medium">
                    <span className="text-foreground">{risk.risk_score != null ? `${Number(risk.risk_score).toFixed(1)}%` : '0%'}</span>
                    <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className={`h-full ${getScoreColor(risk.risk_score)}`} style={{ width: `${Math.min(100, Math.max(0, risk.risk_score || 0))}%` }} />
                    </div>
                  </div>
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
          <CardDescription>Narrow down risks by category, severity, or keyword.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Query</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search risk names..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Risk Category</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Categories</option>
                {riskTypes.map(type => <option key={type} value={type}>{type}</option>)}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">AI Severity</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All Severities</option>
                {severities.map(sev => <option key={sev} value={sev}>{sev}</option>)}
              </select>
            </div>

            <div className="md:col-span-2">
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
                disabled={!(search || typeFilter || severityFilter || statusFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Directory */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Risks...' : `Risk Directory (${filteredRisks.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredRisks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No matching risks</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                We couldn't find any risks matching your current filters. Try broadening your search criteria.
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
                    <TableHead className="w-[35%] pl-6">Risk Details</TableHead>
                    <TableHead className="w-[15%]">Category</TableHead>
                    <TableHead className="w-[15%]">Risk Score</TableHead>
                    <TableHead className="w-[10%]">Status</TableHead>
                    <TableHead className="w-[10%]">Updated</TableHead>
                    <TableHead className="w-[15%] pr-6 text-right">Severity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedRisks.map(risk => (
                    <TableRow 
                      key={risk.id} 
                      className="cursor-pointer group"
                      onClick={() => navigate(`/risks/${risk.id}`)}
                    >
                      <TableCell className="pl-6">
                        <div className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1" title={risk.risk_name}>
                          {risk.risk_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="px-1.5 py-0 text-[10px] uppercase font-semibold tracking-wider bg-muted text-muted-foreground">
                          {risk.risk_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1.5 mt-1">
                          <span className="text-sm font-medium">{risk.risk_score != null ? `${Number(risk.risk_score).toFixed(2)}%` : '0%'}</span>
                          <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${getScoreColor(risk.risk_score)}`} 
                              style={{ width: `${Math.min(100, Math.max(0, risk.risk_score || 0))}%` }} 
                            />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize whitespace-nowrap bg-background/50">
                          {risk.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                          <Calendar className="h-3.5 w-3.5 shrink-0" />
                          <span className="whitespace-nowrap">{risk.updated_at ? format(new Date(risk.updated_at), 'MMM d') : format(new Date(risk.created_at), 'MMM d')}</span>
                        </div>
                      </TableCell>
                      <TableCell className="pr-6 text-right">
                        <SeverityBadge severity={risk.severity} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between p-4 border-t border-border/50 bg-muted/10">
                  <p className="text-xs text-muted-foreground">
                    Showing <span className="font-medium text-foreground">{((currentPage - 1) * itemsPerPage) + 1}</span> to <span className="font-medium text-foreground">{Math.min(currentPage * itemsPerPage, filteredRisks.length)}</span> of <span className="font-medium text-foreground">{filteredRisks.length}</span> results
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

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline">Unknown</Badge>;
  const lower = severity.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="high" className="whitespace-nowrap">{severity}</Badge>;
  if (lower === 'medium') return <Badge variant="medium" className="whitespace-nowrap">{severity}</Badge>;
  if (lower === 'low') return <Badge variant="low" className="whitespace-nowrap">{severity}</Badge>;
  return <Badge variant="outline" className="whitespace-nowrap">{severity}</Badge>;
}
