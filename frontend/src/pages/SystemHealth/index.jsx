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
import { Activity, Database, Server, AlertTriangle, Clock, ServerCog, HeartPulse, Search, X, RefreshCw, Info } from 'lucide-react';
import { format } from 'date-fns';

const fetchHealthData = async () => {
  const [healthRes, logsRes] = await Promise.all([
    api.get('/health').catch(e => ({ error: true, message: e.message })),
    api.get('/system-logs/').catch(() => ({ data: [] }))
  ]);
  
  return {
    health: healthRes.error ? null : healthRes.data,
    healthError: healthRes.error ? healthRes.message : null,
    logs: Array.isArray(logsRes.data) 
      ? logsRes.data.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).slice(0, 100)
      : []
  };
};

export default function SystemHealth() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchHealthData,
    refetchInterval: 15000,
  });

  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('');

  const healthData = data?.health;
  
  // Safe status determination
  const isApiOnline = !isError && !data?.healthError;
  const dbStatusString = healthData?.database || '';
  const isDbConnected = dbStatusString.toLowerCase().includes('successfully');

  const logStats = useMemo(() => {
    const logsArray = data?.logs || [];
    let errors = 0;
    let warnings = 0;
    let infos = 0;

    logsArray.forEach(log => {
      const lvl = log.log_level?.toLowerCase();
      if (lvl === 'error' || lvl === 'critical') errors++;
      else if (lvl === 'warning') warnings++;
      else infos++;
    });

    return { total: logsArray.length, errors, warnings, infos };
  }, [data?.logs]);

  const filteredLogs = useMemo(() => {
    const logsArray = data?.logs || [];
    return logsArray.filter(log => {
      const matchesSearch = search === '' || 
        log.action?.toLowerCase().includes(search.toLowerCase()) || 
        log.details?.toLowerCase().includes(search.toLowerCase());
      
      const matchesLevel = levelFilter === '' || log.log_level?.toLowerCase() === levelFilter.toLowerCase();
      
      return matchesSearch && matchesLevel;
    });
  }, [data?.logs, search, levelFilter]);

  const handleClearFilters = () => {
    setSearch('');
    setLevelFilter('');
  };

  const getLogLevelBg = (level) => {
    const l = (level || '').toLowerCase();
    if (l === 'error' || l === 'critical') return 'bg-destructive/10 border-destructive/20 text-destructive';
    if (l === 'warning') return 'bg-amber-500/10 border-amber-500/20 text-amber-500';
    if (l === 'info' || l === 'success') return 'bg-blue-500/10 border-blue-500/20 text-blue-500';
    return 'bg-muted border-border text-muted-foreground';
  };

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <ServerCog className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Platform Unreachable</h2>
        <p className="text-muted-foreground mt-2 max-w-md">{error.message || 'The backend API is currently down or unreachable.'}</p>
        <Button variant="outline" className="mt-6" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Retry Connection
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <HeartPulse className="h-8 w-8 text-primary" />
            System Health
          </h2>
          <p className="text-muted-foreground mt-1">Monitor platform availability, backend services, database connectivity, and system activity.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className={`p-5 flex flex-col justify-between ${!isApiOnline ? 'border-destructive/50 bg-destructive/5' : ''}`}>
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Overall System Status</h3>
            <div className={`p-2 rounded-full ${isApiOnline && isDbConnected ? 'bg-green-500/10' : 'bg-destructive/10'}`}>
              <HeartPulse className={`h-4 w-4 ${isApiOnline && isDbConnected ? 'text-green-500' : 'text-destructive'}`} />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1">
            {isLoading ? <Skeleton className="h-8 w-24" /> : (
              <>
                <div className={`h-3 w-3 rounded-full ${isApiOnline && isDbConnected ? 'bg-green-500 animate-pulse' : 'bg-destructive'}`}></div>
                <span className="text-2xl font-bold tracking-tight">{isApiOnline && isDbConnected ? 'Healthy' : 'Degraded'}</span>
              </>
            )}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Database Connectivity</h3>
            <div className={`p-2 rounded-full ${isDbConnected ? 'bg-blue-500/10' : 'bg-amber-500/10'}`}>
              <Database className={`h-4 w-4 ${isDbConnected ? 'text-blue-500' : 'text-amber-500'}`} />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight flex items-center gap-2 mt-1">
            {isLoading ? <Skeleton className="h-8 w-24" /> : isDbConnected ? 'Connected' : 'Disconnected'}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Recent System Events</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <Activity className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight mt-1">
            {isLoading ? <Skeleton className="h-8 w-16" /> : logStats.total}
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Critical Errors</h3>
            <div className="p-2 bg-destructive/10 rounded-full">
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-destructive mt-1">
            {isLoading ? <Skeleton className="h-8 w-16" /> : logStats.errors}
          </div>
        </Card>
      </div>

      {/* Service Status Overview */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="bg-muted/10 border-b border-border/50 pb-4">
            <CardTitle className="text-lg flex items-center gap-2"><ServerCog className="h-5 w-5 text-muted-foreground" /> Platform Health Overview</CardTitle>
            <CardDescription>Real-time telemetry of backend microservices.</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 border border-border/50 rounded-lg bg-background">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-md ${isApiOnline ? 'bg-green-500/10' : 'bg-destructive/10'}`}>
                    <Server className={`h-4 w-4 ${isApiOnline ? 'text-green-500' : 'text-destructive'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm">FastAPI Backend API</h4>
                    <p className="text-xs text-muted-foreground">Core intelligence and routing service</p>
                  </div>
                </div>
                {isLoading ? <Skeleton className="h-6 w-16" /> : (
                  <Badge variant="outline" className={isApiOnline ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-destructive/10 text-destructive border-destructive/20'}>
                    {isApiOnline ? 'Online' : 'Offline'}
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 border border-border/50 rounded-lg bg-background">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-md ${isDbConnected ? 'bg-blue-500/10' : 'bg-amber-500/10'}`}>
                    <Database className={`h-4 w-4 ${isDbConnected ? 'text-blue-500' : 'text-amber-500'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm">PostgreSQL Database</h4>
                    <p className="text-xs text-muted-foreground line-clamp-1" title={dbStatusString}>{dbStatusString || 'Primary persistent storage cluster'}</p>
                  </div>
                </div>
                {isLoading ? <Skeleton className="h-6 w-16" /> : (
                  <Badge variant="outline" className={isDbConnected ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}>
                    {isDbConnected ? 'Connected' : 'Degraded'}
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="bg-muted/10 border-b border-border/50 pb-4">
            <CardTitle className="text-lg flex items-center gap-2"><Activity className="h-5 w-5 text-muted-foreground" /> Operational Summary</CardTitle>
            <CardDescription>Aggregated metrics from the latest system logs.</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex flex-col justify-center h-[calc(100%-80px)]">
            {isLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-2.5 px-4 bg-muted/30 rounded-lg border border-border/50">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Informational Events</span>
                  </div>
                  <span className="font-bold">{logStats.infos}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 px-4 bg-amber-500/5 rounded-lg border border-amber-500/20">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    <span className="text-sm font-medium text-amber-600 dark:text-amber-400">Warnings</span>
                  </div>
                  <span className="font-bold text-amber-600 dark:text-amber-400">{logStats.warnings}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 px-4 bg-destructive/5 rounded-lg border border-destructive/20">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                    <span className="text-sm font-medium text-destructive">Critical & Errors</span>
                  </div>
                  <span className="font-bold text-destructive">{logStats.errors}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Filter Portfolio */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-lg">Filter Logs</CardTitle>
          <CardDescription>Search operational activity by keyword or severity level.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-8">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Action or Details</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search system logs..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Log Level</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="">All Levels</option>
                <option value="info">INFO</option>
                <option value="warning">WARNING</option>
                <option value="error">ERROR</option>
              </select>
            </div>
            
            <div className="md:col-span-1 flex justify-end">
              <Button 
                variant="ghost" 
                className="h-10 px-3 w-full border border-transparent hover:bg-muted/50 text-muted-foreground disabled:opacity-50" 
                onClick={handleClearFilters}
                disabled={!(search || levelFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Logs Directory */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Logs...' : `System Activity (${filteredLogs.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Clock className="h-6 w-6 text-muted-foreground opacity-50" />
              </div>
              <h3 className="text-lg font-semibold">No operational logs found</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                No system activity matches your current filters.
              </p>
              <Button variant="outline" className="mt-4" onClick={handleClearFilters}>
                Clear all filters
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-transparent hover:bg-transparent">
                  <TableHead className="pl-6 w-[20%]">Timestamp</TableHead>
                  <TableHead className="w-[15%]">Level</TableHead>
                  <TableHead className="w-[20%]">Action</TableHead>
                  <TableHead className="w-[45%] pr-6">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.map((log, idx) => {
                  const levelStr = log.log_level || 'UNKNOWN';
                  return (
                    <TableRow key={log.id || idx} className="group hover:bg-muted/30">
                      <TableCell className="pl-6 text-xs text-muted-foreground whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5" />
                          {log.created_at ? format(new Date(log.created_at), 'MMM d, yyyy HH:mm:ss') : 'Unknown Time'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={`uppercase text-[10px] tracking-wider ${getLogLevelBg(levelStr)}`}>
                          {levelStr}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-sm truncate" title={log.action || 'Unknown Action'}>
                          {log.action || 'Unknown Action'}
                        </div>
                        {log.ip_address && (
                          <div className="text-[10px] font-mono text-muted-foreground mt-0.5">
                            IP: {log.ip_address}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="pr-6">
                        <div className="text-sm text-muted-foreground line-clamp-2" title={log.details || 'No details provided'}>
                          {log.details || 'No details provided'}
                        </div>
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
