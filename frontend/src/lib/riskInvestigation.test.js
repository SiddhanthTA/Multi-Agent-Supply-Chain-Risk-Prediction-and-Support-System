import test from 'node:test';
import assert from 'node:assert/strict';
import { assertRiskId, parseRiskIdParam } from './riskRouteParams.js';

test('risk route parameter accepts real numeric ids', () => {
  assert.equal(parseRiskIdParam('1337'), 1337);
  assert.equal(parseRiskIdParam('1452'), 1452);
  assert.equal(parseRiskIdParam(1337), 1337);
});

test('risk route parameter rejects anything that is not a positive integer', () => {
  // These are exactly the values that previously produced "/risks/undefined".
  assert.equal(parseRiskIdParam(undefined), null);
  assert.equal(parseRiskIdParam(null), null);
  assert.equal(parseRiskIdParam(''), null);
  assert.equal(parseRiskIdParam('abc'), null);
  assert.equal(parseRiskIdParam('13.37'), null);
  assert.equal(parseRiskIdParam('0'), null);
  assert.equal(parseRiskIdParam('-5'), null);
});

test('assertRiskId blocks any request that would build a URL with undefined', () => {
  assert.equal(assertRiskId('1337'), 1337);
  for (const bad of [undefined, null, '', 'abc', 0, -1, NaN]) {
    assert.throws(() => assertRiskId(bad), /valid risk id/);
  }
});

test('an invalid id never produces a request URL', () => {
  // Mirrors what the pages do: bail out rather than call the helper.
  const riskId = parseRiskIdParam(undefined);
  const enabled = riskId != null;
  assert.equal(enabled, false);
  assert.equal(`${riskId}`, 'null');
});

import {
  RESPONSE_PLAN_OPTION_TITLES,
  RESPONSE_PLAN_TEXT,
  RESOLVE_RISK_TEXT,
  canShowResolveAction,
  claimGeneration,
  formatResponseOptionTitle,
  isCompleteResponsePlan,
  isGenerationInFlight,
  isNotGeneratedError,
  releaseGeneration,
  resetGenerationState,
  responsePlanErrorMessage,
  responsePlanRetry,
  shouldStartGeneration,
} from './riskInvestigation.js';

const notFound = { response: { status: 404 } };
const serverError = { response: { status: 500 } };
const plan = { response_objective: 'Reduce exposure' };

/** 1. Existing plan: nothing is generated. */
test('existing plan means no generation is started', () => {
  const start = shouldStartGeneration({
    enabled: true,
    querySettled: true,
    plan,
    error: null,
    alreadyStarted: false,
    isPending: false,
  });
  assert.equal(start, false);
});

/** 2. Missing plan: a settled 404 starts generation. */
test('a settled 404 means exactly one generation should start', () => {
  const start = shouldStartGeneration({
    enabled: true,
    querySettled: true,
    plan: undefined,
    error: notFound,
    alreadyStarted: false,
    isPending: false,
  });
  assert.equal(start, true);
});

test('generation does not start before the query settles, or without a 404', () => {
  const base = { enabled: true, plan: undefined, alreadyStarted: false, isPending: false };
  // Still in flight.
  assert.equal(shouldStartGeneration({ ...base, querySettled: false, error: null }), false);
  // A real failure must not silently trigger generation.
  assert.equal(shouldStartGeneration({ ...base, querySettled: true, error: serverError }), false);
  // Invalid route issues no request at all.
  assert.equal(
    shouldStartGeneration({ ...base, enabled: false, querySettled: true, error: notFound }),
    false,
  );
});

/** 3-5. Rerenders and remounts must not cause a duplicate POST. */
test('rerenders and remounts never start a second generation', () => {
  const base = {
    enabled: true,
    querySettled: true,
    plan: undefined,
    error: notFound,
    alreadyStarted: false,
    isPending: false,
  };
  // First render: allowed.
  assert.equal(shouldStartGeneration(base), true);
  // A later render in the same mount: blocked by the local flag.
  assert.equal(shouldStartGeneration({ ...base, alreadyStarted: true }), false);
  // A remount mid-flight: blocked by the shared in-flight marker.
  assert.equal(shouldStartGeneration({ ...base, isPending: true }), false);
  // A remount after a plan arrived: nothing to generate.
  assert.equal(shouldStartGeneration({ ...base, plan }), false);
});

test('the in-flight guard permits exactly one POST per risk', () => {
  resetGenerationState();
  assert.equal(isGenerationInFlight(1337), false);
  assert.equal(claimGeneration(1337), true);
  // A duplicate claim, from StrictMode or a remount, is refused.
  assert.equal(claimGeneration(1337), false);
  assert.equal(claimGeneration(1337), false);
  assert.equal(isGenerationInFlight(1337), true);
  // A different risk is unaffected.
  assert.equal(claimGeneration(1438), true);
  releaseGeneration(1337);
  assert.equal(isGenerationInFlight(1337), false);
  // After release, a deliberate Retry may claim the slot again.
  assert.equal(claimGeneration(1337), true);
  resetGenerationState();
});

