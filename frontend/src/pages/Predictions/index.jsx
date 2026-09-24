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
import { Search, X, ChevronLeft, ChevronRight, BrainCircuit, Calendar, AlertTriangle, RefreshCw, BarChart3, Activity } from 'lucide-react';
import { format } from 'date-fns';

const fetchPredictions = async () => {
  const response = await api.get('/predictions/');
  return response.data;
};

const getConfidenceColor = (confidence) => {
  const score = Number(confidence) || 0;
  // Assuming confidence is 0-1
  if (score >= 0.85) return 'bg-green-500';
  if (score >= 0.60) return 'bg-amber-500';
  if (score >= 0.40) return 'bg-yellow-500';
  return 'bg-destructive';
};

export default function Predictions() {
  const navigate = useNavigate();
  const { data: predictions = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['predictionsList'],
    queryFn: fetchPredictions,
  });

  const [search, setSearch] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const models = useMemo(() => [...new Set(predictions.map(p => p.prediction_model).filter(Boolean))], [predictions]);
  const severities = useMemo(() => [...new Set(predictions.map(p => p.predicted_severity).filter(Boolean))], [predictions]);
  const statuses = useMemo(() => [...new Set(predictions.map(p => p.prediction_status).filter(Boolean))], [predictions]);

  const kpis = useMemo(() => {
    if (!predictions.length) return null;
    let pendingOrActive = 0;
    let criticalHigh = 0;
    let totalConfidence = 0;
    let scoredCount = 0;
    
    predictions.forEach(p => {
      const s = p.prediction_status?.toLowerCase();
      // Assume anything not explicitly resolved or false positive is active/pending
      if (s && !['resolved', 'dismissed', 'false positive', 'completed'].includes(s)) {
        pendingOrActive++;
      }
      
      const sev = p.predicted_severity?.toLowerCase();
      if (sev === 'critical' || sev === 'high') criticalHigh++;
      
      if (p.confidence_score != null) {
        totalConfidence += Number(p.confidence_score);
        scoredCount++;
      }
    });
    
    return {
      total: predictions.length,
      active: pendingOrActive,
      criticalHigh,
      avgConfidence: scoredCount > 0 ? (totalConfidence / scoredCount) * 100 : 0
    };
  }, [predictions]);

  // Model Intelligence Highlights
  const highlights = useMemo(() => {
    if (!predictions.length) return null;
    
    // Highest confidence critical/high prediction
    const highestConfidence = [...predictions]
      .filter(p => {
        const s = p.prediction_status?.toLowerCase();
        return s && !['resolved', 'dismissed', 'false positive'].includes(s);
      })
      .sort((a,b) => (b.confidence_score || 0) - (a.confidence_score || 0))[0];

    // Most common model
    const modelCounts = {};
    predictions.forEach(p => {
      if (p.prediction_model) {
        modelCounts[p.prediction_model] = (modelCounts[p.prediction_model] || 0) + 1;
      }
    });
    const mostCommonModel = Object.keys(modelCounts).sort((a,b) => modelCounts[b] - modelCounts[a])[0];

    return {
      highestConfidence,
      mostCommonModel,
      mostCommonModelCount: mostCommonModel ? modelCounts[mostCommonModel] : 0
    };
  }, [predictions]);

  const filteredPredictions = useMemo(() => {
    return predictions.filter(pred => {
      const matchesSearch = search === '' || 
        pred.predicted_risk?.toLowerCase().includes(search.toLowerCase());
      
      const matchesModel = modelFilter === '' || pred.prediction_model === modelFilter;
      const matchesSeverity = severityFilter === '' || pred.predicted_severity === severityFilter;
      const matchesStatus = statusFilter === '' || pred.prediction_status === statusFilter;

      return matchesSearch && matchesModel && matchesSeverity && matchesStatus;
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [predictions, search, modelFilter, severityFilter, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredPredictions.length / itemsPerPage));
  const paginatedPredictions = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredPredictions.slice(start, start + itemsPerPage);
  }, [filteredPredictions, currentPage]);

  const handleClearFilters = () => {
    setSearch('');
    setModelFilter('');
    setSeverityFilter('');
    setStatusFilter('');
    setCurrentPage(1);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [search, modelFilter, severityFilter, statusFilter]);

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load predictions</h2>
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
            <BrainCircuit className="h-8 w-8 text-primary" />
            Prediction Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">Analyze AI-generated risk predictions and model confidence across your supply chain.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Total Predictions</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <BrainCircuit className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.total || 0}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Active/Pending</h3>
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
            <h3 className="text-sm font-medium text-muted-foreground">High/Critical Alerts</h3>
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
            <h3 className="text-sm font-medium text-muted-foreground">Average Confidence</h3>
            <div className="p-2 bg-blue-500/10 rounded-full">
              <BarChart3 className="h-4 w-4 text-blue-500" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-foreground">
            {isLoading ? <Skeleton className="h-8 w-16" /> : `${(kpis?.avgConfidence || 0).toFixed(1)}%`}
          </div>
        </Card>
      </div>

      {/* Model Intelligence Highlights */}
      {!isLoading && highlights && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold tracking-tight text-muted-foreground uppercase">Model Intelligence Highlights</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {highlights.highestConfidence && (
              <Card 
                className="p-4 flex flex-col justify-between cursor-pointer hover:border-primary/50 transition-colors bg-muted/10 border-border/60" 
                onClick={() => navigate(`/predictions/${highlights.highestConfidence.id}`)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Top Active Prediction</div>
                  <SeverityBadge severity={highlights.highestConfidence.predicted_severity} />
                </div>
                <div className="font-medium text-sm line-clamp-2 pr-2 mb-2" title={highlights.highestConfidence.predicted_risk}>
                  {highlights.highestConfidence.predicted_risk}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-auto">
                  <span className="truncate max-w-[120px]">{highlights.highestConfidence.prediction_model}</span>
                  <div className="flex items-center gap-2 font-medium">
                    <span className="text-foreground">{(Number(highlights.highestConfidence.confidence_score || 0) * 100).toFixed(1)}% Confidence</span>
                  </div>
                </div>
              </Card>
            )}
            
            {highlights.mostCommonModel && (
              <Card className="p-4 flex flex-col justify-between bg-muted/10 border-border/60">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Primary Engine</div>
                  <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">Active</Badge>
                </div>
                <div className="font-medium text-lg mb-1">
                  {highlights.mostCommonModel}
                </div>
                <div className="text-xs text-muted-foreground mt-auto">
                  Driving <span className="font-semibold text-foreground">{highlights.mostCommonModelCount}</span> total predictions
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
          <CardDescription>Narrow down predictions by model, severity, or keyword.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Query</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search predicted risks..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">AI Model</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={modelFilter}
                onChange={(e) => setModelFilter(e.target.value)}
              >
                <option value="">All Models</option>
                {models.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Predicted Severity</label>
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
                disabled={!(search || modelFilter || severityFilter || statusFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Directory */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Predictions...' : `Prediction Directory (${filteredPredictions.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredPredictions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No matching predictions</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                We couldn't find any predictions matching your current filters. Try broadening your search criteria.
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
                    <TableHead className="w-[35%] pl-6">Predicted Risk</TableHead>
                    <TableHead className="w-[15%]">Model Engine</TableHead>
                    <TableHead className="w-[15%]">Confidence</TableHead>
                    <TableHead className="w-[10%]">Status</TableHead>
                    <TableHead className="w-[10%]">Created</TableHead>
                    <TableHead className="w-[15%] pr-6 text-right">Severity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedPredictions.map(pred => {
                    const confidencePct = pred.confidence_score != null ? Number(pred.confidence_score) * 100 : 0;
                    return (
                      <TableRow 
                        key={pred.id} 
                        className="cursor-pointer group"
                        onClick={() => navigate(`/predictions/${pred.id}`)}
                      >
                        <TableCell className="pl-6">
                          <div className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1" title={pred.predicted_risk}>
                            {pred.predicted_risk}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1 font-mono">
                            ID: #{String(pred.id).substring(0, 8)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="px-1.5 py-0 text-[10px] uppercase font-semibold tracking-wider bg-muted text-muted-foreground">
                            {pred.prediction_model}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1.5 mt-1">
                            <span className="text-sm font-medium">{pred.confidence_score != null ? `${confidencePct.toFixed(1)}%` : 'N/A'}</span>
                            <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${getConfidenceColor(pred.confidence_score)}`} 
                                style={{ width: `${Math.min(100, Math.max(0, confidencePct))}%` }} 
                              />
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize whitespace-nowrap bg-background/50">
                            {pred.prediction_status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                            <Calendar className="h-3.5 w-3.5 shrink-0" />
                            <span className="whitespace-nowrap">{pred.created_at ? format(new Date(pred.created_at), 'MMM d') : 'Unknown'}</span>
                          </div>
                        </TableCell>
                        <TableCell className="pr-6 text-right">
                          <SeverityBadge severity={pred.predicted_severity} />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between p-4 border-t border-border/50 bg-muted/10">
                  <p className="text-xs text-muted-foreground">
                    Showing <span className="font-medium text-foreground">{((currentPage - 1) * itemsPerPage) + 1}</span> to <span className="font-medium text-foreground">{Math.min(currentPage * itemsPerPage, filteredPredictions.length)}</span> of <span className="font-medium text-foreground">{filteredPredictions.length}</span> results
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
