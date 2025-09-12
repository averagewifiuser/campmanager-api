"""Add performance indexes for frequently queried columns

Revision ID: add_performance_indexes
Revises: fa85fbf47d0f
Create Date: 2025-12-09 14:46:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = '85d323a03768'
branch_labels = None
depends_on = None


def upgrade():
    # User table indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Camp table indexes
    op.create_index('idx_camps_is_active', 'camps', ['is_active'])
    op.create_index('idx_camps_start_date', 'camps', ['start_date'])
    op.create_index('idx_camps_end_date', 'camps', ['end_date'])
    op.create_index('idx_camps_registration_deadline', 'camps', ['registration_deadline'])
    
    # CampWorker table indexes
    op.create_index('idx_camp_workers_user_id', 'camp_workers', ['user_id'])
    op.create_index('idx_camp_workers_camp_id', 'camp_workers', ['camp_id'])
    op.create_index('idx_camp_workers_role', 'camp_workers', ['role'])
    op.create_index('idx_camp_workers_user_camp', 'camp_workers', ['user_id', 'camp_id'])
    
    # Church table indexes
    op.create_index('idx_churches_camp_id', 'churches', ['camp_id'])
    op.create_index('idx_churches_name', 'churches', ['name'])
    op.create_index('idx_churches_district', 'churches', ['district'])
    op.create_index('idx_churches_area', 'churches', ['area'])
    
    # Category table indexes
    op.create_index('idx_categories_camp_id', 'categories', ['camp_id'])
    op.create_index('idx_categories_is_default', 'categories', ['is_default'])
    op.create_index('idx_categories_name', 'categories', ['name'])
    
    # CustomField table indexes
    op.create_index('idx_custom_fields_camp_id', 'custom_fields', ['camp_id'])
    op.create_index('idx_custom_fields_order', 'custom_fields', ['order'])
    op.create_index('idx_custom_fields_field_type', 'custom_fields', ['field_type'])
    
    # RegistrationLink table indexes
    op.create_index('idx_registration_links_camp_id', 'registration_links', ['camp_id'])
    op.create_index('idx_registration_links_link_token', 'registration_links', ['link_token'])
    op.create_index('idx_registration_links_is_active', 'registration_links', ['is_active'])
    op.create_index('idx_registration_links_expires_at', 'registration_links', ['expires_at'])
    op.create_index('idx_registration_links_created_by', 'registration_links', ['created_by'])
    
    # Registration table indexes (most critical for performance)
    # Note: camp_id already has an index from the model definition
    op.create_index('idx_registrations_church_id', 'registrations', ['church_id'])
    op.create_index('idx_registrations_category_id', 'registrations', ['category_id'])
    op.create_index('idx_registrations_has_paid', 'registrations', ['has_paid'])
    op.create_index('idx_registrations_has_checked_in', 'registrations', ['has_checked_in'])
    op.create_index('idx_registrations_registration_date', 'registrations', ['registration_date'])
    op.create_index('idx_registrations_camper_code', 'registrations', ['camper_code'])
    op.create_index('idx_registrations_phone_number', 'registrations', ['phone_number'])
    op.create_index('idx_registrations_email', 'registrations', ['email'])
    op.create_index('idx_registrations_registration_link_id', 'registrations', ['registration_link_id'])
    op.create_index('idx_registrations_otp_requested', 'registrations', ['otp_requested'])
    op.create_index('idx_registrations_sex', 'registrations', ['sex'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_registrations_camp_church', 'registrations', ['camp_id', 'church_id'])
    op.create_index('idx_registrations_camp_category', 'registrations', ['camp_id', 'category_id'])
    op.create_index('idx_registrations_camp_paid', 'registrations', ['camp_id', 'has_paid'])
    op.create_index('idx_registrations_camp_checkin', 'registrations', ['camp_id', 'has_checked_in'])
    op.create_index('idx_registrations_email_phone_camp', 'registrations', ['email', 'phone_number', 'camp_id'])
    
    # Payment table indexes
    op.create_index('idx_payments_camp_id', 'payments', ['camp_id'])
    op.create_index('idx_payments_payment_date', 'payments', ['payment_date'])
    op.create_index('idx_payments_payment_channel', 'payments', ['payment_channel'])
    op.create_index('idx_payments_recorded_by', 'payments', ['recorded_by'])
    op.create_index('idx_payments_payment_reference', 'payments', ['payment_reference'])
    
    # Financial table indexes
    op.create_index('idx_financial_transactions_camp_id', 'financial_transactions', ['camp_id'])
    op.create_index('idx_financial_transactions_transaction_type', 'financial_transactions', ['transaction_type'])
    op.create_index('idx_financial_transactions_transaction_category', 'financial_transactions', ['transaction_category'])
    op.create_index('idx_financial_transactions_date', 'financial_transactions', ['date'])
    op.create_index('idx_financial_transactions_is_deleted', 'financial_transactions', ['is_deleted'])
    op.create_index('idx_financial_transactions_payment_method', 'financial_transactions', ['payment_method'])
    op.create_index('idx_financial_transactions_reference_number', 'financial_transactions', ['reference_number'])
    
    # Composite indexes for financial queries
    op.create_index('idx_financial_camp_type', 'financial_transactions', ['camp_id', 'transaction_type'])
    op.create_index('idx_financial_camp_category', 'financial_transactions', ['camp_id', 'transaction_category'])
    op.create_index('idx_financial_camp_deleted', 'financial_transactions', ['camp_id', 'is_deleted'])
    
    # Inventory table indexes
    op.create_index('idx_inventory_camp_id', 'inventory', ['camp_id'])
    op.create_index('idx_inventory_inventory_type', 'inventory', ['inventory_type'])
    op.create_index('idx_inventory_is_deleted', 'inventory', ['is_deleted'])
    op.create_index('idx_inventory_camp_deleted', 'inventory', ['camp_id', 'is_deleted'])
    
    # Purchase table indexes
    op.create_index('idx_purchases_camp_id', 'purchases', ['camp_id'])
    op.create_index('idx_purchases_purchase_date', 'purchases', ['purchase_date'])
    op.create_index('idx_purchases_sold_by', 'purchases', ['sold_by'])
    
    # Pledge table indexes
    op.create_index('idx_pledges_camp_id', 'pledges', ['camp_id'])
    op.create_index('idx_pledges_camper_id', 'pledges', ['camper_id'])
    op.create_index('idx_pledges_status', 'pledges', ['status'])
    op.create_index('idx_pledges_pledge_date', 'pledges', ['pledge_date'])
    op.create_index('idx_pledges_camper_camp', 'pledges', ['camper_id', 'camp_id'])
    
    # Room table indexes
    op.create_index('idx_rooms_camp_id', 'rooms', ['camp_id'])
    op.create_index('idx_rooms_hostel_name', 'rooms', ['hostel_name'])
    op.create_index('idx_rooms_room_gender', 'rooms', ['room_gender'])
    op.create_index('idx_rooms_is_damaged', 'rooms', ['is_damaged'])
    op.create_index('idx_rooms_is_special_room', 'rooms', ['is_special_room'])
    op.create_index('idx_rooms_camp_gender', 'rooms', ['camp_id', 'room_gender'])
    op.create_index('idx_rooms_camp_damaged', 'rooms', ['camp_id', 'is_damaged'])
    
    # RoomAllocation table indexes
    op.create_index('idx_room_allocations_room_id', 'room_allocations', ['room_id'])
    op.create_index('idx_room_allocations_registration_id', 'room_allocations', ['registration_id'])
    op.create_index('idx_room_allocations_camp_id', 'room_allocations', ['camp_id'])
    op.create_index('idx_room_allocations_allocated_by', 'room_allocations', ['allocated_by'])
    op.create_index('idx_room_allocations_allocation_date', 'room_allocations', ['allocation_date'])
    op.create_index('idx_room_allocations_is_active', 'room_allocations', ['is_active'])
    op.create_index('idx_room_allocations_camp_active', 'room_allocations', ['camp_id', 'is_active'])
    
    # Food table indexes
    op.create_index('idx_foods_camp_id', 'foods', ['camp_id'])
    op.create_index('idx_foods_category', 'foods', ['category'])
    op.create_index('idx_foods_date', 'foods', ['date'])
    op.create_index('idx_foods_vendor', 'foods', ['vendor'])
    op.create_index('idx_foods_camp_category', 'foods', ['camp_id', 'category'])
    op.create_index('idx_foods_camp_date', 'foods', ['camp_id', 'date'])
    
    # FoodAllocation table indexes
    op.create_index('idx_food_allocations_food_id', 'food_allocations', ['food_id'])
    op.create_index('idx_food_allocations_registration_id', 'food_allocations', ['registration_id'])
    op.create_index('idx_food_allocations_camp_id', 'food_allocations', ['camp_id'])
    op.create_index('idx_food_allocations_allocated_by', 'food_allocations', ['allocated_by'])
    op.create_index('idx_food_allocations_allocation_date', 'food_allocations', ['allocation_date'])
    
    # Registration payments junction table indexes
    op.create_index('idx_registration_payments_registration_id', 'registration_payments', ['registration_id'])
    op.create_index('idx_registration_payments_payment_id', 'registration_payments', ['payment_id'])
    op.create_index('idx_registration_payments_created_at', 'registration_payments', ['created_at'])


def downgrade():
    # Drop all indexes in reverse order
    
    # Registration payments junction table indexes
    op.drop_index('idx_registration_payments_created_at', 'registration_payments')
    op.drop_index('idx_registration_payments_payment_id', 'registration_payments')
    op.drop_index('idx_registration_payments_registration_id', 'registration_payments')
    
    # FoodAllocation table indexes
    op.drop_index('idx_food_allocations_allocation_date', 'food_allocations')
    op.drop_index('idx_food_allocations_allocated_by', 'food_allocations')
    op.drop_index('idx_food_allocations_camp_id', 'food_allocations')
    op.drop_index('idx_food_allocations_registration_id', 'food_allocations')
    op.drop_index('idx_food_allocations_food_id', 'food_allocations')
    
    # Food table indexes
    op.drop_index('idx_foods_camp_date', 'foods')
    op.drop_index('idx_foods_camp_category', 'foods')
    op.drop_index('idx_foods_vendor', 'foods')
    op.drop_index('idx_foods_date', 'foods')
    op.drop_index('idx_foods_category', 'foods')
    op.drop_index('idx_foods_camp_id', 'foods')
    
    # RoomAllocation table indexes
    op.drop_index('idx_room_allocations_camp_active', 'room_allocations')
    op.drop_index('idx_room_allocations_is_active', 'room_allocations')
    op.drop_index('idx_room_allocations_allocation_date', 'room_allocations')
    op.drop_index('idx_room_allocations_allocated_by', 'room_allocations')
    op.drop_index('idx_room_allocations_camp_id', 'room_allocations')
    op.drop_index('idx_room_allocations_registration_id', 'room_allocations')
    op.drop_index('idx_room_allocations_room_id', 'room_allocations')
    
    # Room table indexes
    op.drop_index('idx_rooms_camp_damaged', 'rooms')
    op.drop_index('idx_rooms_camp_gender', 'rooms')
    op.drop_index('idx_rooms_is_special_room', 'rooms')
    op.drop_index('idx_rooms_is_damaged', 'rooms')
    op.drop_index('idx_rooms_room_gender', 'rooms')
    op.drop_index('idx_rooms_hostel_name', 'rooms')
    op.drop_index('idx_rooms_camp_id', 'rooms')
    
    # Pledge table indexes
    op.drop_index('idx_pledges_camper_camp', 'pledges')
    op.drop_index('idx_pledges_pledge_date', 'pledges')
    op.drop_index('idx_pledges_status', 'pledges')
    op.drop_index('idx_pledges_camper_id', 'pledges')
    op.drop_index('idx_pledges_camp_id', 'pledges')
    
    # Purchase table indexes
    op.drop_index('idx_purchases_sold_by', 'purchases')
    op.drop_index('idx_purchases_purchase_date', 'purchases')
    op.drop_index('idx_purchases_camp_id', 'purchases')
    
    # Inventory table indexes
    op.drop_index('idx_inventory_camp_deleted', 'inventory')
    op.drop_index('idx_inventory_is_deleted', 'inventory')
    op.drop_index('idx_inventory_inventory_type', 'inventory')
    op.drop_index('idx_inventory_camp_id', 'inventory')
    
    # Financial table indexes
    op.drop_index('idx_financial_camp_deleted', 'financial_transactions')
    op.drop_index('idx_financial_camp_category', 'financial_transactions')
    op.drop_index('idx_financial_camp_type', 'financial_transactions')
    op.drop_index('idx_financial_transactions_reference_number', 'financial_transactions')
    op.drop_index('idx_financial_transactions_payment_method', 'financial_transactions')
    op.drop_index('idx_financial_transactions_is_deleted', 'financial_transactions')
    op.drop_index('idx_financial_transactions_date', 'financial_transactions')
    op.drop_index('idx_financial_transactions_transaction_category', 'financial_transactions')
    op.drop_index('idx_financial_transactions_transaction_type', 'financial_transactions')
    op.drop_index('idx_financial_transactions_camp_id', 'financial_transactions')
    
    # Payment table indexes
    op.drop_index('idx_payments_payment_reference', 'payments')
    op.drop_index('idx_payments_recorded_by', 'payments')
    op.drop_index('idx_payments_payment_channel', 'payments')
    op.drop_index('idx_payments_payment_date', 'payments')
    op.drop_index('idx_payments_camp_id', 'payments')
    
    # Registration table indexes
    op.drop_index('idx_registrations_email_phone_camp', 'registrations')
    op.drop_index('idx_registrations_camp_checkin', 'registrations')
    op.drop_index('idx_registrations_camp_paid', 'registrations')
    op.drop_index('idx_registrations_camp_category', 'registrations')
    op.drop_index('idx_registrations_camp_church', 'registrations')
    op.drop_index('idx_registrations_sex', 'registrations')
    op.drop_index('idx_registrations_otp_requested', 'registrations')
    op.drop_index('idx_registrations_registration_link_id', 'registrations')
    op.drop_index('idx_registrations_email', 'registrations')
    op.drop_index('idx_registrations_phone_number', 'registrations')
    op.drop_index('idx_registrations_camper_code', 'registrations')
    op.drop_index('idx_registrations_registration_date', 'registrations')
    op.drop_index('idx_registrations_has_checked_in', 'registrations')
    op.drop_index('idx_registrations_has_paid', 'registrations')
    op.drop_index('idx_registrations_category_id', 'registrations')
    op.drop_index('idx_registrations_church_id', 'registrations')
    
    # RegistrationLink table indexes
    op.drop_index('idx_registration_links_created_by', 'registration_links')
    op.drop_index('idx_registration_links_expires_at', 'registration_links')
    op.drop_index('idx_registration_links_is_active', 'registration_links')
    op.drop_index('idx_registration_links_link_token', 'registration_links')
    op.drop_index('idx_registration_links_camp_id', 'registration_links')
    
    # CustomField table indexes
    op.drop_index('idx_custom_fields_field_type', 'custom_fields')
    op.drop_index('idx_custom_fields_order', 'custom_fields')
    op.drop_index('idx_custom_fields_camp_id', 'custom_fields')
    
    # Category table indexes
    op.drop_index('idx_categories_name', 'categories')
    op.drop_index('idx_categories_is_default', 'categories')
    op.drop_index('idx_categories_camp_id', 'categories')
    
    # Church table indexes
    op.drop_index('idx_churches_area', 'churches')
    op.drop_index('idx_churches_district', 'churches')
    op.drop_index('idx_churches_name', 'churches')
    op.drop_index('idx_churches_camp_id', 'churches')
    
    # CampWorker table indexes
    op.drop_index('idx_camp_workers_user_camp', 'camp_workers')
    op.drop_index('idx_camp_workers_role', 'camp_workers')
    op.drop_index('idx_camp_workers_camp_id', 'camp_workers')
    op.drop_index('idx_camp_workers_user_id', 'camp_workers')
    
    # Camp table indexes
    op.drop_index('idx_camps_registration_deadline', 'camps')
    op.drop_index('idx_camps_end_date', 'camps')
    op.drop_index('idx_camps_start_date', 'camps')
    op.drop_index('idx_camps_is_active', 'camps')
    
    # User table indexes
    op.drop_index('idx_users_role', 'users')
    op.drop_index('idx_users_email', 'users')
