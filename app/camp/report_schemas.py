"""Response schemas for the camp report endpoint."""

from apiflask import Schema
from marshmallow import fields


class ReportCampSchema(Schema):
    """Camp header shown on the report cover."""
    id = fields.String()
    name = fields.String()
    start_date = fields.String(allow_none=True)
    end_date = fields.String(allow_none=True)
    location = fields.String(allow_none=True)
    capacity = fields.Integer()
    base_fee = fields.Float()
    description = fields.String(allow_none=True)
    registration_deadline = fields.String(allow_none=True)
    is_active = fields.Boolean()
    generated_at = fields.String()


class ReportSummarySchema(Schema):
    """Headline figures for the executive summary."""
    total_registered = fields.Integer()
    total_checked_in = fields.Integer()
    check_in_rate = fields.Float()
    no_show_count = fields.Integer()
    no_show_rate = fields.Float()
    capacity = fields.Integer()
    capacity_utilization = fields.Float()
    expected_revenue = fields.Float()
    collected_revenue = fields.Float()
    collection_rate = fields.Float()
    outstanding_balance = fields.Float()
    beds_available = fields.Integer()
    beds_allocated = fields.Integer()


class RegistrationByDateSchema(Schema):
    date = fields.String()
    count = fields.Integer()
    cumulative = fields.Integer()


class RegistrationByLinkSchema(Schema):
    link_name = fields.String()
    count = fields.Integer()


class ReportRegistrationSchema(Schema):
    by_date = fields.List(fields.Nested(RegistrationByDateSchema))
    registrations_after_deadline = fields.Integer()
    by_link = fields.List(fields.Nested(RegistrationByLinkSchema))
    first_registration = fields.String(allow_none=True)
    last_registration = fields.String(allow_none=True)


class AgeBandSchema(Schema):
    band = fields.String()
    count = fields.Integer()


class SexSplitSchema(Schema):
    sex = fields.String()
    count = fields.Integer()


class ReportDemographicsSchema(Schema):
    by_age_band = fields.List(fields.Nested(AgeBandSchema))
    by_sex = fields.List(fields.Nested(SexSplitSchema))
    age_min = fields.Integer()
    age_max = fields.Integer()
    age_average = fields.Float()
    age_median = fields.Float()


class ReportCategorySchema(Schema):
    name = fields.String()
    count = fields.Integer()
    share = fields.Float()
    discount_percentage = fields.Float()
    discount_amount = fields.Float()
    expected_revenue = fields.Float()
    collected_revenue = fields.Float()
    total_discount_given = fields.Float()
    checked_in = fields.Integer()


class CustomFieldOptionSchema(Schema):
    option = fields.String()
    count = fields.Integer()
    share = fields.Float()


class ReportCustomFieldSchema(Schema):
    field_name = fields.String()
    field_type = fields.String()
    is_required = fields.Boolean()
    is_multi_select = fields.Boolean()
    answered_count = fields.Integer()
    unanswered_count = fields.Integer()
    answered_rate = fields.Float()
    options = fields.List(fields.Nested(CustomFieldOptionSchema))
    options_truncated = fields.Integer()


class ChurchRowSchema(Schema):
    name = fields.String()
    district = fields.String(allow_none=True)
    area = fields.String(allow_none=True)
    region = fields.String(allow_none=True)
    count = fields.Integer()
    checked_in = fields.Integer()
    collected = fields.Float()


class DistrictSpreadSchema(Schema):
    district = fields.String()
    count = fields.Integer()


class AreaSpreadSchema(Schema):
    area = fields.String()
    count = fields.Integer()


class RegionSpreadSchema(Schema):
    region = fields.String()
    count = fields.Integer()


class ReportChurchesSchema(Schema):
    total_churches_represented = fields.Integer()
    total_churches_registered = fields.Integer()
    by_church = fields.List(fields.Nested(ChurchRowSchema))
    by_district = fields.List(fields.Nested(DistrictSpreadSchema))
    by_area = fields.List(fields.Nested(AreaSpreadSchema))
    by_region = fields.List(fields.Nested(RegionSpreadSchema))


class PaymentChannelSchema(Schema):
    channel = fields.String()
    count = fields.Integer()
    amount = fields.Float()


class ReportPaymentsSchema(Schema):
    expected_total = fields.Float()
    collected_total = fields.Float()
    outstanding_total = fields.Float()
    collection_rate = fields.Float()
    payment_count = fields.Integer()
    fully_paid_count = fields.Integer()
    partially_paid_count = fields.Integer()
    unpaid_count = fields.Integer()
    by_channel = fields.List(fields.Nested(PaymentChannelSchema))
    has_paid_flag_true = fields.Integer()
    flag_mismatch_count = fields.Integer()