/** 6. A complete POST body is used without another GET. */
test('a complete plan from POST is recognised', () => {
  assert.equal(isCompleteResponsePlan(plan), true);
  assert.equal(isCompleteResponsePlan({ status: 'ok' }), false);
  assert.equal(isCompleteResponsePlan(null), false);
  assert.equal(isCompleteResponsePlan(undefined), false);
});

/** 7. The 404 is an expected state, not an error. */
test('only a 404 counts as not-generated', () => {
  assert.equal(isNotGeneratedError(notFound), true);
  assert.equal(isNotGeneratedError(serverError), false);
  assert.equal(isNotGeneratedError(new Error('network')), false);
  assert.equal(isNotGeneratedError(null), false);
});

/** 8. No repeated GET: 404 is never retried, unlike real failures. */
test('a 404 GET is never retried, so it cannot poll in a loop', () => {
  // Every attempt number still returns false, which stops the query retrying.
  for (let attempt = 0; attempt < 5; attempt += 1) {
    assert.equal(responsePlanRetry(attempt, notFound), false);
  }
  // Genuine failures get a small, bounded number of attempts instead.
  assert.equal(responsePlanRetry(0, serverError), true);
  assert.equal(responsePlanRetry(1, serverError), true);
  assert.equal(responsePlanRetry(2, serverError), false);
});

/** 9. Failure text prefers the backend detail. */
test('failure messages use the backend detail when present', () => {
  assert.equal(
    responsePlanErrorMessage({ response: { data: { detail: 'Risk has no investigation.' } } }),
    'Risk has no investigation.',
  );
  assert.match(responsePlanErrorMessage(new Error('boom')), /could not be prepared/);
});

/** 10. Encoding: the option titles render as plain ASCII. */
test('option titles are normalised to plain ASCII punctuation', async () => {
  const { readFile } = await import('node:fs/promises');
  const source = await readFile(new URL('./riskInvestigation.js', import.meta.url), 'utf8');
  // No mis-encoded em dash may live in the copy module.
  assert.ok(!source.includes('\u00e2\u20ac\u201d'), 'no mojibake em dash in UI text');
  assert.ok(!source.includes('\u00e2\u0080'), 'no stray byte sequence in UI text');
  assert.deepEqual(RESPONSE_PLAN_OPTION_TITLES, [
    'Option 1: Monitor and Verify',
    'Option 2: Reduce Near-Term Exposure',
    'Option 3: Escalate for Review',
  ]);
  assert.equal(RESPONSE_PLAN_TEXT.title, 'Response Plan');
  assert.equal(RESPONSE_PLAN_TEXT.subtitle, 'Structured response options for this risk');
  assert.equal(RESPONSE_PLAN_TEXT.generatingTitle, 'Generating Response Plan');
});

test('stored plans with a mis-encoded title still render cleanly', () => {
  // Reproduces the bytes that were previously served to the browser.
  const stored = 'Option 1 \u00e2\u20ac\u201d Monitor and Verify';
  const shown = formatResponseOptionTitle(stored, 0);
  assert.ok(!shown.includes('\u00e2'), 'no mojibake survives into the UI');
  assert.equal(shown, 'Option 1: Monitor and Verify');
});

test('every separator style is normalised to the same title', () => {
  const expected = 'Option 2: Reduce Near-Term Exposure';
  for (const variant of [
    'Option 2: Reduce Near-Term Exposure',
    'Option 2 - Reduce Near-Term Exposure',
    'Option 2 \u00e2\u20ac\u201d Reduce Near-Term Exposure',
    'Option 2 \u2014 Reduce Near-Term Exposure',
  ]) {
    assert.equal(formatResponseOptionTitle(variant, 1), expected);
  }
});

import {
  DEPENDENCY_CATEGORIES,
  companyRelevanceLevel,
  companyRelevanceMatches,
  companyRelevanceOptions,
  companyRelevanceSummary,
  emptyDependencies,
  initialInvestigationState,
  investigationErrorMessage,
  investigationReducer,
  isCompanyRelevant,
  toggleDependency,
} from './riskInvestigation.js';

const directRow = {
  event_id: 1,
  relevance: {
    relevance: 'direct',
    matched_dependencies: [
      { category: 'materials', value: 'Semiconductors', matched_terms: ['chip'], matched_on: 'event_text' },
      { category: 'geographic_exposure', value: 'China', matched_terms: ['China'], matched_on: 'event_location' },
    ],
  },
};
const indirectRow = { event_id: 2, relevance: { relevance: 'indirect', matched_dependencies: [] } };
const generalRow = { event_id: 3, relevance: { relevance: 'no_identified_relevance', matched_dependencies: [] } };

