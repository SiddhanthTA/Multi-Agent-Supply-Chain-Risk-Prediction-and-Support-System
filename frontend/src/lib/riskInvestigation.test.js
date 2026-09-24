import test from 'node:test';
import assert from 'node:assert/strict';
import {
  initialInvestigationState,
  investigationErrorMessage,
  investigationReducer,
} from './riskInvestigation.js';

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