class HostelRowSchema(Schema):
    hostel_name = fields.String()
    rooms = fields.Integer()
    beds = fields.Integer()
    allocated = fields.Integer()
    occupancy_rate = fields.Float()


class RoomGenderRowSchema(Schema):
    room_gender = fields.String()
    rooms = fields.Integer()
    beds = fields.Integer()
    allocated = fields.Integer()
    occupancy_rate = fields.Float()


class ReportAccommodationSchema(Schema):
    total_rooms = fields.Integer()
    usable_rooms = fields.Integer()
    damaged_rooms = fields.Integer()
    special_rooms = fields.Integer()
    total_beds = fields.Integer()
    base_beds = fields.Integer()
    extra_beds = fields.Integer()
    allocated_beds = fields.Integer()
    free_beds = fields.Integer()
    occupancy_rate = fields.Float()
    unallocated_campers = fields.Integer()
    by_hostel = fields.List(fields.Nested(HostelRowSchema))
    by_gender = fields.List(fields.Nested(RoomGenderRowSchema))


class PledgeStatusSchema(Schema):
    status = fields.String()
    count = fields.Integer()
    amount = fields.Float()


class ReportPledgesSchema(Schema):
    pledge_count = fields.Integer()
    total_pledged = fields.Float()
    total_fulfilled = fields.Float()
    total_outstanding = fields.Float()
    fulfillment_rate = fields.Float()
    fully_fulfilled_count = fields.Integer()
    by_status = fields.List(fields.Nested(PledgeStatusSchema))


class FinancialCategorySchema(Schema):
    transaction_type = fields.String()
    transaction_category = fields.String()
    count = fields.Integer()
    amount = fields.Float()


class ReportFinancialsSchema(Schema):
    transaction_count = fields.Integer()
    total_income = fields.Float()
    total_expense = fields.Float()
    net = fields.Float()
    by_category = fields.List(fields.Nested(FinancialCategorySchema))


class InventoryItemSchema(Schema):
    name = fields.String()
    inventory_type = fields.String()
    cost = fields.Float()
    quantity = fields.Integer()
    stock_value = fields.Float()


class InventorySalesSchema(Schema):
    purchase_count = fields.Integer()
    total_sales = fields.Float()
    unsupplied_count = fields.Integer()


class ReportInventorySchema(Schema):
    item_count = fields.Integer()
    total_stock_value = fields.Float()
    items = fields.List(fields.Nested(InventoryItemSchema))
    sales = fields.Nested(InventorySalesSchema)


class FoodCategorySchema(Schema):
    category = fields.String()
    entries = fields.Integer()
    quantity = fields.Integer()


class FoodVendorSchema(Schema):
    vendor = fields.String()
    entries = fields.Integer()
    quantity = fields.Integer()


class ReportFoodSchema(Schema):
    total_meals_recorded = fields.Integer()
    total_quantity = fields.Integer()
    by_category = fields.List(fields.Nested(FoodCategorySchema))
    by_vendor = fields.List(fields.Nested(FoodVendorSchema))
    allocations_recorded = fields.Integer()
    campers_served = fields.Integer()
    coverage_rate = fields.Float()


class ReportDataQualitySchema(Schema):
    shared_payments_detected = fields.Integer()
    payments_not_linked_to_any_registration = fields.Integer()
    registrations_missing_email = fields.Integer()
    registrations_missing_church = fields.Integer()
    checked_in_without_bed = fields.Integer()


class CampReportSchema(Schema):
    """Complete camp report payload."""
    camp = fields.Nested(ReportCampSchema)
    summary = fields.Nested(ReportSummarySchema)
    registration = fields.Nested(ReportRegistrationSchema)
    demographics = fields.Nested(ReportDemographicsSchema)
    categories = fields.List(fields.Nested(ReportCategorySchema))
    custom_fields = fields.List(fields.Nested(ReportCustomFieldSchema))
    churches = fields.Nested(ReportChurchesSchema)
    payments = fields.Nested(ReportPaymentsSchema)
    accommodation = fields.Nested(ReportAccommodationSchema)
    pledges = fields.Nested(ReportPledgesSchema)
    financials = fields.Nested(ReportFinancialsSchema)
    inventory = fields.Nested(ReportInventorySchema)
    food = fields.Nested(ReportFoodSchema)
    data_quality = fields.Nested(ReportDataQualitySchema)


class CampReportResponseWrapperSchema(Schema):
    """Wrapper for the camp report response"""
    data = fields.Nested(CampReportSchema, required=True)
