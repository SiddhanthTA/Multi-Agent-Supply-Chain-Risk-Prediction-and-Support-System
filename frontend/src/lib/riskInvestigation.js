export const initialInvestigationState = Object.freeze({
  investigation: null,
  isLoading: false,
  error: '',
});

export function investigationReducer(state, action) {
  if (action.type === 'start') {
    return { investigation: null, isLoading: true, error: '' };
  }
  if (action.type === 'success') {
    return { investigation: action.investigation, isLoading: false, error: '' };
  }
  if (action.type === 'error') {
    return { investigation: null, isLoading: false, error: action.error };
  }
  return state;
}

export function investigationErrorMessage(error) {
  return (
    error?.response?.data?.detail ||
    error?.message ||
    'The investigation could not be generated. Please try again.'
  );
}

export const INVESTIGATION_SECTION_LABELS = Object.freeze({
  investigation_summary: 'Investigation Summary',
  why_this_matters: 'Why This Matters',
  supporting_evidence: 'Supporting Evidence',
  related_intelligence: 'Related Intelligence',
  what_to_investigate_next: 'What To Investigate Next',
});

export const INVESTIGATION_TYPE_LABELS = Object.freeze({
  fact: 'Platform fact',
  model_prediction: 'Model prediction',
  platform_recommendation: 'Platform recommendation',
  agent_interpretation: 'Agent interpretation',
});
