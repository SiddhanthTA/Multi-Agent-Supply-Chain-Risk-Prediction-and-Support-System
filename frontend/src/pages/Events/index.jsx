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
import { Search, X, ChevronLeft, ChevronRight, MapPin, Calendar, Activity, AlertTriangle, AlertCircle, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import { formatLocationDisplay } from '@/lib/locationDisplay';

const fetchEventsData = async () => {
  const [eventsRes, risksRes] = await Promise.all([
    api.get('/events/'),
    api.get('/risks/')
  ]);
  
  const risks = risksRes.data;
  
  return eventsRes.data.map(event => {
    const associatedRisk = risks.find(r => r.event_id === event.id);
    const displayLocation = formatLocationDisplay(event.location);
    return {
      ...event,
      displaySeverity: associatedRisk?.severity || 'Unknown',
      displayLocation: displayLocation.label,
      displayLocationSecondary: displayLocation.secondary,
    };
  });
};

export default function Events() {
  const navigate = useNavigate();
  const { data: events = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['eventsList'],
    queryFn: fetchEventsData,
  });

  // Filtering State
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Derive unique filter options from data
  const eventTypes = useMemo(() => [...new Set(events.map(e => e.event_type).filter(Boolean))], [events]);
  const severities = useMemo(() => [...new Set(events.map(e => e.displaySeverity).filter(Boolean))], [events]);
  const statuses = useMemo(() => [...new Set(events.map(e => e.status).filter(Boolean))], [events]);

  // Derived KPIs
  const kpis = useMemo(() => {
    if (!events.length) return null;
    const criticalHigh = events.filter(e => {
      const s = e.displaySeverity?.toLowerCase();
      return s === 'critical' || s === 'high';
    }).length;
    const active = events.filter(e => {
      const s = e.status?.toLowerCase();
      return s === 'active' || s === 'new' || s === 'in progress';
    }).length;
    return {
      total: events.length,
      critical: criticalHigh,
      active: active
    };
  }, [events]);

  // Apply filters
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      const matchesSearch = search === '' || 
        event.title?.toLowerCase().includes(search.toLowerCase()) || 
        event.description?.toLowerCase().includes(search.toLowerCase());
      
      const matchesType = typeFilter === '' || event.event_type === typeFilter;
      const matchesSeverity = severityFilter === '' || event.displaySeverity === severityFilter;
      const matchesStatus = statusFilter === '' || event.status === statusFilter;

      return matchesSearch && matchesType && matchesSeverity && matchesStatus;
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [events, search, typeFilter, severityFilter, statusFilter]);

  // Pagination logic
  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / itemsPerPage));
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredEvents.slice(start, start + itemsPerPage);
  }, [filteredEvents, currentPage]);

  const handleClearFilters = () => {
    setSearch('');
    setTypeFilter('');
    setSeverityFilter('');
    setStatusFilter('');
    setCurrentPage(1);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [search, typeFilter, severityFilter, statusFilter]);

  if (isError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load events</h2>
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
            <Activity className="h-8 w-8 text-primary" />
            Event Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">Monitor, filter, and analyze supply chain disruptions globally.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Total Monitored Events</h3>
            <div className="p-2 bg-primary/10 rounded-full">
              <Activity className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight">
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.total || 0}
          </div>
        </Card>
        
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Active Disruptions</h3>
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
            {isLoading ? <Skeleton className="h-8 w-16" /> : kpis?.critical || 0}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-lg">Filter Portfolio</CardTitle>
          <CardDescription>Narrow down events by severity, status, or keyword.</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Search Query</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search titles or descriptions..."
                  className="pl-9 bg-background/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="md:col-span-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">Event Type</label>
              <select 
                className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Types</option>
                {eventTypes.map(type => <option key={type} value={type}>{type}</option>)}
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
                disabled={!(search || typeFilter || severityFilter || statusFilter)}
              >
                <X className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between bg-muted/20 border-b border-border/50 py-4">
          <CardTitle className="text-base font-semibold">
            {isLoading ? 'Loading Events...' : `Event Directory (${filteredEvents.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No matching events</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                We couldn't find any events matching your current filters. Try broadening your search criteria.
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
                    <TableHead className="w-[45%] pl-6">Event Details</TableHead>
                    <TableHead className="w-[15%]">Location</TableHead>
                    <TableHead className="w-[15%]">Time</TableHead>
                    <TableHead className="w-[10%]">Status</TableHead>
                    <TableHead className="w-[15%] pr-6 text-right">Severity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedEvents.map(event => (
                    <TableRow 
                      key={event.id} 
                      className="cursor-pointer group"
                      onClick={() => navigate(`/events/${event.id}`)}
                    >
                      <TableCell className="pl-6">
                        <div className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1" title={event.title}>
                          {event.title}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                          <Badge variant="secondary" className="px-1.5 py-0 text-[10px] uppercase font-semibold tracking-wider">
                            {event.event_type}
                          </Badge>
                          <span className="truncate max-w-[200px] sm:max-w-[300px]" title={event.description}>
                            {event.description || 'No description available'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                          <MapPin className="h-3.5 w-3.5 shrink-0" />
                          <div className="flex flex-col">
                            <span className="line-clamp-1">{event.displayLocation}</span>
                            {event.displayLocationSecondary && (
                              <span className="text-[10px] text-muted-foreground">{event.displayLocationSecondary}</span>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                          <Calendar className="h-3.5 w-3.5 shrink-0" />
                          <span className="whitespace-nowrap">{event.event_time ? format(new Date(event.event_time), 'MMM d, yyyy') : 'Unknown'}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize whitespace-nowrap bg-background/50">
                          {event.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-6 text-right">
                        <SeverityBadge severity={event.displaySeverity} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between p-4 border-t border-border/50 bg-muted/10">
                  <p className="text-xs text-muted-foreground">
                    Showing <span className="font-medium text-foreground">{((currentPage - 1) * itemsPerPage) + 1}</span> to <span className="font-medium text-foreground">{Math.min(currentPage * itemsPerPage, filteredEvents.length)}</span> of <span className="font-medium text-foreground">{filteredEvents.length}</span> results
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
