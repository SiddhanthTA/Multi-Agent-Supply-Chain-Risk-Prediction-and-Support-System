import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ArrowLeft, BrainCircuit, Calendar, AlertTriangle, Lightbulb } from 'lucide-react';
import { format } from 'date-fns';

const fetchPredictionDetails = async (id) => {
  const predRes = await api.get(`/predictions/${id}`);
  const prediction = predRes.data;

  // Fetch associated risk if available
  let risk = null;
  if (prediction.risk_id) {
    try {
      const riskRes = await api.get(`/risks/${prediction.risk_id}`);
      risk = riskRes.data;
    } catch (err) {
      console.warn("Could not fetch associated risk", err);
    }
  }

  // Fetch related recommendations
  let recommendations = [];
  try {
    const recsRes = await api.get('/recommendations/');
    recommendations = recsRes.data.filter(r => r.prediction_id === parseInt(id));
  } catch (err) {
    console.warn("Could not fetch associated recommendations", err);
  }

  return {
    ...prediction,
    risk,
    recommendations
  };
};

export default function PredictionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: prediction, isLoading, isError, error } = useQuery({
    queryKey: ['prediction', id],
    queryFn: () => fetchPredictionDetails(id),
  });

  if (isError) {
    return (
      <div className="p-8 text-center">
        <BrainCircuit className="mx-auto h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load prediction details</h2>
        <p className="text-muted-foreground mt-2">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/predictions')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Predictions
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/predictions')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Prediction Details</h2>
          <p className="text-muted-foreground">AI-forecasted risk assessment and severity model output.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Prediction Info */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl">
                    {isLoading ? <Skeleton className="h-8 w-[300px]" /> : prediction?.predicted_risk}
                  </CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-4">
                    {isLoading ? (
                      <Skeleton className="h-4 w-[200px]" />
                    ) : (
                      <>
                        <span className="text-sm font-mono text-muted-foreground flex items-center gap-1">
                          ID: #{prediction?.id}
                        </span>
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Generated: {prediction?.created_at ? format(new Date(prediction.created_at), 'MMM d, yyyy') : 'Unknown'}
                        </span>
                      </>
                    )}
                  </CardDescription>
                </div>
                {!isLoading && <SeverityBadge severity={prediction?.predicted_severity} />}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-b pb-6">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Confidence Score</h4>
                  <div className="text-2xl font-bold text-primary">
                    {isLoading ? <Skeleton className="h-8 w-20" /> : (prediction?.confidence_score != null ? Number(prediction.confidence_score).toFixed(4) : 'N/A')}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">AI Model</h4>
                  <div className="mt-1">
                    {isLoading ? <Skeleton className="h-6 w-24" /> : <Badge variant="outline">{prediction?.prediction_model}</Badge>}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Status</h4>
                  <div className="mt-1">
                    {isLoading ? <Skeleton className="h-6 w-20" /> : <Badge variant="secondary">{prediction?.prediction_status}</Badge>}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Last Updated</h4>
                  <div className="text-sm mt-2">
                    {isLoading ? <Skeleton className="h-5 w-24" /> : (prediction?.updated_at ? format(new Date(prediction.updated_at), 'PPp') : 'Never')}
                  </div>
                </div>
              </div>

              {/* Related Risk Section */}
              <div>
                <h3 className="font-semibold mb-4 flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Base Risk Analyzed</h3>
                {isLoading ? (
                  <Skeleton className="h-24 w-full" />
                ) : prediction?.risk ? (
                  <div 
                    className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/risks/${prediction.risk.id}`)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium line-clamp-1">{prediction.risk.risk_name}</h4>
                      <SeverityBadge severity={prediction.risk.severity} />
                    </div>
                    <div className="flex gap-4 text-xs text-muted-foreground">
                      <span>Type: {prediction.risk.risk_type}</span>
                      <span>Score: {prediction.risk.risk_score != null ? `${Number(prediction.risk.risk_score).toFixed(2)}%` : '0%'}</span>
                      <span>Probability: {prediction.risk.probability != null ? `${Number(prediction.risk.probability).toFixed(2)}%` : 'N/A'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 border border-dashed rounded-lg text-center text-muted-foreground text-sm">
                    No linked risk information available.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar / AI Recommendations */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5" /> Generated Recommendations</CardTitle>
              <CardDescription>Mitigation strategies based on this prediction.</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : prediction?.recommendations?.length > 0 ? (
                <div className="space-y-4">
                  {prediction.recommendations.map(rec => (
                    <div 
                      key={rec.id} 
                      className="p-3 border rounded-lg bg-muted/10 cursor-pointer hover:bg-muted/30 transition-colors"
                      onClick={() => navigate(`/recommendations/${rec.id}`)}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-sm line-clamp-1" title={rec.recommendation_title}>{rec.recommendation_title}</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-2 flex justify-between items-center">
                        <Badge variant={rec.priority?.toLowerCase() === 'high' ? 'destructive' : 'outline'} className="text-[10px] h-5">
                          {rec.priority}
                        </Badge>
                        <span>{rec.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center p-6 border border-dashed rounded-lg text-muted-foreground text-sm">
                  No recommendations generated for this prediction.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }) {
  if (!severity) return <Badge variant="outline">Unknown</Badge>;
  const lower = severity.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="high">{severity}</Badge>;
  if (lower === 'medium') return <Badge variant="medium">{severity}</Badge>;
  if (lower === 'low') return <Badge variant="low">{severity}</Badge>;
  return <Badge variant="outline">{severity}</Badge>;
}
