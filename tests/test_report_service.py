"""
Tests for the camp report aggregation service.

The most important case here is shared-payment allocation: `registration_payments` is
many-to-many, so a payment covering several campers must not be counted once per camper.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.extensions import db
from app.camp.models import (
    Camp,
    Category,
    Church,
    Financial,
    Food,
    FoodAllocation,
    Inventory,
    Payment,
    Pledge,
    Purchase,
    Registration,
    Room,
    RoomAllocation,
)
from app.camp.report_service import ReportService
from app.user.models import User


@pytest.fixture
def service():
    return ReportService()


@pytest.fixture
def user(db_session):
    manager = User(
        email='report-manager@example.com',
        full_name='Report Manager',
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
        name='Report Test Camp',
        start_date=datetime.now(timezone.utc).date(),
        end_date=datetime.now(timezone.utc).date() + timedelta(days=4),
        location='Test Grounds',
        base_fee=Decimal('500.00'),
        capacity=10,
        description='Camp used for report tests',
        registration_deadline=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def church(db_session, camp):
    record = Church(
        name='Test Church',
        district='Test District',
        area='Test Area',
        region='Test Region',
        camp_id=camp.id,
    )
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


def make_registration(camp, church, category, **overrides):
    """Create and persist a registration with sensible defaults."""
    values = {
        'surname': 'Doe',
        'middle_name': '',
        'last_name': 'Camper',
        'age': 20,
        'sex': 'male',
        'email': 'camper@example.com',
        'phone_number': '0200000000',
        'emergency_contact_name': 'Next Of Kin',
        'emergency_contact_phone': '0244444444',
        'church_id': church.id,
        'category_id': category.id,
        'total_amount': Decimal('500.00'),
        'has_paid': False,
        'has_checked_in': False,
        'camp_id': camp.id,
    }
    values.update(overrides)
    record = Registration(**values)
    db.session.add(record)
    db.session.commit()
    return record


def make_payment(camp, user, amount, registrations, channel='cash'):
    """Create a payment linked to one or more registrations."""
    record = Payment(
        amount=Decimal(str(amount)),
        payment_channel=channel,
        recorded_by=user.id,
        camp_id=camp.id,
    )
    db.session.add(record)
    db.session.flush()
    for registration in registrations:
        record.registrations.append(registration)
    db.session.commit()
    return record


def make_room(camp, number, capacity=2, extra_beds=0, damaged=False, gender='male',
              hostel='Hostel A'):
    record = Room(
        hostel_name=hostel,
        block='A',
        room_number=number,
        room_capacity=capacity,
        extra_beds=extra_beds,
        room_gender=gender,
        is_damaged=damaged,
        camp_id=camp.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


class TestEmptyCamp:
    def test_camp_with_no_data_returns_zeroed_report(self, service, camp):
        report = service.get_camp_report(camp.id)

        assert report is not None
        assert report['summary']['total_registered'] == 0
        # Every rate guards its denominator rather than raising ZeroDivisionError.
        assert report['summary']['check_in_rate'] == 0.0
        assert report['summary']['no_show_rate'] == 0.0
        assert report['summary']['collection_rate'] == 0.0
        assert report['accommodation']['occupancy_rate'] == 0.0
        assert report['pledges']['fulfillment_rate'] == 0.0
        assert report['food']['coverage_rate'] == 0.0
        assert report['demographics']['age_median'] == 0.0

    def test_missing_camp_returns_none(self, service, camp):
        assert service.get_camp_report('does-not-exist') is None


class TestPaymentAllocation:
    def test_shared_payment_is_not_double_counted(
        self, service, camp, church, category, user
    ):
        """
        One GHS 1000 payment covering two GHS 500 campers settles both, and camp
        revenue stays 1000 - not 2000.
        """
        first = make_registration(camp, church, category)
        second = make_registration(camp, church, category)
        make_payment(camp, user, 1000, [first, second])

        report = service.get_camp_report(camp.id)
        payments = report['payments']

        assert payments['collected_total'] == 1000.00
        assert payments['expected_total'] == 1000.00
        assert payments['outstanding_total'] == 0.00
        assert payments['fully_paid_count'] == 2
        assert payments['unpaid_count'] == 0
        assert report['data_quality']['shared_payments_detected'] == 1

    def test_shared_payment_splits_proportionally_to_amount_owed(
        self, service, camp, church, category, user
    ):
        """A camper owing twice as much absorbs twice the share of a shared payment."""
        big = make_registration(camp, church, category, total_amount=Decimal('800.00'))
        small = make_registration(camp, church, category, total_amount=Decimal('400.00'))
        # 600 against 1200 owed -> big gets 400, small gets 200; both half-paid.
        make_payment(camp, user, 600, [big, small])

        report = service.get_camp_report(camp.id)
        payments = report['payments']

        assert payments['collected_total'] == 600.00
        assert payments['expected_total'] == 1200.00
        assert payments['outstanding_total'] == 600.00
        assert payments['partially_paid_count'] == 2
        assert payments['fully_paid_count'] == 0

    def test_single_registration_payment_allocates_fully(
        self, service, camp, church, category, user
    ):
        registration = make_registration(camp, church, category)
        make_payment(camp, user, 500, [registration])

        report = service.get_camp_report(camp.id)

        assert report['payments']['fully_paid_count'] == 1
        assert report['payments']['outstanding_total'] == 0.00
        assert report['data_quality']['shared_payments_detected'] == 0

    def test_partial_and_unpaid_are_distinguished(
        self, service, camp, church, category, user
    ):
        partial = make_registration(camp, church, category)
        make_registration(camp, church, category)  # never pays
        make_payment(camp, user, 200, [partial])

        payments = service.get_camp_report(camp.id)['payments']

        assert payments['partially_paid_count'] == 1
        assert payments['unpaid_count'] == 1
        assert payments['fully_paid_count'] == 0
        assert payments['outstanding_total'] == 800.00

    def test_has_paid_flag_disagreeing_with_records_is_flagged(
        self, service, camp, church, category
    ):
        """Camper marked paid by hand but with no payment recorded."""
        make_registration(camp, church, category, has_paid=True)

        payments = service.get_camp_report(camp.id)['payments']

        assert payments['has_paid_flag_true'] == 1
        assert payments['unpaid_count'] == 1
        assert payments['flag_mismatch_count'] == 1

    def test_payment_linked_to_nothing_is_reported(self, service, camp, user):
        make_payment(camp, user, 300, [])

        report = service.get_camp_report(camp.id)

        assert report['data_quality']['payments_not_linked_to_any_registration'] == 1
        # Still counts toward camp revenue - the money did come in.
        assert report['payments']['collected_total'] == 300.00

    def test_channel_breakdown_totals_match(
        self, service, camp, church, category, user
    ):
        first = make_registration(camp, church, category)
        second = make_registration(camp, church, category)
        make_payment(camp, user, 200, [first], channel='momo')
        make_payment(camp, user, 300, [second], channel='cash')

        channels = {
            row['channel']: row for row in service.get_camp_report(camp.id)['payments']['by_channel']
        }

        assert channels['momo']['amount'] == 200.00
        assert channels['cash']['amount'] == 300.00


class TestAttendance:
    def test_check_in_and_no_show_rates(self, service, camp, church, category):
        make_registration(camp, church, category, has_checked_in=True)
        make_registration(camp, church, category, has_checked_in=True)
        make_registration(camp, church, category, has_checked_in=False)
        make_registration(camp, church, category, has_checked_in=False)

        summary = service.get_camp_report(camp.id)['summary']

        assert summary['total_registered'] == 4
        assert summary['total_checked_in'] == 2
        assert summary['check_in_rate'] == 50.0
        assert summary['no_show_count'] == 2
        assert summary['no_show_rate'] == 50.0

    def test_over_capacity_is_not_clamped(self, service, camp, church, category):
        """Camp capacity is 10; 12 registrations should read as 120%."""
        for _ in range(12):
            make_registration(camp, church, category)

        summary = service.get_camp_report(camp.id)['summary']

        assert summary['capacity_utilization'] == 120.0


class TestAccommodation:
    def test_damaged_rooms_excluded_from_beds_but_counted(self, service, camp):
        make_room(camp, '101', capacity=4)
        make_room(camp, '102', capacity=4, damaged=True)

        accommodation = service.get_camp_report(camp.id)['accommodation']

        assert accommodation['total_rooms'] == 2
        assert accommodation['usable_rooms'] == 1
        assert accommodation['damaged_rooms'] == 1
        assert accommodation['total_beds'] == 4

    def test_extra_beds_included_in_capacity(self, service, camp):
        make_room(camp, '201', capacity=4, extra_beds=2)

        accommodation = service.get_camp_report(camp.id)['accommodation']

        assert accommodation['base_beds'] == 4
        assert accommodation['extra_beds'] == 2
        assert accommodation['total_beds'] == 6

    def test_inactive_allocations_excluded_from_occupancy(
        self, service, camp, church, category, user
    ):
        room = make_room(camp, '301', capacity=4)
        active_reg = make_registration(camp, church, category)
        moved_reg = make_registration(camp, church, category)

        db.session.add(RoomAllocation(
            room_id=room.id, registration_id=active_reg.id, camp_id=camp.id,
            allocated_by=user.id, is_active=True,
        ))
        db.session.add(RoomAllocation(
            room_id=room.id, registration_id=moved_reg.id, camp_id=camp.id,
            allocated_by=user.id, is_active=False,
        ))
        db.session.commit()

        accommodation = service.get_camp_report(camp.id)['accommodation']

        assert accommodation['allocated_beds'] == 1
        assert accommodation['occupancy_rate'] == 25.0
        assert accommodation['unallocated_campers'] == 1

    def test_checked_in_without_bed_is_flagged(
        self, service, camp, church, category
    ):
        make_registration(camp, church, category, has_checked_in=True)
        make_registration(camp, church, category, has_checked_in=False)

        report = service.get_camp_report(camp.id)

        assert report['data_quality']['checked_in_without_bed'] == 1
        assert report['accommodation']['unallocated_campers'] == 2


class TestCategoriesAndDemographics:
    def test_discount_given_is_computed_against_base_fee(
        self, service, camp, church, db_session
    ):
        discounted = Category(
            name='Student', discount_percentage=Decimal('20.00'),
            discount_amount=Decimal('0.00'), camp_id=camp.id,
        )
        db.session.add(discounted)
        db.session.commit()

        # base_fee 500, 20% off -> 400 each
        make_registration(camp, church, discounted, total_amount=Decimal('400.00'))
        make_registration(camp, church, discounted, total_amount=Decimal('400.00'))

        row = service.get_camp_report(camp.id)['categories'][0]

        assert row['name'] == 'Student'
        assert row['count'] == 2
        assert row['expected_revenue'] == 800.00
        assert row['total_discount_given'] == 200.00
        assert row['share'] == 100.0

    def test_age_bands_and_sex_split(self, service, camp, church, category):
        make_registration(camp, church, category, age=10, sex='female')
        make_registration(camp, church, category, age=15, sex='female')
        make_registration(camp, church, category, age=30, sex='male')

        demographics = service.get_camp_report(camp.id)['demographics']
        bands = {row['band']: row['count'] for row in demographics['by_age_band']}
        sexes = {row['sex']: row['count'] for row in demographics['by_sex']}

        assert bands['Under 13'] == 1
        assert bands['13-17'] == 1
        assert bands['26-35'] == 1
        assert sexes['female'] == 2
        assert sexes['male'] == 1
        assert demographics['age_min'] == 10
        assert demographics['age_max'] == 30
        assert demographics['age_median'] == 15.0


class TestChurches:
    def test_church_spread_counts_registrations(
        self, service, camp, church, category, db_session
    ):
        other = Church(
            name='Second Church', district='Other District', area='Other Area',
            region='Other Region', camp_id=camp.id,
        )
        db.session.add(other)
        db.session.commit()

        make_registration(camp, church, category)
        make_registration(camp, church, category)
        make_registration(camp, other, category)

        churches = service.get_camp_report(camp.id)['churches']

        assert churches['total_churches_represented'] == 2
        assert churches['total_churches_registered'] == 2
        assert churches['by_church'][0]['name'] == 'Test Church'
        assert churches['by_church'][0]['count'] == 2
        districts = {row['district']: row['count'] for row in churches['by_district']}
        assert districts['Test District'] == 2
        assert districts['Other District'] == 1


class TestSoftDeletesAndLedger:
    def test_deleted_financials_excluded(self, service, camp, user):
        db.session.add(Financial(
            amount=Decimal('100.00'), received_by='Treasurer', transaction_type='income',
            transaction_category='offering', reference_number='REF-1',
            recorded_by=user.id, camp_id=camp.id, is_deleted=False,
        ))
        db.session.add(Financial(
            amount=Decimal('999.00'), received_by='Treasurer', transaction_type='income',
            transaction_category='offering', reference_number='REF-2',
            recorded_by=user.id, camp_id=camp.id, is_deleted=True,
        ))
        db.session.add(Financial(
            amount=Decimal('40.00'), received_by='Treasurer', transaction_type='expense',
            transaction_category='transport', reference_number='REF-3',
            recorded_by=user.id, camp_id=camp.id, is_deleted=False,
        ))
        db.session.commit()

        financials = service.get_camp_report(camp.id)['financials']

        assert financials['total_income'] == 100.00
        assert financials['total_expense'] == 40.00
        assert financials['net'] == 60.00
        assert financials['transaction_count'] == 2

    def test_deleted_inventory_excluded_and_stock_valued(self, service, camp):
        db.session.add(Inventory(
            cost=Decimal('50.00'), name='Shirt', inventory_type='shirts',
            quantity=10, camp_id=camp.id, is_deleted=False,
        ))
        db.session.add(Inventory(
            cost=Decimal('80.00'), name='Old Hoodie', inventory_type='hoodies',
            quantity=5, camp_id=camp.id, is_deleted=True,
        ))
        db.session.commit()

        inventory = service.get_camp_report(camp.id)['inventory']

        assert inventory['item_count'] == 1
        assert inventory['total_stock_value'] == 500.00

    def test_purchases_summarised_with_unsupplied_count(self, service, camp, user):
        db.session.add(Purchase(
            amount=Decimal('50.00'), items=[{'name': 'Shirt', 'quantity': 1}],
            sold_by=user.id, camp_id=camp.id, is_item_supplied=True,
        ))
        db.session.add(Purchase(
            amount=Decimal('75.00'), items=[{'name': 'Hoodie', 'quantity': 1}],
            sold_by=user.id, camp_id=camp.id, is_item_supplied=False,
        ))
        db.session.commit()

        sales = service.get_camp_report(camp.id)['inventory']['sales']

        assert sales['purchase_count'] == 2
        assert sales['total_sales'] == 125.00
        assert sales['unsupplied_count'] == 1


class TestPledgesAndFood:
    def test_pledge_fulfillment_totals(self, service, camp, church, category):
        registration = make_registration(camp, church, category)
        db.session.add(Pledge(
            amount=Decimal('1000.00'), fulfilled_amount=Decimal('250.00'),
            status='partial', camp_id=camp.id, camper_id=registration.id,
        ))
        db.session.add(Pledge(
            amount=Decimal('500.00'), fulfilled_amount=Decimal('500.00'),
            status='fulfilled', camp_id=camp.id, camper_id=registration.id,
        ))
        db.session.commit()

        pledges = service.get_camp_report(camp.id)['pledges']

        assert pledges['pledge_count'] == 2
        assert pledges['total_pledged'] == 1500.00
        assert pledges['total_fulfilled'] == 750.00
        assert pledges['total_outstanding'] == 750.00
        assert pledges['fulfillment_rate'] == 50.0
        assert pledges['fully_fulfilled_count'] == 1

    def test_food_coverage_counts_distinct_campers(
        self, service, camp, church, category, user
    ):
        served = make_registration(camp, church, category)
        make_registration(camp, church, category)  # never served

        food = Food(
            name='Jollof', quantity=100, vendor='Mama Kitchen',
            category='Lunch', camp_id=camp.id,
        )
        db.session.add(food)
        db.session.commit()

        # Same camper allocated twice must count once.
        for _ in range(2):
            db.session.add(FoodAllocation(
                food_id=food.id, registration_id=served.id,
                camp_id=camp.id, allocated_by=user.id,
            ))
        db.session.commit()

        food_section = service.get_camp_report(camp.id)['food']

        assert food_section['total_meals_recorded'] == 1
        assert food_section['total_quantity'] == 100
        assert food_section['allocations_recorded'] == 2
        assert food_section['campers_served'] == 1
        assert food_section['coverage_rate'] == 50.0


class TestCampIsolation:
    def test_other_camps_data_is_excluded(
        self, service, camp, church, category, user, db_session
    ):
        other_camp = Camp(
            name='Other Camp',
            start_date=datetime.now(timezone.utc).date(),
            end_date=datetime.now(timezone.utc).date() + timedelta(days=2),
            location='Elsewhere', base_fee=Decimal('100.00'), capacity=5,
            registration_deadline=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.session.add(other_camp)
        db.session.commit()

        other_church = Church(name='Other Church', camp_id=other_camp.id)
        other_category = Category(
            name='Other', discount_percentage=Decimal('0'),
            discount_amount=Decimal('0'), camp_id=other_camp.id,
        )
        db.session.add_all([other_church, other_category])
        db.session.commit()

        make_registration(camp, church, category)
        make_registration(other_camp, other_church, other_category,
                          total_amount=Decimal('100.00'))
        make_room(other_camp, '999', capacity=8)

        report = service.get_camp_report(camp.id)

        assert report['summary']['total_registered'] == 1
        assert report['summary']['expected_revenue'] == 500.00
        assert report['accommodation']['total_beds'] == 0
