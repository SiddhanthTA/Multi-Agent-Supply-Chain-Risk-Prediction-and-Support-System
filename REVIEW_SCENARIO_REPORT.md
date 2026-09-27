# SupplySentry — Review Workspace

Updated for the final presentation workspace.

## Purpose

The review workspace surfaces the curated ReviewRisk population rather than the full historical Event/Risk tables. Historical intelligence remains intact in the database.

### Workspace rules

- Dashboard, Events, Risks and Intelligence Feed use the curated review population.
- India, United States, Global and All Locations are location-scoped.
- The U.S. review population is the only population with user-facing investigation, supply-chain impact, response-plan and correlation workflows.
- India and other locations remain visible as intelligence, but their presentation does not expose the U.S.-only View Risk workflow.
- Risk 396 (Colorado bear/garbage-truck story) is not part of the review population.
- Review explanations are versioned in backend/app/services/review_content.py and are tied to real stored Risk IDs.
- No Event, Risk, Prediction or Recommendation row is fabricated or rewritten by the review-content layer.
- Resolve Risk is available for curated U.S. review risks and changes only the existing Risk.status lifecycle state.

## Curated U.S. review risks

| Risk | Severity | Stored event |
|---:|---|---|
| 292 | High | GSME and Teradyne Announce Strategic Partnership |
| 436 | Medium | Trump Pushing for Diesel Export Ban Amid Surging Fuel Prices |
| 550 | High | A Trump diesel export ban is an Australian nightmare |
| 724 | Low | Iran turns to land trade as US blockade chokes ports and oil |
| 731 | High | Trump Backs Diesel Export Ban as Fuel Costs Continue Soaring |
| 1019 | High | Greek-operated air defense system shoots down missile in Saudi... |
| 1035 | Low | Nth Cycle signs $1bn recycled minerals supply deal with Glencore |
| 1265 | Medium | Where things stand after Iran's new pitch for a deal to open... |
| 1360 | Low | Why Unigrid’s Sodium-Ion Batteries Are the Game-Changer... |
| 1373 | Low | Roads flood in New Jersey, inundate some homes... |
| 1419 | Low | India seeks 2027 LPG imports from US via term tender... |

The stored severity values above are preserved. They are not rewritten merely to force a target distribution.

## Review content

For each retained U.S. risk, the review catalog contains event-specific:

1. Investigation Summary
2. Why This Matters
3. What To Investigate Next
4. Supply Chain Impact mappings
5. Response objective and response options
6. Curated correlations to other displayed U.S. risks

The correlation relationships are restricted to real risks in the displayed review population and include the actual related event title, severity and location from the database. They do not claim causation.

## Location-aware endpoints

- GET /events/review-set?location=...
- GET /risks/review-set?location=...
- Existing full historical endpoints remain available to backend/internal functionality.

## Resolution

A curated U.S. risk is considered review-complete for lifecycle purposes because its investigation and response-plan content are available from the versioned review catalog. Resolve Risk therefore works without requiring the old generated-report rows to be recreated.

Resolving a risk does not delete the event, risk, prediction, recommendation or review content.

## Data integrity

The review layer is presentation metadata/content. It does not alter the underlying Event/Risk/Prediction records.

