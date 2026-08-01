"""
Camp report aggregation.

Builds the comprehensive end-of-camp report consumed by the web report page.
All aggregation happens here so the frontend needs a single request.

Note on payments: `registration_payments` is many-to-many, so a payment can cover
several campers. Such a payment is shared out across the registrations it covers in
proportion to what each owes, and camp-level revenue is taken from distinct payments
so nothing is counted twice.

This applies the same rule as `Registration.get_total_payments()`, but resolves the
whole camp in two queries instead of one per registration. If the allocation rule
changes, change it in both places.
"""

from collections import Counter, defaultdict, OrderedDict
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

from .models import (
    Camp,
    Category,
    Church,
    CustomField,
    Financial,
    Food,
    FoodAllocation,
    Inventory,
    Payment,
    Pledge,
    Purchase,
    Registration,
    RegistrationLink,
    Room,
    RoomAllocation,
    registration_payments,
)


AGE_BANDS = (
    ("Under 13", 0, 12),
    ("13-17", 13, 17),
    ("18-25", 18, 25),
    ("26-35", 26, 35),
    ("36-50", 36, 50),
    ("51+", 51, 200),
)

# Money below this is treated as settled, to absorb floating point drift from
# proportional payment allocation.
SETTLED_EPSILON = 0.01

# A free-text custom field can hold as many distinct answers as there are campers.
# Keep the top slice so one such field cannot flood the report.
MAX_CUSTOM_FIELD_OPTIONS = 25


def _round(value: float, places: int = 2) -> float:
    """Round, normalising -0.0 to 0.0 so reports never show a negative zero."""
    result = round(float(value or 0), places)
    return 0.0 if result == 0 else result


def _rate(numerator: float, denominator: float) -> float:
    """Percentage rounded to one decimal. Returns 0.0 when the denominator is zero."""
    if not denominator:
        return 0.0
    return _round((float(numerator) / float(denominator)) * 100, 1)


