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

export const DEPENDENCY_CATEGORIES = Object.freeze({
  materials: ['Semiconductors', 'Batteries', 'Copper', 'Steel', 'Aluminum', 'Lithium', 'Plastics', 'Other', 'None'],
  fuel_energy: ['Petrol', 'Diesel', 'Natural Gas', 'Electricity', 'Coal', 'Other', 'None'],
  logistics: ['Road', 'Rail', 'Sea', 'Air', 'Ports', 'Warehousing', 'Other', 'None'],
  technology: ['Cloud Services', 'Semiconductors', 'Telecom', 'Data Centers', 'Other', 'None'],
  geographic_exposure: ['India', 'China', 'Southeast Asia', 'Europe', 'North America', 'Middle East', 'Other', 'None'],
});

export const DEPENDENCY_LABELS = Object.freeze({
  materials: 'Key Materials',
  fuel_energy: 'Fuel & Energy',
  logistics: 'Logistics',
  technology: 'Technology',
  geographic_exposure: 'Geographic Exposure',
});

export const INDUSTRIES = Object.freeze([
  'Consumer Electronics',
  'Automotive',
  'Aerospace',
  'Chemicals',
  'Construction',
  'Energy',
  'Food & Beverage',
  'Healthcare',
  'Logistics',
  'Manufacturing',
  'Retail',
  'Technology',
  'Other',
]);

export function emptyDependencies() {
  return Object.fromEntries(
    Object.keys(DEPENDENCY_CATEGORIES).map((category) => [category, []]),
  );
}

