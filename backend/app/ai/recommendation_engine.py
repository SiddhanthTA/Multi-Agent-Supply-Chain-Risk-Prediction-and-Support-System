from typing import Dict


RECOMMENDATION_RULES = {
    "Transportation": {
        "High": {
            "recommendation_type": "Transportation",
            "title": "Switch Transport Route",
            "description": "Use an alternate transport corridor or nearby port to minimize shipment delays.",
            "priority": "High",
        },
        "Medium": {
            "recommendation_type": "Transportation",
            "title": "Monitor Shipment Status",
            "description": "Track shipment progress closely and prepare alternate logistics if delays increase.",
            "priority": "Medium",
        },
        "Low": {
            "recommendation_type": "Transportation",
            "title": "Continue Monitoring",
            "description": "Transportation risk is currently low. Continue monitoring for any changes.",
            "priority": "Low",
        },
    },
    "Supplier": {
        "High": {
            "recommendation_type": "Supplier",
            "title": "Activate Backup Supplier",
            "description": "Immediately engage an approved backup supplier to prevent supply disruption.",
            "priority": "High",
        },
        "Medium": {
            "recommendation_type": "Supplier",
            "title": "Contact Supplier Immediately",
            "description": "Communicate with the supplier to assess the issue and prepare contingency plans.",
            "priority": "Medium",
        },
        "Low": {
            "recommendation_type": "Supplier",
            "title": "Monitor Supplier Performance",
            "description": "Continue monitoring supplier performance and delivery commitments.",
            "priority": "Low",
        },
    },
    "Natural Disaster": {
        "High": {
            "recommendation_type": "Natural Disaster",
            "title": "Increase Inventory and Reroute Shipments",
            "description": "Increase safety stock and reroute shipments away from affected regions.",
            "priority": "High",
        },
        "Medium": {
            "recommendation_type": "Natural Disaster",
            "title": "Monitor Weather Forecast",
            "description": "Track weather updates continuously and prepare mitigation plans.",
            "priority": "Medium",
        },
        "Low": {
            "recommendation_type": "Natural Disaster",
            "title": "Continue Monitoring",
            "description": "Current weather-related disruption risk is low. Continue monitoring.",
            "priority": "Low",
        },
    },
    "Financial": {
        "High": {
            "recommendation_type": "Financial",
            "title": "Review Procurement Budget",
            "description": "Review procurement spending and identify opportunities to reduce financial risk.",
            "priority": "High",
        },
        "Medium": {
            "recommendation_type": "Financial",
            "title": "Optimize Purchasing Plan",
            "description": "Optimize purchasing schedules and supplier contracts to reduce costs.",
            "priority": "Medium",
        },
        "Low": {
            "recommendation_type": "Financial",
            "title": "Continue Monitoring",
            "description": "Financial risk is currently low. Continue monitoring market conditions.",
            "priority": "Low",
        },
    },
    "Political": {
        "High": {
            "recommendation_type": "Political",
            "title": "Shift Procurement Region",
            "description": "Move procurement activities to a more stable region to reduce disruption.",
            "priority": "High",
        },
        "Medium": {
            "recommendation_type": "Political",
            "title": "Watch Regulatory Changes",
            "description": "Monitor policy and regulatory developments that may impact the supply chain.",
            "priority": "Medium",
        },
        "Low": {
            "recommendation_type": "Political",
            "title": "Continue Monitoring",
            "description": "Political risk is currently low. Continue monitoring regional developments.",
            "priority": "Low",
        },
    },
}


DEFAULT_RECOMMENDATION = {
    "recommendation_type": "General",
    "title": "Manual Review Required",
    "description": "No predefined recommendation is available. Please review this event manually.",
    "priority": "Medium",
}


def generate_recommendation(category: str, severity: str) -> Dict[str, str]:
    """
    Generate a recommendation based on the predicted
    risk category and severity.
    """

    if not category or not severity:
        return DEFAULT_RECOMMENDATION.copy()

    category = category.strip()
    severity = severity.strip().title()

    if category.lower() == "weather delay" and severity == "Low":
        return {
            "recommendation_type": "Weather",
            "title": "Normal Conditions",
            "description": "No active disruption detected for this weather observation. Continue monitoring routine operations and keep the site on normal operating status.",
            "priority": "Low",
        }

    return (
        RECOMMENDATION_RULES
        .get(category, {})
        .get(severity, DEFAULT_RECOMMENDATION)
        .copy()
    )


if __name__ == "__main__":
    test_cases = [
        ("Transportation", "High"),
        ("Supplier", "Medium"),
        ("Natural Disaster", "Low"),
        ("Financial", "High"),
        ("Political", "Medium"),
        ("Unknown", "High"),
    ]

    for category, severity in test_cases:
        print(f"\nCategory: {category}")
        print(f"Severity: {severity}")
        print(generate_recommendation(category, severity))