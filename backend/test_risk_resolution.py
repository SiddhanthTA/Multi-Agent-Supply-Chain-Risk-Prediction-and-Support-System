"""Focused tests for the risk resolution lifecycle and the review-set metadata.

Resolution is a lifecycle state on the existing Risk.status field. These tests
prove that a risk cannot be resolved before both its investigation and its
response plan exist, that resolving never deletes or alters the original
assessment, and that ownership comes from the authenticated user only.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.risk import Risk
from app.models.event import Event
from app.models.risk_report import RiskReport, KIND_INVESTIGATION, KIND_RESPONSE_PLAN
from app.crud.risk import (
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    is_resolved,
    is_risk_resolvable,
    reopen_risk,
    resolve_risk,
    set_review_risks,
)
from app.crud.risk_report import get_report_kinds


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def make_risk(db, name="Risk"):
    event = Event(title=name, description="d", event_type="News",
                  location="India", category="Energy", source="Test")
    db.add(event)
    db.commit()
    risk = Risk(event_id=event.id, risk_name=name, risk_type="Supplier",
                risk_score=71.5, severity="High", probability=0.71,
                status=STATUS_ACTIVE)
    db.add(risk)
    db.commit()
    return risk


def add_report(db, risk, user_id, kind):
    db.add(RiskReport(risk_id=risk.id, user_id=user_id, kind=kind, payload={}))
    db.commit()


def test_a_new_risk_cannot_be_resolved(db):
    risk = make_risk(db)
    assert is_risk_resolvable(db, risk, 1) is False
    with pytest.raises(ValueError):
        resolve_risk(db, risk, 1)
    assert risk.status == STATUS_ACTIVE


def test_investigation_alone_is_not_enough(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_INVESTIGATION)
    assert is_risk_resolvable(db, risk, 1) is False
    with pytest.raises(ValueError):
        resolve_risk(db, risk, 1)


def test_response_plan_alone_is_not_enough(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_RESPONSE_PLAN)
    assert is_risk_resolvable(db, risk, 1) is False


def test_both_reports_required_then_resolve_succeeds(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_INVESTIGATION)
    add_report(db, risk, 1, KIND_RESPONSE_PLAN)
    assert is_risk_resolvable(db, risk, 1) is True

    original_score, original_severity = risk.risk_score, risk.severity
    resolve_risk(db, risk, 1)

    assert risk.status == STATUS_RESOLVED
    assert is_resolved(risk) is True
    # Resolution must not change the original assessment.
    assert risk.risk_score == original_score
    assert risk.severity == original_severity
    # And it must not delete the event, risk or reports.
    assert db.query(Event).filter(Event.id == risk.event_id).count() == 1
    assert db.query(Risk).filter(Risk.id == risk.id).count() == 1
    kinds = get_report_kinds(db, risk.id, 1)
    assert KIND_INVESTIGATION in kinds and KIND_RESPONSE_PLAN in kinds


def test_reports_are_scoped_to_the_requesting_user(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_INVESTIGATION)
    add_report(db, risk, 1, KIND_RESPONSE_PLAN)
    # A different user has no reports for this risk, so cannot resolve it.
    assert is_risk_resolvable(db, risk, 2) is False


def test_resolved_risk_cannot_be_resolved_again(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_INVESTIGATION)
    add_report(db, risk, 1, KIND_RESPONSE_PLAN)
    resolve_risk(db, risk, 1)
    assert is_risk_resolvable(db, risk, 1) is False


def test_reopen_returns_the_risk_to_active(db):
    risk = make_risk(db)
    add_report(db, risk, 1, KIND_INVESTIGATION)
    add_report(db, risk, 1, KIND_RESPONSE_PLAN)
    resolve_risk(db, risk, 1)
    reopen_risk(db, risk)
    assert risk.status == STATUS_ACTIVE
    assert is_resolved(risk) is False
    # Still resolvable, and history intact.
    assert is_risk_resolvable(db, risk, 1) is True
    assert get_report_kinds(db, risk.id, 1)


def test_review_set_is_metadata_only(db):
    first = make_risk(db, "First")
    second = make_risk(db, "Second")
    second.severity = "Low"
    db.commit()

    count = set_review_risks(db, [
        {"risk_id": first.id, "reason": "fuel case"},
        {"risk_id": second.id, "reason": "materials case"},
    ])
    assert count == 2
    # No risk was duplicated and the assessments are untouched.
    assert db.query(Risk).count() == 2
    assert first.severity == "High"
    assert second.severity == "Low"

    # Re-running replaces the set rather than accumulating duplicates.
    set_review_risks(db, [{"risk_id": first.id, "reason": "fuel case"}])
    assert db.query(Risk).count() == 2


def test_review_set_ignores_unknown_risk_ids(db):
    risk = make_risk(db)
    count = set_review_risks(db, [
        {"risk_id": risk.id, "reason": "ok"},
        {"risk_id": 999999, "reason": "missing"},
    ])
    assert count == 1