test('company relevance level, matches and filters handle all three states', () => {
  assert.equal(companyRelevanceLevel(directRow), 'direct');
  assert.equal(companyRelevanceLevel(null), 'no_identified_relevance');
  assert.equal(companyRelevanceMatches(directRow).length, 2);
  assert.equal(companyRelevanceMatches(generalRow).length, 0);

  assert.equal(isCompanyRelevant(directRow, ''), true);
  assert.equal(isCompanyRelevant(directRow, 'company_relevant'), true);
  assert.equal(isCompanyRelevant(indirectRow, 'company_relevant'), true);
  assert.equal(isCompanyRelevant(generalRow, 'company_relevant'), false);
  assert.equal(isCompanyRelevant(indirectRow, 'direct'), false);
  assert.equal(isCompanyRelevant(directRow, 'direct'), true);
});

test('company relevance summary counts levels across events', () => {
  const totals = companyRelevanceSummary([directRow, indirectRow, generalRow, generalRow]);
  assert.equal(totals.direct, 1);
  assert.equal(totals.indirect, 1);
  assert.equal(totals.none, 2);
  assert.equal(companyRelevanceSummary(undefined).direct, 0);
});

test('company relevance filter options cover all, relevant, direct and indirect', () => {
  assert.deepEqual(
    companyRelevanceOptions().map((option) => option.value),
    ['', 'company_relevant', 'direct', 'indirect'],
  );
});

test('investigation state covers loading, success, and retryable errors', () => {
  const loading = investigationReducer(initialInvestigationState, { type: 'start' });
  assert.equal(loading.isLoading, true);
  assert.equal(loading.error, '');

  const success = investigationReducer(loading, {
    type: 'success',
    investigation: { sections: { investigation_summary: [] } },
  });
  assert.equal(success.isLoading, false);
  assert.equal(success.investigation.sections.investigation_summary.length, 0);

  const failed = investigationReducer(loading, { type: 'error', error: 'Unavailable' });
  assert.equal(failed.isLoading, false);
  assert.equal(failed.investigation, null);
  assert.equal(failed.error, 'Unavailable');
});

test('dependency selection supports multiple values and exclusive None', () => {
  const empty = emptyDependencies();
  assert.deepEqual(empty.materials, []);
  assert.deepEqual(DEPENDENCY_CATEGORIES.geographic_exposure.slice(-1), ['None']);

  const selected = toggleDependency(empty, 'materials', 'Semiconductors');
  const multi = toggleDependency(selected, 'materials', 'Batteries');
  assert.deepEqual(multi.materials, ['Semiconductors', 'Batteries']);

  const withNone = toggleDependency(multi, 'materials', 'None');
  assert.deepEqual(withNone.materials, ['None']);
  assert.deepEqual(toggleDependency(withNone, 'materials', 'Copper').materials, ['Copper']);
});

test('investigation errors use API detail and safe fallback', () => {
  assert.equal(
    investigationErrorMessage({ response: { data: { detail: 'Model unavailable' } } }),
    'Model unavailable',
  );
  assert.equal(
    investigationErrorMessage({}),
    'The investigation could not be generated. Please try again.',
  );
});

// --- Risk resolution lifecycle -------------------------------------------

test('Resolve Risk is offered only once the backend says the risk is resolvable', () => {
  // Investigation and response plan both exist -> the action is available.
  assert.equal(canShowResolveAction({ status: 'Active', resolvable: true }), true);
  // Not resolvable yet: missing investigation and/or response plan.
  assert.equal(canShowResolveAction({ status: 'Active', resolvable: false }), false);
  assert.equal(canShowResolveAction({ status: 'Active', resolvable: undefined }), false);
  assert.equal(canShowResolveAction({ status: 'Active' }), false);
});

test('an already resolved risk is never offered Resolve Risk again', () => {
  assert.equal(canShowResolveAction({ status: 'Resolved', resolvable: true }), false);
  assert.equal(canShowResolveAction({ status: 'resolved', resolvable: true }), false);
  assert.equal(canShowResolveAction({ status: 'RESOLVED', resolvable: true }), false);
});

test('resolution status matching is case insensitive for real stored values', () => {
  for (const status of ['Active', 'active', 'Pending', 'Inactive']) {
    assert.equal(canShowResolveAction({ status, resolvable: true }), true);
  }
});

test('the resolve confirmation explains that history is retained', () => {
  assert.equal(RESOLVE_RISK_TEXT.action, 'Resolve Risk');
  assert.equal(RESOLVE_RISK_TEXT.confirmTitle, 'Resolve this risk?');
  assert.equal(RESOLVE_RISK_TEXT.cancel, 'Cancel');
  // The confirmation must state that the intelligence is preserved.
  assert.match(RESOLVE_RISK_TEXT.confirmBody, /remain available for historical review/);
  assert.match(RESOLVE_RISK_TEXT.confirmBody, /investigation/);
  assert.match(RESOLVE_RISK_TEXT.confirmBody, /response plan/);
});
