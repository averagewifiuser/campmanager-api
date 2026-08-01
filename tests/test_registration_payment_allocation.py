"""
Tests for how a Registration totals up the payments linked to it.

`registration_payments` is many-to-many. The app's own create_payment() splits a
group payment into one Payment row per camper, so links are 1:1 in practice - but
the schema permits sharing, and a shared payment must not be counted in full
against every camper it touches.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.extensions import db
from app.camp.models import Camp, Category, Church, Payment, Registration
from app.user.models import User


@pytest.fixture
def user(db_session):
    manager = User(
        email='allocation-manager@example.com',
        full_name='Allocation Manager',
        role='camp_manager',
        permissions=[],
    )
    manager.set_password('password123')
    db.session.add(manager)
    db.session.commit()
    return manager


@pytest.fixture
def camp(db_session):
    record = Camp(
        name='Allocation Test Camp',
        start_date=datetime.now(timezone.utc).date(),
        end_date=datetime.now(timezone.utc).date() + timedelta(days=3),
        location='Test Grounds',
        base_fee=Decimal('500.00'),
        capacity=20,
        registration_deadline=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def church(db_session, camp):
    record = Church(name='Allocation Church', camp_id=camp.id)
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def category(db_session, camp):
    record = Category(
        name='Regular',
        discount_percentage=Decimal('0.00'),
        discount_amount=Decimal('0.00'),
        is_default=True,
        camp_id=camp.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


def make_registration(camp, church, category, total_amount='500.00'):
    record = Registration(
        surname='Doe',
        last_name='Camper',
        age=22,
        sex='female',
        phone_number='0200000000',
        emergency_contact_name='Next Of Kin',
        emergency_contact_phone='0244444444',
        church_id=church.id,
        category_id=category.id,
        total_amount=Decimal(total_amount),
        camp_id=camp.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


def make_payment(camp, user, amount, registrations):
    record = Payment(
        amount=Decimal(str(amount)),
        payment_channel='cash',
        recorded_by=user.id,
        camp_id=camp.id,
    )
    db.session.add(record)
    db.session.flush()
    for registration in registrations:
        record.registrations.append(registration)
    db.session.commit()
    return record


class TestSingleRegistrationPayments:
    """The 1:1 case the app actually produces - must keep working unchanged."""

    def test_payment_for_one_camper_counts_in_full(self, camp, church, category, user):
        registration = make_registration(camp, church, category)
        make_payment(camp, user, 500, [registration])

        assert registration.get_total_payments() == 500.00
        assert registration.get_outstanding_balance() == 0.00
        assert registration.is_fully_paid() is True

    def test_multiple_payments_for_one_camper_add_up(self, camp, church, category, user):
        registration = make_registration(camp, church, category)
        make_payment(camp, user, 200, [registration])
        make_payment(camp, user, 150, [registration])

        assert registration.get_total_payments() == 350.00
        assert registration.get_outstanding_balance() == 150.00
        assert registration.is_fully_paid() is False

    def test_camper_with_no_payments_owes_everything(self, camp, church, category):
        registration = make_registration(camp, church, category)

        assert registration.get_total_payments() == 0.00
        assert registration.get_outstanding_balance() == 500.00
        assert registration.is_fully_paid() is False


class TestSharedPayments:
    """A payment linked to several campers must be shared out, not duplicated."""

    def test_shared_payment_splits_between_two_campers(
        self, camp, church, category, user
    ):
        first = make_registration(camp, church, category)
        second = make_registration(camp, church, category)
        make_payment(camp, user, 1000, [first, second])

        assert first.get_total_payments() == 500.00
        assert second.get_total_payments() == 500.00
        assert first.is_fully_paid() is True
        assert second.is_fully_paid() is True

    def test_shared_payment_splits_in_proportion_to_what_each_owes(
        self, camp, church, category, user
    ):
        big = make_registration(camp, church, category, total_amount='800.00')
        small = make_registration(camp, church, category, total_amount='400.00')
        # 600 against 1200 owed -> big takes 400, small takes 200.
        make_payment(camp, user, 600, [big, small])

        assert big.get_total_payments() == 400.00
        assert small.get_total_payments() == 200.00
        assert big.get_outstanding_balance() == 400.00
        assert small.get_outstanding_balance() == 200.00

    def test_shared_payment_splits_evenly_when_nothing_is_owed(
        self, camp, church, category, user
    ):
        first = make_registration(camp, church, category, total_amount='0.00')
        second = make_registration(camp, church, category, total_amount='0.00')
        make_payment(camp, user, 300, [first, second])

        assert first.get_total_payments() == 150.00
        assert second.get_total_payments() == 150.00

    def test_camper_mixing_shared_and_own_payments(
        self, camp, church, category, user
    ):
        first = make_registration(camp, church, category)
        second = make_registration(camp, church, category)
        make_payment(camp, user, 400, [first, second])  # 200 each
        make_payment(camp, user, 300, [first])          # first only

        assert first.get_total_payments() == 500.00
        assert second.get_total_payments() == 200.00
        assert first.is_fully_paid() is True
        assert second.is_fully_paid() is False

    def test_to_dict_reports_the_shared_out_amount(
        self, camp, church, category, user
    ):
        first = make_registration(camp, church, category)
        second = make_registration(camp, church, category)
        make_payment(camp, user, 1000, [first, second])

        payload = first.to_dict(include_payments=True)

        assert payload['total_payments'] == 500.00
        assert payload['outstanding_balance'] == 0.00
        assert payload['is_fully_paid'] is True
