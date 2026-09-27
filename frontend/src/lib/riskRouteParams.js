/**
 * Parsing of the risk id used by every risk-scoped route.
 *
 * The routes are declared as /risks/:id/... in App.jsx, so the URL parameter
 * is `id`. Anything that is not a positive integer becomes null, which is what
 * every page treats as "invalid route" and renders instead of requesting.
 *
 * This module deliberately has no imports so it stays testable on its own.
 */
export const parseRiskIdParam = (id) => {
  const riskId = Number(id);
  return Number.isInteger(riskId) && riskId > 0 ? riskId : null;
};

/**
 * Guard used by every request helper. It throws before any URL is built, so a
 * bad route can never produce a request containing "undefined".
 */
export const assertRiskId = (riskId) => {
  const value = Number(riskId);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error('A valid risk id is required.');
  }
  return value;
};
