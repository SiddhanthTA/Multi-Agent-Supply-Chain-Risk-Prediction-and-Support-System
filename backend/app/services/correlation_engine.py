from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.risk import Risk


def correlate_risks(
    db: Session,
):
    """
    Correlate all active risks and generate
    an overall supply chain assessment.
    """

    # Fetch all active risks
    active_risks = (
        db.query(Risk)
        .filter(Risk.status == "Active")
        .all()
    )

    # Group risks by location
    location_groups = defaultdict(list)

    for risk in active_risks:
        if risk.event:
            location_groups[risk.event.location].append(risk)

    # Store correlation results
    correlation_results = []

    # Process each location
    for location, risks in location_groups.items():

        # Unique risk categories
        categories = list({
            risk.risk_name
            for risk in risks
        })

        # Average risk score
        average_score = (
            sum(risk.risk_score for risk in risks)
            / len(risks)
        )

        # Determine overall risk level
        if average_score >= 80:
            overall_risk = "Critical"
        elif average_score >= 60:
            overall_risk = "High"
        elif average_score >= 40:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        # Save result
        correlation_results.append(
            {
                "location": location,
                "active_events": len(risks),
                "categories": categories,
                "overall_score": round(average_score, 2),
                "overall_risk": overall_risk,
            }
        )

    return correlation_results