export function toggleDependency(selected, category, value) {
  const current = new Set(selected[category] || []);
  if (value === 'None') {
    return { ...selected, [category]: current.has('None') ? [] : ['None'] };
  }
  current.delete('None');
  if (current.has(value)) current.delete(value);
  else current.add(value);
  return { ...selected, [category]: [...current] };
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

export const COMPANY_RELEVANCE_LABELS = Object.freeze({
  direct: 'Company Relevant',
  indirect: 'Company Relevant',
  no_identified_relevance: 'General Intelligence',
});

export function companyRelevanceLevel(row) {
  return row?.relevance?.relevance || 'no_identified_relevance';
}

export const CORRELATION_LEVEL_VARIANTS = {
  high_similarity: 'critical',
  moderate_similarity: 'high',
  limited_similarity: 'medium',
};

export function correlationLevelLabel(level) {
  const labels = {
    high_similarity: 'High similarity',
    moderate_similarity: 'Moderate similarity',
    limited_similarity: 'Limited similarity',
  };
  return labels[level] || 'Similarity';
}

export const RESPONSE_PLAN_SECTION_LABELS = {
  response_objective: 'Response Objective',
  immediate_checks: 'Immediate Checks',
  response_options: 'Response Options',
  information_required: 'Information Required',
  escalation_conditions: 'Escalation Conditions',
  responsible_areas: 'Responsible Areas',
};

/**
 * Response plan flow.
 *
 * A 404 from GET /investigations/risk/{id}/response-plan means "no plan has
 * been generated yet". That is an expected application state, not a failure,
 * so it must never be retried automatically and must never be shown as an
 * error. This module holds that decision logic as pure functions so it can be
 * tested without a DOM, matching the existing lib + node:test approach.
 */

/**
 * User-facing copy for the response plan pages.
 *
 * Kept in one ASCII-only module so the punctuation can be verified by tests
 * and cannot drift back to a mis-encoded em dash. Titles use a plain colon.
 */
export const RESPONSE_PLAN_TEXT = {
  title: 'Response Plan',
  subtitle: 'Structured response options for this risk',
  loading: 'Loading response plan...',
  generatingTitle: 'Generating Response Plan',
  generatingSubtitle: 'Analyzing the investigated risk and preparing response options...',
  empty: 'No response plan is available for this risk yet.',
  retry: 'Retry',
  objectiveSection: 'Response objective',
  optionsSection: 'Response options',
  optionsNote: 'Options for human review. None is ranked above another.',
  checksLabel: 'Checks',
  informationRequiredLabel: 'Information required',
  immediateChecksSection: 'Immediate checks',
  escalationSection: 'Escalation conditions',
  responsibleSection: 'Responsible areas',
  recommendationSection: 'Existing SupplySentry recommendation',
  disclaimer:
    'Decision-support template based on available SupplySentry intelligence. Options are provided for human review and do not constitute an automated business decision.',
};

/** Option titles, matching the backend templates. Plain ASCII punctuation. */
export const RESPONSE_PLAN_OPTION_TITLES = [
  'Option 1: Monitor and Verify',
  'Option 2: Reduce Near-Term Exposure',
  'Option 3: Escalate for Review',
];

/** User-facing copy for the risk resolution workflow. */
export const RESOLVE_RISK_TEXT = {
  action: 'Resolve Risk',
  confirmTitle: 'Resolve this risk?',
  confirmBody:
    'This will move the risk from active intelligence to Resolved Risks. Its investigation, ' +
    'response plan, correlations and supply-chain impact will remain available for historical review.',
  confirmAction: 'Resolve Risk',
  cancel: 'Cancel',
  reopen: 'Return to Active',
  readyHint:
    'Investigation and response plan are both complete, so this risk is ready to be resolved.',
  resolvedBadge: 'Resolved',
  pageTitle: 'Resolved Risks',
  pageSubtitle: 'Completed risk assessments retained for historical review.',
  empty: 'No risks have been resolved yet.',
};

/**
 * The Resolve Risk action is only offered once the server confirms the risk is
 * resolvable, which requires both the investigation and the response plan to
 * exist. Already-resolved risks are not offered the action again.
 */
export const canShowResolveAction = ({ status, resolvable }) => {
  const normalized = String(status || '').trim().toLowerCase();
  if (normalized === 'resolved') return false;
  return Boolean(resolvable);
};

export const isNotGeneratedError = (error) => {
  return error?.response?.status === 404;
};

/**
 * Repairs an option title.
 *
 * Plans persisted before the encoding fix can still carry the broken
 * "a€”" bytes. This normalises any such title to plain ASCII punctuation
 * on display, without changing the backend or rewriting stored records.
 */
export const formatResponseOptionTitle = (name, index) => {
  const cleaned = String(name || '')
    // Keep only printable ASCII, collapsing any stray separator bytes.
    .replace(/[^\x20-\x7E]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!cleaned) return RESPONSE_PLAN_OPTION_TITLES[index] || `Option ${index + 1}`;
  // Normalise "Option 1 - X" and similar to "Option 1: X".
  return cleaned.replace(/^(Option\s+\d+)\s*[-:]?\s*/i, '$1: ');
};

/**
 * Retry policy for the response plan GET, scoped to this endpoint only.
 *
 * 404 is an expected state, so it is never retried. Any other failure gets a
 * small, bounded number of attempts instead of the global default.
 */
export const responsePlanRetry = (failureCount, error) => {
  if (isNotGeneratedError(error)) return false;
  return failureCount < 2;
};

/** The POST response is the authoritative plan when it is complete. */
export const isCompleteResponsePlan = (plan) => {
  return Boolean(plan && typeof plan === 'object' && plan.response_objective);
};

/**
 * Decides whether generation should start.
 *
 * Exactly one POST may be started per risk, and only when the GET has
 * definitively reported that no plan exists.
 */
export const shouldStartGeneration = ({ enabled, querySettled, plan, error, alreadyStarted, isPending }) => {
  if (!enabled) return false;
  if (alreadyStarted || isPending) return false;
  if (plan) return false;
  if (!querySettled) return false;
  return isNotGeneratedError(error);
};

/**
 * In-flight POSTs, keyed by risk id.
 *
 * A plain ref resets when the component remounts, and React StrictMode mounts
 * twice in development. This tiny module-level set makes "exactly one
 * generation at a time" hold across remounts, StrictMode and navigation
 * without introducing broader application state.
 */
const inFlight = new Set();

export const isGenerationInFlight = (key) => inFlight.has(String(key));

/** Claims the slot for this risk. Returns false if a POST already owns it. */
export const claimGeneration = (key) => {
  const k = String(key);
  if (inFlight.has(k)) return false;
  inFlight.add(k);
  return true;
};

export const releaseGeneration = (key) => {
  inFlight.delete(String(key));
};

/** Test-only reset so suites do not leak state into one another. */
export const resetGenerationState = () => inFlight.clear();

/** Human-readable failure text, preferring the backend detail. */
export const responsePlanErrorMessage = (error) => {
  return error?.response?.data?.detail || 'The response plan could not be prepared. Please try again.';
};

export function responsePlanSectionLabel(key) {
  return RESPONSE_PLAN_SECTION_LABELS[key] || key;
}

export function isCompanyRelevant(row, level) {
  if (!level) return true;
  const current = companyRelevanceLevel(row);
  if (level === 'company_relevant') return current === 'direct' || current === 'indirect';
  return current === level;
}

export function companyRelevanceMatches(row) {
  return row?.relevance?.matched_dependencies || [];
}

/**
 * De-duplicated dependency values.
 *
 * The same value can legitimately exist under several company categories
 * (for example Semiconductors under both Materials and Technology). For the
 * end user that is a single supply-chain concern, so presentation shows it once.
 */
export function companyRelevanceValues(row) {
  const seen = new Set();
  const values = [];
  for (const match of companyRelevanceMatches(row)) {
    const value = match?.value;
    if (!value || seen.has(value)) continue;
    seen.add(value);
    values.push(value);
  }
  return values;
}

const AREA_BY_CATEGORY = {
  materials: 'materials supply',
  fuel_energy: 'fuel and energy supply',
  logistics: 'logistics',
  technology: 'technology supply',
  geographic_exposure: 'regional exposure',
};

function joinWords(items) {
  if (items.length <= 1) return items[0] || '';
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

function lowercaseFirst(value) {
  return value ? value.charAt(0).toLowerCase() + value.slice(1) : value;
}

/**
 * User-facing relevance sentence.
 *
 * Built only from information the relevance engine already returned: the
 * relevance level and the matched dependency values/categories. It never adds
 * impact that is not implied by those matches.
 */
export function companyRelevanceSentence(row) {
  const level = companyRelevanceLevel(row);
  const values = companyRelevanceValues(row);
  if (!values.length) {
    return 'No configured company dependency matches this event.';
  }
  const areas = [
    ...new Set(
      companyRelevanceMatches(row)
        .map((match) => AREA_BY_CATEGORY[match?.category])
        .filter(Boolean),
    ),
  ];
  const subject = joinWords(values);
  const areaText = areas.length
    ? ` to your ${joinWords(areas)}`
    : ' to your supply chain';
  if (level === 'direct') {
    return `Directly relevant to your ${subject}${areaText}.`;
  }
  if (level === 'indirect') {
    return `Potentially related to your ${subject}${areaText}, based on an indirect relationship rather than a direct match.`;
  }
  return `No configured company dependency currently matches this event. That means SupplySentry has no identified link to your ${subject} yet, not that it cannot affect you.`;
}

/** Short label used where a full sentence would be too verbose. */
export function companyRelevanceShortSentence(row) {
  const level = companyRelevanceLevel(row);
  const values = companyRelevanceValues(row);
  if (!values.length) return 'No identified company dependency match';
  const subject = joinWords(values.map(lowercaseFirst));
  if (level === 'direct') return `Direct company relevance · ${subject}`;
  if (level === 'indirect') return `Indirect company relevance · ${subject}`;
  return 'No identified company dependency match';
}

export function companyRelevanceSummary(eventRelevance) {
  return (eventRelevance || []).reduce(
    (totals, row) => {
      const level = companyRelevanceLevel(row);
      if (level === 'direct') totals.direct += 1;
      else if (level === 'indirect') totals.indirect += 1;
      else totals.none += 1;
      return totals;
    },
    { direct: 0, indirect: 0, none: 0 },
  );
}

export function companyRelevanceOptions() {
  return [
    { value: '', label: 'All Intelligence' },
    { value: 'company_relevant', label: 'Company Relevant' },
    { value: 'direct', label: 'Direct' },
    { value: 'indirect', label: 'Indirect' },
  ];
}

// Groups dependencies by category and marks values configured in more than one
// category, so a value such as "Semiconductors" appearing under both Materials
// and Technology reads clearly instead of looking like a duplicate entry.
export function describeDependencySelections(dependencies) {
  return Object.entries(dependencies || {}).map(([category, values]) => {
    const items = (values || []).map((value) => ({
      value,
      categories: Object.entries(dependencies || {})
        .filter(([, list]) => (list || []).includes(value))
        .map(([otherCategory]) => otherCategory),
    }));
    return { category, label: DEPENDENCY_LABELS[category] || category, items };
  });
}
