// Risk-scoped AI reports (investigation / response plan) and the
// deterministic read-only analyses that are reached from Risk Details.
//
// All of these are per risk and authenticated. Investigation and response plan
// are generated once and then retrieved; the analyses are always read-only.
import api from '@/services/api';
import { useParams } from 'react-router-dom';
import { assertRiskId, parseRiskIdParam } from './riskRouteParams';

export { assertRiskId, parseRiskIdParam };

/** Reads the current risk from the URL, which is the source of truth. */
export function useRiskIdParam() {
  return parseRiskIdParam(useParams().id);
}

export const fetchRiskReportStatus = async (riskId) => {
  const response = await api.get(`/investigations/risk/${assertRiskId(riskId)}/status`);
  return response.data;
};

export const fetchInvestigation = async (riskId) => {
  const response = await api.get(`/investigations/risk/${assertRiskId(riskId)}`);
  return response.data;
};

/** Generate the investigation only when one does not already exist. */
export const generateInvestigation = async (riskId) => {
  const response = await api.post(`/investigations/risk/${assertRiskId(riskId)}`);
  return response.data;
};

export const fetchResponsePlan = async (riskId) => {
  const response = await api.get(`/investigations/risk/${assertRiskId(riskId)}/response-plan`);
  return response.data;
};

/** Generate the response plan only when one does not already exist. */
export const generateResponsePlan = async (riskId) => {
  const response = await api.post(`/investigations/risk/${assertRiskId(riskId)}/response-plan`);
  return response.data;
};

export const fetchCorrelations = async (riskId) => {
  const response = await api.get(`/investigations/risk/${assertRiskId(riskId)}/correlations`);
  return response.data;
};

export const fetchImpactMap = async (riskId) => {
  const response = await api.get(`/investigations/risk/${assertRiskId(riskId)}/impact-map`);
  return response.data;
};

/** The full risk record plus its event, used as the header of every risk page. */
export const fetchRiskContext = async (riskId) => {
  const riskRes = await api.get(`/risks/${assertRiskId(riskId)}`);
  const risk = riskRes.data;
  let event = null;
  if (risk.event_id) {
    try {
      const eventRes = await api.get(`/events/${risk.event_id}`);
      event = eventRes.data;
    } catch {
      event = null;
    }
  }
  return { risk, event };
};

export const isNotGenerated = (error) => {
  return error?.response?.status === 404;
};

// ---------------------------------------------------------------------------
// Risk resolution and the curated review set
//
// Resolution is a lifecycle state on the server. Ownership always comes from
// the authenticated session: no user id is ever sent from the client.
// ---------------------------------------------------------------------------

/** Whether this risk can be resolved yet (needs investigation + response plan). */
export const fetchRiskResolution = async (riskId) => {
  const response = await api.get(`/risks/${assertRiskId(riskId)}/resolution`);
  return response.data;
};

export const resolveRisk = async (riskId) => {
  const response = await api.post(`/risks/${assertRiskId(riskId)}/resolve`);
  return response.data;
};

export const reopenRisk = async (riskId) => {
  const response = await api.post(`/risks/${assertRiskId(riskId)}/reopen`);
  return response.data;
};

/** Risks that completed the investigate -> plan -> resolve lifecycle. */
export const fetchResolvedRisks = async () => {
  const response = await api.get('/risks/resolved/list');
  return response.data;
};

/**
 * Risks currently surfaced for the active workspace.
 *
 * These are the risks SupplySentry has classified and prioritised from the
 * wider event stream. Resolved risks are excluded and listed separately.
 */
export const fetchCurrentRisks = async () => {
  const response = await api.get('/risks/review-set');
  return response.data;
};

// Rolling review window.
//
// The review and demo focus on the most recent intelligence. This is a
// presentation/query filter only: nothing is deleted, and omitting the
// parameter still returns the full history.
export const REVIEW_WINDOW_DAYS = 7;

export const recentParams = (days = REVIEW_WINDOW_DAYS) => ({ days });

// Mirrors the backend window for views that already hold the full list.
export const withinReviewWindow = (items, days = REVIEW_WINDOW_DAYS, field = 'created_at') => {
  if (!Array.isArray(items) || !items.length) return [];
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  return items.filter((item) => {
    const value = item?.[field];
    if (!value) return false;
    const time = new Date(value).getTime();
    return Number.isNaN(time) ? false : time >= cutoff;
  });
};
