import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ArrowLeft, Lightbulb, Calendar, BrainCircuit } from 'lucide-react';
import { format } from 'date-fns';

const fetchRecommendationDetails = async (id) => {
  const recRes = await api.get(`/recommendations/${id}`);
  const recommendation = recRes.data;

  // Fetch associated prediction if available
  let prediction = null;
  if (recommendation.prediction_id) {
    try {
      const predRes = await api.get(`/predictions/${recommendation.prediction_id}`);
      prediction = predRes.data;
    } catch (err) {
      console.warn("Could not fetch associated prediction", err);
    }
  }

  return {
    ...recommendation,
    prediction
  };
};

export default function RecommendationDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: recommendation, isLoading, isError, error } = useQuery({
    queryKey: ['recommendation', id],
    queryFn: () => fetchRecommendationDetails(id),
  });

  if (isError) {
    return (
      <div className="p-8 text-center">
        <Lightbulb className="mx-auto h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold text-destructive">Failed to load recommendation details</h2>
        <p className="text-muted-foreground mt-2">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/recommendations')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Recommendations
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/recommendations')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Mitigation Strategy</h2>
          <p className="text-muted-foreground">Actionable steps and related AI forecast context.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Recommendation Info */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl">
                    {isLoading ? <Skeleton className="h-8 w-[300px]" /> : recommendation?.recommendation_title}
                  </CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-4">
                    {isLoading ? (
                      <Skeleton className="h-4 w-[200px]" />
                    ) : (
                      <>
                        <span className="text-sm font-mono text-muted-foreground flex items-center gap-1">
                          ID: #{recommendation?.id}
                        </span>
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Created: {recommendation?.created_at ? format(new Date(recommendation.created_at), 'MMM d, yyyy') : 'Unknown'}
                        </span>
                      </>
                    )}
                  </CardDescription>
                </div>
                {!isLoading && <PriorityBadge priority={recommendation?.priority} />}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Recommended Action</h3>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-[80%]" />
                  </div>
                ) : (
                  <div className="p-4 bg-muted/30 rounded-lg border">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{recommendation?.recommendation_text}</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 border-t pt-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Implementation Status</h4>
                  <div className="mt-1">
                    {isLoading ? <Skeleton className="h-6 w-24" /> : <Badge variant={recommendation?.status?.toLowerCase() === 'implemented' ? 'default' : 'secondary'}>{recommendation?.status}</Badge>}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Last Updated</h4>
                  <div className="text-sm mt-2">
                    {isLoading ? <Skeleton className="h-5 w-24" /> : (recommendation?.updated_at ? format(new Date(recommendation.updated_at), 'PPp') : 'Never')}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar / AI Prediction Context */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BrainCircuit className="h-5 w-5" /> Triggering Prediction</CardTitle>
              <CardDescription>The AI forecast that generated this recommendation.</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : recommendation?.prediction ? (
                <div 
                  className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/predictions/${recommendation.prediction.id}`)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium line-clamp-1">{recommendation.prediction.predicted_risk}</h4>
                  </div>
                  <div className="flex flex-col gap-2 text-xs text-muted-foreground mt-3">
                    <div className="flex justify-between border-b pb-1">
                      <span>Predicted Severity</span>
                      <span className="font-medium">{recommendation.prediction.predicted_severity}</span>
                    </div>
                    <div className="flex justify-between border-b pb-1">
                      <span>Confidence</span>
                      <span className="font-medium text-primary">{recommendation.prediction.confidence_score != null ? Number(recommendation.prediction.confidence_score).toFixed(4) : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>AI Model</span>
                      <span className="font-medium">{recommendation.prediction.prediction_model}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 border border-dashed rounded-lg text-center text-muted-foreground text-sm">
                  No linked prediction information available.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function PriorityBadge({ priority }) {
  if (!priority) return <Badge variant="outline">Unknown</Badge>;
  const lower = priority.toLowerCase();
  if (lower === 'high' || lower === 'critical') return <Badge variant="destructive">{priority}</Badge>;
  if (lower === 'medium') return <Badge variant="default" className="bg-orange-500 hover:bg-orange-600">{priority}</Badge>;
  if (lower === 'low') return <Badge variant="secondary">{priority}</Badge>;
  return <Badge variant="outline">{priority}</Badge>;
}
