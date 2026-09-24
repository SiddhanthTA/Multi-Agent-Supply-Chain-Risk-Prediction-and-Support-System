function eventTimestamp(event) {
  return event?.published_at || event?.received_at || event?.event_time || event?.created_at;
}

export function composeEventIntelligence(events = [], risks = [], predictions = [], recommendations = []) {
  const eventById = new Map(events.map((event) => [event.id, event]));
  const riskByEvent = new Map();
  const predictionByRisk = new Map();
  const recommendationByPrediction = new Map();

  risks.forEach((risk) => {
    const existing = riskByEvent.get(risk.event_id) || [];
    existing.push(risk);
    riskByEvent.set(risk.event_id, existing);
  });
  predictions.forEach((prediction) => {
    const existing = predictionByRisk.get(prediction.risk_id) || [];
    existing.push(prediction);
    predictionByRisk.set(prediction.risk_id, existing);
  });
  recommendations.forEach((recommendation) => {
    const existing = recommendationByPrediction.get(recommendation.prediction_id) || [];
    existing.push(recommendation);
    recommendationByPrediction.set(recommendation.prediction_id, existing);
  });

  return events.map((event) => {
    const eventRisks = riskByEvent.get(event.id) || [];
    const eventPredictions = eventRisks.flatMap((risk) => predictionByRisk.get(risk.id) || []);
    const eventRecommendations = eventPredictions.flatMap((prediction) => recommendationByPrediction.get(prediction.id) || []);
    const primaryRisk = [...eventRisks].sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0))[0] || null;
    const primaryPrediction = eventPredictions[0] || null;

    return {
      id: `event-${event.id}`,
      event,
      risks: eventRisks,
      predictions: eventPredictions,
      recommendations: eventRecommendations,
      primaryRisk,
      primaryPrediction,
      title: event.title || 'Untitled event',
      description: event.description || `${event.category || event.event_type || 'General'} event received from ${event.source || 'an available source'}.`,
      category: event.category || event.event_type || 'General',
      timestamp: eventTimestamp(event),
      href: primaryRisk ? `/risks/${primaryRisk.id}` : `/events/${event.id}`,
    };
  });
}

export function getEventForRisk(risk, events = []) {
  return eventById(events).get(risk?.event_id) || null;
}

function eventById(events) {
  return new Map(events.map((event) => [event.id, event]));
}