def _naive_utc(value: Any) -> Optional[datetime]:
    """Drop tzinfo so values loaded from SQLite compare against aware values safely."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return None


def _age_band(age: Optional[int]) -> str:
    if age is None:
        return "Unknown"
    for label, low, high in AGE_BANDS:
        if low <= age <= high:
            return label
    return "Unknown"


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return _round(ordered[midpoint], 1)
    return _round((ordered[midpoint - 1] + ordered[midpoint]) / 2, 1)


class ReportService:
    """Builds the full camp report payload."""

    def get_camp_report(self, camp_id: str) -> Optional[Dict[str, Any]]:
        """Return the complete report for a camp, or None when the camp is missing."""
        try:
            camp = Camp.query.filter_by(id=camp_id).first()
            if not camp:
                return None

            registrations = Registration.query.filter_by(camp_id=camp_id).all()
            payments = Payment.query.filter_by(camp_id=camp_id).all()
            churches = Church.query.filter_by(camp_id=camp_id).all()
            categories = Category.query.filter_by(camp_id=camp_id).all()
            links = RegistrationLink.query.filter_by(camp_id=camp_id).all()
            custom_fields = CustomField.query.filter_by(camp_id=camp_id).order_by(
                CustomField.order
            ).all()
            rooms = Room.query.filter_by(camp_id=camp_id).all()
            allocations = RoomAllocation.query.filter_by(camp_id=camp_id).all()
            pledges = Pledge.query.filter_by(camp_id=camp_id).all()
            financials = Financial.query.filter_by(
                camp_id=camp_id, is_deleted=False
            ).all()
            inventory = Inventory.query.filter_by(camp_id=camp_id, is_deleted=False).all()
            purchases = Purchase.query.filter_by(camp_id=camp_id).all()
            foods = Food.query.filter_by(camp_id=camp_id).all()
            food_allocations = FoodAllocation.query.filter_by(camp_id=camp_id).all()

            payment_links = self._payment_links([p.id for p in payments])
            allocated = self._allocate_payments(registrations, payments, payment_links)

            accommodation = self._accommodation(registrations, rooms, allocations)
            payments_section = self._payments(registrations, payments, allocated)

            return {
                "camp": self._camp(camp),
                "summary": self._summary(
                    camp, registrations, payments, accommodation, payments_section
                ),
                "registration": self._registration(camp, registrations, links),
                "demographics": self._demographics(registrations),
                "categories": self._categories(camp, registrations, categories, allocated),
                "custom_fields": self._custom_fields(registrations, custom_fields),
                "churches": self._churches(registrations, churches, allocated),
                "payments": payments_section,
                "accommodation": accommodation,
                "pledges": self._pledges(pledges),
                "financials": self._financials(financials),
                "inventory": self._inventory(inventory, purchases),
                "food": self._food(registrations, foods, food_allocations),
                "data_quality": self._data_quality(
                    registrations, payments, payment_links, allocations
                ),
            }

        except SQLAlchemyError as exc:
            current_app.logger.error(f"Database error in get_camp_report: {exc}")
            raise
        except Exception as exc:
            current_app.logger.error(f"Error in get_camp_report: {exc}")
            raise

    # ------------------------------------------------------------------
    # Payment allocation
    # ------------------------------------------------------------------

    def _payment_links(self, payment_ids: List[str]) -> Dict[str, List[str]]:
        """Map payment_id -> [registration_id]. One query rather than N lazy loads."""
        if not payment_ids:
            return {}

        links: Dict[str, List[str]] = defaultdict(list)
        # Chunk to stay clear of SQLite's variable limit on large camps.
        chunk_size = 500
        for start in range(0, len(payment_ids), chunk_size):
            chunk = payment_ids[start : start + chunk_size]
            rows = db.session.query(
                registration_payments.c.payment_id,
                registration_payments.c.registration_id,
            ).filter(registration_payments.c.payment_id.in_(chunk)).all()
            for payment_id, registration_id in rows:
                links[payment_id].append(registration_id)
        return links

    def _allocate_payments(
        self,
        registrations: List[Registration],
        payments: List[Payment],
        payment_links: Dict[str, List[str]],
    ) -> Dict[str, float]:
        """
        Allocate each payment across its linked registrations in proportion to what
        each camper owes, so a shared payment is never counted more than once.
        """
        owed = {r.id: float(r.total_amount or 0) for r in registrations}
        allocated = {r.id: 0.0 for r in registrations}

        for payment in payments:
            linked = [rid for rid in payment_links.get(payment.id, []) if rid in owed]
            if not linked:
                continue

            amount = float(payment.amount or 0)
            total_owed = sum(owed[rid] for rid in linked)

            if total_owed > 0:
                for rid in linked:
                    allocated[rid] += amount * (owed[rid] / total_owed)
            else:
                # Nothing owed to weight by - split evenly.
                share = amount / len(linked)
                for rid in linked:
                    allocated[rid] += share

        return allocated

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _camp(self, camp: Camp) -> Dict[str, Any]:
        return {
            "id": camp.id,
            "name": camp.name,
            "start_date": camp.start_date.isoformat() if camp.start_date else None,
            "end_date": camp.end_date.isoformat() if camp.end_date else None,
            "location": camp.location,
            "capacity": camp.capacity or 0,
            "base_fee": _round(camp.base_fee),
            "description": camp.description,
            "registration_deadline": (
                camp.registration_deadline.isoformat()
                if camp.registration_deadline
                else None
            ),
            "is_active": bool(camp.is_active),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _summary(
        self,
        camp: Camp,
        registrations: List[Registration],
        payments: List[Payment],
        accommodation: Dict[str, Any],
        payments_section: Dict[str, Any],
    ) -> Dict[str, Any]:
        total = len(registrations)
        checked_in = sum(1 for r in registrations if r.has_checked_in)
        no_shows = total - checked_in
        capacity = camp.capacity or 0

        return {
            "total_registered": total,
            "total_checked_in": checked_in,
            "check_in_rate": _rate(checked_in, total),
            "no_show_count": no_shows,
            "no_show_rate": _rate(no_shows, total),
            "capacity": capacity,
            "capacity_utilization": _rate(total, capacity),
            "expected_revenue": payments_section["expected_total"],
            "collected_revenue": payments_section["collected_total"],
            "collection_rate": _rate(
                payments_section["collected_total"], payments_section["expected_total"]
            ),
            "outstanding_balance": payments_section["outstanding_total"],
            "beds_available": accommodation["total_beds"],
            "beds_allocated": accommodation["allocated_beds"],
        }

    def _registration(
        self, camp: Camp, registrations: List[Registration], links: List[RegistrationLink]
    ) -> Dict[str, Any]:
        per_day: Counter = Counter()
        for reg in registrations:
            moment = _naive_utc(reg.registration_date)
            if moment:
                per_day[moment.date()] += 1

        by_date = []
        cumulative = 0
        for day in sorted(per_day):
            cumulative += per_day[day]
            by_date.append(
                {"date": day.isoformat(), "count": per_day[day], "cumulative": cumulative}
            )

        deadline = _naive_utc(camp.registration_deadline)
        after_deadline = 0
        if deadline:
            after_deadline = sum(
                1
                for r in registrations
                if (_naive_utc(r.registration_date) or datetime.min) > deadline
            )

        link_names = {link.id: link.name for link in links}
        link_counter: Counter = Counter()
        for reg in registrations:
            key = link_names.get(reg.registration_link_id, "Direct / staff entry")
            link_counter[key] += 1

        return {
            "by_date": by_date,
            "registrations_after_deadline": after_deadline,
            "by_link": [
                {"link_name": name, "count": count}
                for name, count in link_counter.most_common()
            ],
            "first_registration": by_date[0]["date"] if by_date else None,
            "last_registration": by_date[-1]["date"] if by_date else None,
        }

    def _demographics(self, registrations: List[Registration]) -> Dict[str, Any]:
        band_counter: Counter = Counter()
        sex_counter: Counter = Counter()
        ages: List[float] = []

        for reg in registrations:
            band_counter[_age_band(reg.age)] += 1
            sex_counter[(reg.sex or "unspecified")] += 1
            if reg.age is not None:
                ages.append(float(reg.age))

        band_order = [label for label, _, _ in AGE_BANDS] + ["Unknown"]

        return {
            "by_age_band": [
                {"band": band, "count": band_counter[band]}
                for band in band_order
                if band_counter[band]
            ],
            "by_sex": [
                {"sex": sex, "count": count} for sex, count in sex_counter.most_common()
            ],
            "age_min": int(min(ages)) if ages else 0,
            "age_max": int(max(ages)) if ages else 0,
            "age_average": _round(sum(ages) / len(ages), 1) if ages else 0.0,
            "age_median": _median(ages),
        }

    def _categories(
        self,
        camp: Camp,
        registrations: List[Registration],
        categories: List[Category],
        allocated: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        base_fee = float(camp.base_fee or 0)
        total_registrations = len(registrations)
        grouped: Dict[str, List[Registration]] = defaultdict(list)
        for reg in registrations:
            grouped[reg.category_id].append(reg)

        rows = []
        for category in categories:
            members = grouped.get(category.id, [])
            expected = sum(float(r.total_amount or 0) for r in members)
            collected = sum(allocated.get(r.id, 0.0) for r in members)
            rows.append(
                {
                    "name": category.name,
                    "count": len(members),
                    "share": _rate(len(members), total_registrations),
                    "discount_percentage": _round(category.discount_percentage),
                    "discount_amount": _round(category.discount_amount),
                    "expected_revenue": _round(expected),
                    "collected_revenue": _round(collected),
                    "total_discount_given": _round(base_fee * len(members) - expected),
                    "checked_in": sum(1 for r in members if r.has_checked_in),
                }
            )

        rows.sort(key=lambda row: row["count"], reverse=True)
        return rows

    def _custom_fields(
        self, registrations: List[Registration], custom_fields: List[CustomField]
    ) -> List[Dict[str, Any]]:
        """
        Per-option counts for each of the camp's own questions.

        Dropdown answers are a single value, checkbox answers a list - so for a
        checkbox the counts can exceed the number of campers, and `is_multi_select`
        flags that. Declared options nobody picked are kept at zero, because that
        is itself worth knowing. Free-text answers are counted by value, capped so
        a many-valued field cannot flood the report.
        """
        total = len(registrations)
        sections = []

        for field in custom_fields:
            counter: Counter = Counter()
            answered = 0

            for registration in registrations:
                responses = registration.custom_field_responses
                if not isinstance(responses, dict):
                    continue

                raw = responses.get(field.id)
                if isinstance(raw, list):
                    values = [str(v).strip() for v in raw if str(v).strip()]
                elif raw is None or isinstance(raw, bool):
                    values = [] if raw is None else [str(raw)]
                else:
                    text = str(raw).strip()
                    values = [text] if text else []

                if values:
                    answered += 1
                    counter.update(values)

            declared = field.options if isinstance(field.options, list) else []
            # Declared options first (so zeros survive), then anything unexpected.
            labels = list(
                dict.fromkeys(
                    [str(option) for option in declared] + list(counter.keys())
                )
            )

            options = [
                {
                    "option": label,
                    "count": counter.get(label, 0),
                    "share": _rate(counter.get(label, 0), total),
                }
                for label in labels
            ]
            options.sort(key=lambda row: (-row["count"], row["option"]))

            truncated = 0
            if len(options) > MAX_CUSTOM_FIELD_OPTIONS:
                truncated = len(options) - MAX_CUSTOM_FIELD_OPTIONS
                options = options[:MAX_CUSTOM_FIELD_OPTIONS]

            sections.append(
                {
                    "field_name": field.field_name,
                    "field_type": field.field_type,
                    "is_required": bool(field.is_required),
                    "is_multi_select": field.field_type == "checkbox",
                    "answered_count": answered,
                    "unanswered_count": total - answered,
                    "answered_rate": _rate(answered, total),
                    "options": options,
                    "options_truncated": truncated,
                }
            )

        return sections

    def _churches(
        self,
        registrations: List[Registration],
        churches: List[Church],
        allocated: Dict[str, float],
    ) -> Dict[str, Any]:
        church_map = {c.id: c for c in churches}
        grouped: Dict[str, List[Registration]] = defaultdict(list)
        for reg in registrations:
            grouped[reg.church_id].append(reg)

        by_church = []
        district_counter: Counter = Counter()
        area_counter: Counter = Counter()
        region_counter: Counter = Counter()

        for church_id, members in grouped.items():
            church = church_map.get(church_id)
            if church is None:
                name, district, area, region = "Unknown church", None, None, None
            else:
                name = church.name
                district, area, region = church.district, church.area, church.region

            by_church.append(
                {
                    "name": name,
                    "district": district,
                    "area": area,
                    "region": region,
                    "count": len(members),
                    "checked_in": sum(1 for r in members if r.has_checked_in),
                    "collected": _round(
                        sum(allocated.get(r.id, 0.0) for r in members)
                    ),
                }
            )

            district_counter[district or "Unspecified"] += len(members)
            area_counter[area or "Unspecified"] += len(members)
            region_counter[region or "Unspecified"] += len(members)

        by_church.sort(key=lambda row: row["count"], reverse=True)

        def spread(counter: Counter, key: str) -> List[Dict[str, Any]]:
            return [
                {key: label, "count": count} for label, count in counter.most_common()
            ]

        return {
            "total_churches_represented": len(grouped),
            "total_churches_registered": len(churches),
            "by_church": by_church,
            "by_district": spread(district_counter, "district"),
            "by_area": spread(area_counter, "area"),
            "by_region": spread(region_counter, "region"),
        }

    def _payments(
        self,
        registrations: List[Registration],
        payments: List[Payment],
        allocated: Dict[str, float],
    ) -> Dict[str, Any]:
        expected_total = sum(float(r.total_amount or 0) for r in registrations)
        # Camp revenue comes from distinct payments, never from summed allocations.
        collected_total = sum(float(p.amount or 0) for p in payments)

        fully_paid = partially_paid = unpaid = 0
        outstanding_total = 0.0
        flag_mismatch = 0

        for reg in registrations:
            owed = float(reg.total_amount or 0)
            paid = allocated.get(reg.id, 0.0)
            balance = owed - paid

            if balance <= SETTLED_EPSILON:
                fully_paid += 1
                is_settled = True
            elif paid > SETTLED_EPSILON:
                partially_paid += 1
                outstanding_total += balance
                is_settled = False
            else:
                unpaid += 1
                outstanding_total += balance
                is_settled = False

            if bool(reg.has_paid) != is_settled:
                flag_mismatch += 1

        channel_count: Counter = Counter()
        channel_amount: Dict[str, float] = defaultdict(float)
        for payment in payments:
            channel = payment.payment_channel or "unspecified"
            channel_count[channel] += 1
            channel_amount[channel] += float(payment.amount or 0)

        return {
            "expected_total": _round(expected_total),
            "collected_total": _round(collected_total),
            "outstanding_total": _round(outstanding_total),
            "collection_rate": _rate(collected_total, expected_total),
            "payment_count": len(payments),
            "fully_paid_count": fully_paid,
            "partially_paid_count": partially_paid,
            "unpaid_count": unpaid,
            "by_channel": [
                {
                    "channel": channel,
                    "count": count,
                    "amount": _round(channel_amount[channel]),
                }
                for channel, count in channel_count.most_common()
            ],
            "has_paid_flag_true": sum(1 for r in registrations if r.has_paid),
            "flag_mismatch_count": flag_mismatch,
        }

    def _accommodation(
        self,
        registrations: List[Registration],
        rooms: List[Room],
        allocations: List[RoomAllocation],
    ) -> Dict[str, Any]:
        active = [a for a in allocations if a.is_active]
        allocated_by_room: Counter = Counter(a.room_id for a in active)
        allocated_registration_ids = {a.registration_id for a in active}

        usable_rooms = [r for r in rooms if not r.is_damaged]
        damaged_rooms = [r for r in rooms if r.is_damaged]

        base_beds = sum(int(r.room_capacity or 0) for r in usable_rooms)
        extra_beds = sum(int(r.extra_beds or 0) for r in usable_rooms)
        total_beds = base_beds + extra_beds
        allocated_beds = len(active)

        hostel_stats: Dict[str, Dict[str, int]] = OrderedDict()
        gender_stats: Dict[str, Dict[str, int]] = OrderedDict()

        for room in usable_rooms:
            beds = int(room.room_capacity or 0) + int(room.extra_beds or 0)
            taken = allocated_by_room.get(room.id, 0)

            hostel = hostel_stats.setdefault(
                room.hostel_name or "Unspecified",
                {"rooms": 0, "beds": 0, "allocated": 0},
            )
            hostel["rooms"] += 1
            hostel["beds"] += beds
            hostel["allocated"] += taken

            gender = gender_stats.setdefault(
                room.room_gender or "unspecified",
                {"rooms": 0, "beds": 0, "allocated": 0},
            )
            gender["rooms"] += 1
            gender["beds"] += beds
            gender["allocated"] += taken

        unallocated = [
            r for r in registrations if r.id not in allocated_registration_ids
        ]

        return {
            "total_rooms": len(rooms),
            "usable_rooms": len(usable_rooms),
            "damaged_rooms": len(damaged_rooms),
            "special_rooms": sum(1 for r in rooms if r.is_special_room),
            "total_beds": total_beds,
            "base_beds": base_beds,
            "extra_beds": extra_beds,
            "allocated_beds": allocated_beds,
            "free_beds": max(0, total_beds - allocated_beds),
            "occupancy_rate": _rate(allocated_beds, total_beds),
            "unallocated_campers": len(unallocated),
            "by_hostel": [
                {
                    "hostel_name": name,
                    "rooms": stats["rooms"],
                    "beds": stats["beds"],
                    "allocated": stats["allocated"],
                    "occupancy_rate": _rate(stats["allocated"], stats["beds"]),
                }
                for name, stats in sorted(hostel_stats.items())
            ],
            "by_gender": [
                {
                    "room_gender": gender,
                    "rooms": stats["rooms"],
                    "beds": stats["beds"],
                    "allocated": stats["allocated"],
                    "occupancy_rate": _rate(stats["allocated"], stats["beds"]),
                }
                for gender, stats in sorted(gender_stats.items())
            ],
        }

    def _pledges(self, pledges: List[Pledge]) -> Dict[str, Any]:
        total_pledged = sum(float(p.amount or 0) for p in pledges)
        total_fulfilled = sum(float(p.fulfilled_amount or 0) for p in pledges)

        status_count: Counter = Counter()
        status_amount: Dict[str, float] = defaultdict(float)
        for pledge in pledges:
            status = pledge.status or "unspecified"
            status_count[status] += 1
            status_amount[status] += float(pledge.amount or 0)

        return {
            "pledge_count": len(pledges),
            "total_pledged": _round(total_pledged),
            "total_fulfilled": _round(total_fulfilled),
            "total_outstanding": _round(max(0.0, total_pledged - total_fulfilled)),
            "fulfillment_rate": _rate(total_fulfilled, total_pledged),
            "fully_fulfilled_count": sum(
                1
                for p in pledges
                if float(p.fulfilled_amount or 0) >= float(p.amount or 0)
            ),
            "by_status": [
                {
                    "status": status,
                    "count": count,
                    "amount": _round(status_amount[status]),
                }
                for status, count in status_count.most_common()
            ],
        }

    def _financials(self, financials: List[Financial]) -> Dict[str, Any]:
        total_income = sum(
            float(f.amount or 0) for f in financials if f.transaction_type == "income"
        )
        total_expense = sum(
            float(f.amount or 0) for f in financials if f.transaction_type == "expense"
        )

        grouped: Dict[Any, Dict[str, Any]] = OrderedDict()
        for record in financials:
            key = (record.transaction_type, record.transaction_category)
            row = grouped.setdefault(
                key,
                {
                    "transaction_type": record.transaction_type,
                    "transaction_category": record.transaction_category,
                    "count": 0,
                    "amount": 0.0,
                },
            )
            row["count"] += 1
            row["amount"] += float(record.amount or 0)

        by_category = sorted(
            grouped.values(), key=lambda row: row["amount"], reverse=True
        )
        for row in by_category:
            row["amount"] = _round(row["amount"])

        return {
            "transaction_count": len(financials),
            "total_income": _round(total_income),
            "total_expense": _round(total_expense),
            "net": _round(total_income - total_expense),
            "by_category": by_category,
        }

    def _inventory(
        self, inventory: List[Inventory], purchases: List[Purchase]
    ) -> Dict[str, Any]:
        items = [
            {
                "name": item.name,
                "inventory_type": item.inventory_type,
                "cost": _round(item.cost),
                "quantity": int(item.quantity or 0),
                "stock_value": _round(float(item.cost or 0) * int(item.quantity or 0)),
            }
            for item in inventory
        ]
        items.sort(key=lambda row: row["stock_value"], reverse=True)

        return {
            "item_count": len(inventory),
            "total_stock_value": _round(sum(row["stock_value"] for row in items)),
            "items": items,
            "sales": {
                "purchase_count": len(purchases),
                "total_sales": _round(sum(float(p.amount or 0) for p in purchases)),
                "unsupplied_count": sum(
                    1 for p in purchases if not p.is_item_supplied
                ),
            },
        }

    def _food(
        self,
        registrations: List[Registration],
        foods: List[Food],
        food_allocations: List[FoodAllocation],
    ) -> Dict[str, Any]:
        category_entries: Counter = Counter()
        category_quantity: Dict[str, int] = defaultdict(int)
        vendor_entries: Counter = Counter()
        vendor_quantity: Dict[str, int] = defaultdict(int)

        for food in foods:
            category = food.category or "Uncategorised"
            vendor = food.vendor or "Unspecified"
            quantity = int(food.quantity or 0)

            category_entries[category] += 1
            category_quantity[category] += quantity
            vendor_entries[vendor] += 1
            vendor_quantity[vendor] += quantity

        campers_served = len({a.registration_id for a in food_allocations})

        return {
            "total_meals_recorded": len(foods),
            "total_quantity": sum(int(f.quantity or 0) for f in foods),
            "by_category": [
                {
                    "category": category,
                    "entries": count,
                    "quantity": category_quantity[category],
                }
                for category, count in category_entries.most_common()
            ],
            "by_vendor": [
                {
                    "vendor": vendor,
                    "entries": count,
                    "quantity": vendor_quantity[vendor],
                }
                for vendor, count in vendor_entries.most_common()
            ],
            "allocations_recorded": len(food_allocations),
            "campers_served": campers_served,
            "coverage_rate": _rate(campers_served, len(registrations)),
        }

    def _data_quality(
        self,
        registrations: List[Registration],
        payments: List[Payment],
        payment_links: Dict[str, List[str]],
        allocations: List[RoomAllocation],
    ) -> Dict[str, Any]:
        allocated_registration_ids = {
            a.registration_id for a in allocations if a.is_active
        }

        shared_payments = sum(
            1 for links in payment_links.values() if len(links) > 1
        )
        unlinked_payments = sum(
            1 for p in payments if not payment_links.get(p.id)
        )

        return {
            "shared_payments_detected": shared_payments,
            "payments_not_linked_to_any_registration": unlinked_payments,
            "registrations_missing_email": sum(
                1 for r in registrations if not (r.email or "").strip()
            ),
            "registrations_missing_church": sum(
                1 for r in registrations if not r.church_id
            ),
            "checked_in_without_bed": sum(
                1
                for r in registrations
                if r.has_checked_in and r.id not in allocated_registration_ids
            ),
        }
