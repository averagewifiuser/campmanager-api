from typing import Optional, Dict, Any, List
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from decimal import Decimal
import random
import string
from app.user.models import User
from app.cache import cached, invalidate_registration_form_cache

from .models import (
    Camp,
    CampWorker,
    Church,
    Category,
    CustomField,
    RegistrationLink,
    Registration,
    Payment,
    Financial,
    Inventory,
    Pledge,
    Room,
    RoomAllocation,
    db,
)


class CampService:
    """Service class for camp-related business logic"""

    def get_camp_by_id(self, camp_id: str) -> Optional[Camp]:
        """Get camp by ID"""
        try:
            return Camp.query.filter_by(id=camp_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_by_id: {str(e)}")
            return None

    def get_user_camps(self, user_id: str) -> List[Camp]:
        """Get all camps for a specific user"""
        try:
            camp_ids = CampWorker.query.filter_by(user_id=user_id).all()
            camps = (
                Camp.query.filter(Camp.id.in_([camp.camp_id for camp in camp_ids]))
                .order_by(Camp.created_at.desc())
                .all()
            )
            return camps
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_user_camps: {str(e)}")
            return []

    def create_camp(self, camp_data: Dict[str, Any]) -> Optional[Camp]:
        """Create a new camp"""
        try:
            # Validate required fields
            required_fields = [
                "name",
                "start_date",
                "end_date",
                "location",
                "base_fee",
                "capacity",
                "registration_deadline",
                "camp_manager_id",
            ]
            for field in required_fields:
                if field not in camp_data or camp_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate dates
            start_date = camp_data["start_date"]
            end_date = camp_data["end_date"]
            registration_deadline = camp_data["registration_deadline"]

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()
            if isinstance(registration_deadline, str):
                registration_deadline = datetime.fromisoformat(registration_deadline)

            if end_date <= start_date:
                raise ValueError("End date must be after start date")

            if registration_deadline.date() > start_date:
                raise ValueError(
                    "Registration deadline must be before or on start date"
                )

            # Validate numeric fields
            if float(camp_data["base_fee"]) < 0:
                raise ValueError("Base fee must be non-negative")

            if int(camp_data["capacity"]) < 1:
                raise ValueError("Capacity must be at least 1")

            # Create camp
            new_camp = Camp(
                name=camp_data["name"].strip(),
                start_date=start_date,
                end_date=end_date,
                location=camp_data["location"].strip(),
                base_fee=Decimal(str(camp_data["base_fee"])),
                capacity=int(camp_data["capacity"]),
                description=camp_data.get("description", "").strip(),
                registration_deadline=registration_deadline,
                is_active=camp_data.get("is_active", True),
            )

            db.session.add(new_camp)
            db.session.commit()

            camp_worker = CampWorker(
                user_id=camp_data["camp_manager_id"],
                camp_id=new_camp.id,
                role="camp_manager",
            )
            db.session.add(camp_worker)
            db.session.commit()

            current_app.logger.info(
                f"New camp created: {new_camp.name} by {camp_data['camp_manager_id']}"
            )
            return new_camp

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_camp: {str(e)}")
            raise Exception("Failed to create camp due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_camp: {str(e)}")
            raise Exception("Failed to create camp")

    def update_camp(self, camp_id: str, update_data: Dict[str, Any]) -> Optional[Camp]:
        """Update camp information"""
        try:
            camp = self.get_camp_by_id(camp_id)
            if not camp:
                return None

            # Validate dates if provided
            if "start_date" in update_data and "end_date" in update_data:
                start_date = update_data["start_date"]
                end_date = update_data["end_date"]

                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date).date()

                if end_date <= start_date:
                    raise ValueError("End date must be after start date")

            # Update fields
            updatable_fields = [
                "name",
                "start_date",
                "end_date",
                "location",
                "base_fee",
                "capacity",
                "description",
                "registration_deadline",
                "is_active",
            ]
            for field in updatable_fields:
                if field in update_data:
                    if field in ["base_fee"] and update_data[field] is not None:
                        if float(update_data[field]) < 0:
                            raise ValueError(f"{field} must be non-negative")
                        setattr(camp, field, Decimal(str(update_data[field])))
                    elif field in ["capacity"] and update_data[field] is not None:
                        if int(update_data[field]) < 1:
                            raise ValueError("Capacity must be at least 1")
                        setattr(camp, field, int(update_data[field]))
                    elif (
                        field in ["registration_deadline"]
                        and update_data[field] is not None
                    ):
                        deadline = update_data[field]
                        if isinstance(deadline, str):
                            deadline = datetime.fromisoformat(deadline)
                        setattr(camp, field, deadline)
                    elif (
                        field in ["start_date", "end_date"]
                        and update_data[field] is not None
                    ):
                        date_val = update_data[field]
                        if isinstance(date_val, str):
                            date_val = datetime.fromisoformat(date_val).date()
                        setattr(camp, field, date_val)
                    else:
                        if update_data[field] is not None:
                            value = (
                                update_data[field].strip()
                                if isinstance(update_data[field], str)
                                else update_data[field]
                            )
                            setattr(camp, field, value)

            db.session.commit()

            current_app.logger.info(f"Camp updated: {camp.name}")
            return camp

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_camp: {str(e)}")
            raise Exception("Failed to update camp due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_camp: {str(e)}")
            raise Exception("Failed to update camp")

    def delete_camp(self, camp_id: str) -> bool:
        """Delete a camp and all related data"""
        try:
            camp = self.get_camp_by_id(camp_id)
            if not camp:
                return False

            # This will cascade delete all related data (churches, categories, etc.)
            db.session.delete(camp)
            db.session.commit()

            current_app.logger.info(f"Camp deleted: {camp.name}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_camp: {str(e)}")
            raise Exception("Failed to delete camp due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_camp: {str(e)}")
            raise Exception("Failed to delete camp")

    def get_camp_stats(self, camp_id: str) -> Optional[Dict[str, Any]]:
        """Get camp statistics"""
        try:
            camp = self.get_camp_by_id(camp_id)
            if not camp:
                return None

            # Count registrations
            total_registrations = len(camp.registrations)
            paid_registrations = sum(1 for reg in camp.registrations if reg.has_paid)
            unpaid_registrations = total_registrations - paid_registrations
            checked_in_count = sum(
                1 for reg in camp.registrations if reg.has_checked_in
            )

            # Calculate capacity percentage
            capacity_percentage = (
                (total_registrations / camp.capacity * 100) if camp.capacity > 0 else 0
            )

            payments = Payment.query.filter_by(camp_id=camp_id).all()
            total_revenue = sum(float(payment.amount) for payment in payments)

            return {
                "camp_id": str(camp.id),
                "total_registrations": total_registrations,
                "paid_registrations": paid_registrations,
                "unpaid_registrations": unpaid_registrations,
                "checked_in_count": checked_in_count,
                "total_capacity": camp.capacity,
                "capacity_percentage": round(capacity_percentage, 2),
                "total_revenue": total_revenue,
            }

        except Exception as e:
            current_app.logger.error(f"Error in get_camp_stats: {str(e)}")
            return None


class ChurchService:
    """Service class for church-related business logic"""

    def get_church_by_id(self, church_id: str) -> Optional[Church]:
        """Get church by ID"""
        try:
            return Church.query.filter_by(id=church_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_church_by_id: {str(e)}")
            return None

    def get_camp_churches(self, camp_id: str) -> List[Church]:
        """Get all churches for a camp"""
        try:
            return Church.query.filter_by(camp_id=camp_id).order_by(Church.name).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_churches: {str(e)}")
            return []

    def create_church(self, church_data: Dict[str, Any]) -> Optional[Church]:
        """Create a new church"""
        try:
            # Validate required fields
            if "name" not in church_data or not church_data["name"].strip():
                raise ValueError("Church name is required")

            if "camp_id" not in church_data:
                raise ValueError("Camp ID is required")

            # Check for duplicate church name in the same camp
            existing_church = Church.query.filter_by(
                name=church_data["name"].strip(),
                camp_id=church_data["camp_id"],
                area=church_data["area"].strip() if "area" in church_data else None,
                district=(
                    church_data["district"].strip()
                    if "district" in church_data
                    else None
                ),
                region=(
                    church_data["region"].strip()
                    if "region" in church_data
                    else None
                )
            ).first()

            if existing_church:
                existing_church.name = (
                    church_data["name"].strip()
                    if "name" in church_data
                    else existing_church.name
                )
                existing_church.area = (
                    church_data["area"].strip()
                    if "area" in church_data
                    else existing_church.area
                )
                existing_church.district = (
                    church_data["district"].strip()
                    if "district" in church_data
                    else existing_church.district
                )
                existing_church.region = (
                    church_data["region"].strip()
                    if "region" in church_data
                    else existing_church.region
                )
                db.session.commit()
                return existing_church

            new_church = Church(
                name=church_data["name"].strip(),
                camp_id=church_data["camp_id"],
                area=church_data["area"].strip() if "area" in church_data else None,
                district=(
                    church_data["district"].strip()
                    if "district" in church_data
                    else None
                ),
                region=(
                    church_data["region"].strip()
                    if "region" in church_data
                    else None
                ),
            )

            db.session.add(new_church)
            db.session.commit()

            # Invalidate registration form cache for this camp
            invalidate_registration_form_cache(church_data['camp_id'])

            current_app.logger.info(
                f"New church created: {new_church.name} for camp {church_data['camp_id']}"
            )
            return new_church

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_church: {str(e)}")
            raise Exception("Failed to create church due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_church: {str(e)}")
            raise Exception("Failed to create church")

    def create_churches(self, church_data: List[Dict[str, Any]]) -> List[Church]:
        """Create multiple churches"""
        try:
            churches = []
            for church in church_data:
                new_church = self.create_church(church)
                churches.append(new_church)
            return churches
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_churches: {str(e)}")
            raise Exception("Failed to create churches due to database error")

    def update_church(
        self, church_id: str, update_data: Dict[str, Any]
    ) -> Optional[Church]:
        """Update church information"""
        try:
            church = self.get_church_by_id(church_id)
            if not church:
                return None

            if "name" in update_data:
                name = update_data["name"].strip()
                if not name:
                    raise ValueError("Church name cannot be empty")

                # Check for duplicate name in the same camp
                existing_church = (
                    Church.query.filter_by(name=name, camp_id=church.camp_id)
                    .filter(Church.id != church_id)
                    .first()
                )

                if existing_church:
                    raise ValueError(
                        "A church with this name already exists in this camp"
                    )

                church.name = name
                church.area = update_data.get("area", church.area)
                church.district = update_data.get("district", church.district)
                church.region = update_data.get("region", church.region)


            db.session.commit()

            current_app.logger.info(f"Church updated: {church.name}")
            return church

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_church: {str(e)}")
            raise Exception("Failed to update church due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_church: {str(e)}")
            raise Exception("Failed to update church")

    def delete_church(self, church_id: str) -> bool:
        """Delete a church"""
        try:
            church = self.get_church_by_id(church_id)
            if not church:
                return False

            # Check if church has registrations
            if len(church.registrations) > 0:
                raise ValueError("Cannot delete church with existing registrations")

            db.session.delete(church)
            db.session.commit()

            current_app.logger.info(f"Church deleted: {church.name}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_church: {str(e)}")
            raise Exception("Failed to delete church due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_church: {str(e)}")
            raise Exception("Failed to delete church")


class CategoryService:
    """Service class for category-related business logic"""

    def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        try:
            return Category.query.filter_by(id=category_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_category_by_id: {str(e)}")
            return None

    def get_camp_categories(self, camp_id: str) -> List[Category]:
        """Get all categories for a camp"""
        try:
            return (
                Category.query.filter_by(camp_id=camp_id).order_by(Category.name).all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_categories: {str(e)}")
            return []

    def create_category(self, category_data: Dict[str, Any]) -> Optional[Category]:
        """Create a new category"""
        try:
            # Validate required fields
            if "name" not in category_data or not category_data["name"].strip():
                raise ValueError("Category name is required")

            if "camp_id" not in category_data:
                raise ValueError("Camp ID is required")

            # Validate discount fields
            discount_percentage = category_data.get("discount_percentage", 0)
            discount_amount = category_data.get("discount_amount", 0)

            if discount_percentage and discount_amount:
                raise ValueError(
                    "Cannot set both discount percentage and discount amount"
                )

            if discount_percentage and (
                discount_percentage < 0 or discount_percentage > 100
            ):
                raise ValueError("Discount percentage must be between 0 and 100")

            if discount_amount and discount_amount < 0:
                raise ValueError("Discount amount must be non-negative")

            # Check for duplicate category name in the same camp
            existing_category = Category.query.filter_by(
                name=category_data["name"].strip(), camp_id=category_data["camp_id"]
            ).first()

            if existing_category:
                raise ValueError(
                    "A category with this name already exists in this camp"
                )

            new_category = Category(
                name=category_data["name"].strip(),
                camp_id=category_data["camp_id"],
                discount_percentage=(
                    Decimal(str(discount_percentage)) if discount_percentage else 0
                ),
                discount_amount=Decimal(str(discount_amount)) if discount_amount else 0,
                is_default=category_data.get("is_default", False),
            )

            db.session.add(new_category)
            db.session.commit()

            # Invalidate registration form cache for this camp
            invalidate_registration_form_cache(category_data['camp_id'])

            current_app.logger.info(
                f"New category created: {new_category.name} for camp {category_data['camp_id']}"
            )
            return new_category

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_category: {str(e)}")
            raise Exception("Failed to create category due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_category: {str(e)}")

    def update_category(
        self, category_id: str, update_data: Dict[str, Any]
    ) -> Optional[Category]:
        """Update category information"""
        try:
            category = self.get_category_by_id(category_id)
            if not category:
                return None

            # Validate discount fields if provided
            if (
                "discount_percentage" in update_data
                and "discount_amount" in update_data
            ):
                if (
                    update_data["discount_percentage"]
                    and update_data["discount_amount"]
                ):
                    raise ValueError(
                        "Cannot set both discount percentage and discount amount"
                    )

            if (
                "discount_percentage" in update_data
                and update_data["discount_percentage"] is not None
            ):
                if (
                    update_data["discount_percentage"] < 0
                    or update_data["discount_percentage"] > 100
                ):
                    raise ValueError("Discount percentage must be between 0 and 100")

            if (
                "discount_amount" in update_data
                and update_data["discount_amount"] is not None
            ):
                if update_data["discount_amount"] < 0:
                    raise ValueError("Discount amount must be non-negative")

            # Check for duplicate name if name is being updated
            if "name" in update_data:
                name = update_data["name"].strip()
                if not name:
                    raise ValueError("Category name cannot be empty")

                existing_category = (
                    Category.query.filter_by(name=name, camp_id=category.camp_id)
                    .filter(Category.id != category_id)
                    .first()
                )

                if existing_category:
                    raise ValueError(
                        "A category with this name already exists in this camp"
                    )

                category.name = name

            # Update other fields
            updatable_fields = ["discount_percentage", "discount_amount", "is_default"]
            for field in updatable_fields:
                if field in update_data:
                    if (
                        field in ["discount_percentage", "discount_amount"]
                        and update_data[field] is not None
                    ):
                        setattr(category, field, Decimal(str(update_data[field])))
                    else:
                        setattr(category, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Category updated: {category.name}")
            return category

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_category: {str(e)}")
            raise Exception("Failed to update category due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_category: {str(e)}")
            raise Exception("Failed to update category")

    def delete_category(self, category_id: str) -> bool:
        """Delete a category"""
        try:
            category = self.get_category_by_id(category_id)
            if not category:
                return False

            # Check if category has registrations
            if len(category.registrations) > 0:
                raise ValueError("Cannot delete category with existing registrations")

            db.session.delete(category)
            db.session.commit()

            current_app.logger.info(f"Category deleted: {category.name}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_category: {str(e)}")
            raise Exception("Failed to delete category due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_category: {str(e)}")
            raise Exception("Failed to delete category")


class CustomFieldService:
    """Service class for custom field-related business logic"""

    def get_custom_field_by_id(self, field_id: str) -> Optional[CustomField]:
        """Get custom field by ID"""
        try:
            return CustomField.query.filter_by(id=field_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_custom_field_by_id: {str(e)}"
            )
            return None

    def get_camp_custom_fields(self, camp_id: str) -> List[CustomField]:
        """Get all custom fields for a camp"""
        try:
            return (
                CustomField.query.filter_by(camp_id=camp_id)
                .order_by(CustomField.order, CustomField.field_name)
                .all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_camp_custom_fields: {str(e)}"
            )
            return []

    def create_custom_field(self, field_data: Dict[str, Any]) -> Optional[CustomField]:
        """Create a new custom field"""
        try:
            # Validate required fields
            required_fields = ["field_name", "field_type", "camp_id"]
            for field in required_fields:
                if field not in field_data or not field_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Validate field type
            valid_types = ["text", "number", "dropdown", "checkbox", "date"]
            if field_data["field_type"] not in valid_types:
                raise ValueError(
                    f"Invalid field type. Must be one of: {', '.join(valid_types)}"
                )

            # Validate options for dropdown/checkbox
            if field_data["field_type"] in ["dropdown", "checkbox"]:
                options = field_data.get("options", [])
                if not options or len(options) == 0:
                    raise ValueError(
                        "Options are required for dropdown and checkbox fields"
                    )

            # Check for duplicate field name in the same camp
            existing_field = CustomField.query.filter_by(
                field_name=field_data["field_name"].strip(),
                camp_id=field_data["camp_id"],
            ).first()

            if existing_field:
                raise ValueError(
                    "A custom field with this name already exists in this camp"
                )

            new_field = CustomField(
                field_name=field_data["field_name"].strip(),
                field_type=field_data["field_type"],
                camp_id=field_data["camp_id"],
                is_required=field_data.get("is_required", False),
                options=field_data.get("options"),
                order=field_data.get("order", 0),
            )

            db.session.add(new_field)
            db.session.commit()

            # Invalidate registration form cache for this camp
            invalidate_registration_form_cache(field_data['camp_id'])

            current_app.logger.info(
                f"New custom field created: {new_field.field_name} for camp {field_data['camp_id']}"
            )
            return new_field

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_custom_field: {str(e)}")
            raise Exception("Failed to create custom field due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in create_custom_field: {str(e)}"
            )
            raise Exception("Failed to create custom field")

    def update_custom_field(
        self, field_id: str, update_data: Dict[str, Any]
    ) -> Optional[CustomField]:
        """Update custom field information"""
        try:
            custom_field = self.get_custom_field_by_id(field_id)
            if not custom_field:
                return None

            # Validate field type if being updated
            if "field_type" in update_data:
                valid_types = ["text", "number", "dropdown", "checkbox", "date"]
                if update_data["field_type"] not in valid_types:
                    raise ValueError(
                        f"Invalid field type. Must be one of: {', '.join(valid_types)}"
                    )

            # Validate options for dropdown/checkbox
            field_type = update_data.get("field_type", custom_field.field_type)
            if field_type in ["dropdown", "checkbox"]:
                options = update_data.get("options", custom_field.options)
                if not options or len(options) == 0:
                    raise ValueError(
                        "Options are required for dropdown and checkbox fields"
                    )

            # Check for duplicate name if name is being updated
            if "field_name" in update_data:
                name = update_data["field_name"].strip()
                if not name:
                    raise ValueError("Field name cannot be empty")

                existing_field = (
                    CustomField.query.filter_by(
                        field_name=name, camp_id=custom_field.camp_id
                    )
                    .filter(CustomField.id != field_id)
                    .first()
                )

                if existing_field:
                    raise ValueError(
                        "A custom field with this name already exists in this camp"
                    )

                custom_field.field_name = name

            # Update other fields
            updatable_fields = ["field_type", "is_required", "options", "order"]
            for field in updatable_fields:
                if field in update_data:
                    setattr(custom_field, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Custom field updated: {custom_field.field_name}")
            return custom_field

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_custom_field: {str(e)}")
            raise Exception("Failed to update custom field due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in update_custom_field: {str(e)}"
            )
            raise Exception("Failed to update custom field")

    def delete_custom_field(self, field_id: str) -> bool:
        """Delete a custom field"""
        try:
            custom_field = self.get_custom_field_by_id(field_id)
            if not custom_field:
                return False

            # Note: Custom field responses in registrations will still exist
            # You might want to handle this differently in production
            db.session.delete(custom_field)
            db.session.commit()

            current_app.logger.info(f"Custom field deleted: {custom_field.field_name}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_custom_field: {str(e)}")
            raise Exception("Failed to delete custom field due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in delete_custom_field: {str(e)}"
            )
            raise Exception("Failed to delete custom field")


class RegistrationLinkService:
    """Service class for registration link-related business logic"""

    def get_registration_link_by_id(self, link_id: str) -> Optional[RegistrationLink]:
        """Get registration link by ID"""
        try:
            return RegistrationLink.query.filter_by(id=link_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_registration_link_by_id: {str(e)}"
            )
            return None

    def get_registration_link_by_token(self, token: str) -> Optional[RegistrationLink]:
        """Get registration link by token"""
        try:
            return RegistrationLink.query.filter_by(link_token=token).first()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_registration_link_by_token: {str(e)}"
            )
            return None

    def get_camp_registration_links(self, camp_id: str) -> List[RegistrationLink]:
        """Get all registration links for a camp"""
        try:
            return (
                RegistrationLink.query.filter_by(camp_id=camp_id)
                .order_by(RegistrationLink.created_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_camp_registration_links: {str(e)}"
            )
            return []

    def create_registration_link(
        self, link_data: Dict[str, Any]
    ) -> Optional[RegistrationLink]:
        """Create a new registration link"""
        try:
            # Validate required fields
            required_fields = ["name", "allowed_categories", "camp_id", "created_by"]
            for field in required_fields:
                if field not in link_data or not link_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Validate allowed_categories
            if (
                not isinstance(link_data["allowed_categories"], list)
                or len(link_data["allowed_categories"]) == 0
            ):
                raise ValueError("At least one category must be allowed")

            # Validate expiration date if provided
            expires_at = link_data.get("expires_at")
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if expires_at <= datetime.now(timezone.utc):
                    raise ValueError("Expiration date must be in the future")

            new_link = RegistrationLink(
                name=link_data["name"].strip(),
                camp_id=link_data["camp_id"],
                allowed_categories=link_data["allowed_categories"],
                created_by=link_data["created_by"],
                expires_at=expires_at,
                usage_limit=link_data.get("usage_limit"),
                is_active=link_data.get("is_active", True),
                form_description=link_data.get("form_description"),
            )

            db.session.add(new_link)
            db.session.commit()

            current_app.logger.info(
                f"New registration link created: {new_link.name} for camp {link_data['camp_id']}"
            )
            return new_link

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in create_registration_link: {str(e)}"
            )
            raise Exception("Failed to create registration link due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in create_registration_link: {str(e)}"
            )

    def update_registration_link(
        self, link_id: str, update_data: Dict[str, Any]
    ) -> Optional[RegistrationLink]:
        """Update registration link information"""
        try:
            link = self.get_registration_link_by_id(link_id)
            if not link:
                return None

            # Validate allowed_categories if being updated
            if "allowed_categories" in update_data:
                allowed_categories = update_data["allowed_categories"]
                if (
                    not isinstance(allowed_categories, list)
                    or len(allowed_categories) == 0
                ):
                    raise ValueError("At least one category must be allowed")

            # Validate expiration date if being updated
            if "expires_at" in update_data and update_data["expires_at"]:
                expires_at = update_data["expires_at"]
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if expires_at <= datetime.now(timezone.utc):
                    raise ValueError("Expiration date must be in the future")

            # Check for duplicate name if name is being updated
            if "name" in update_data:
                name = update_data["name"].strip()
                if not name:
                    raise ValueError("Link name cannot be empty")
                link.name = name

            # Update other fields
            updatable_fields = [
                "allowed_categories",
                "expires_at",
                "usage_limit",
                "is_active",
                "form_description",
            ]
            for field in updatable_fields:
                if field in update_data:
                    setattr(link, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Registration link updated: {link.name}")
            return link

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in update_registration_link: {str(e)}"
            )
            raise Exception("Failed to update registration link due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in update_registration_link: {str(e)}"
            )
            raise Exception("Failed to update registration link")

    def delete_registration_link(self, link_id: str) -> bool:
        """Delete a registration link"""
        try:
            link = self.get_registration_link_by_id(link_id)
            if not link:
                return False

            # Check if link has registrations
            if len(link.registrations) > 0:
                raise ValueError(
                    "Cannot delete registration link with existing registrations"
                )

            db.session.delete(link)
            db.session.commit()

            current_app.logger.info(f"Registration link deleted: {link.name}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in delete_registration_link: {str(e)}"
            )
            raise Exception("Failed to delete registration link due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in delete_registration_link: {str(e)}"
            )
            raise Exception("Failed to delete registration link")

    def toggle_registration_link(self, link_id: str) -> Optional[RegistrationLink]:
        """Toggle registration link active status"""
        try:
            link = self.get_registration_link_by_id(link_id)
            if not link:
                return None

            link.is_active = not link.is_active
            db.session.commit()

            status = "activated" if link.is_active else "deactivated"
            current_app.logger.info(f"Registration link {status}: {link.name}")
            return link

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in toggle_registration_link: {str(e)}"
            )
            raise Exception("Failed to toggle registration link due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in toggle_registration_link: {str(e)}"
            )
            raise Exception("Failed to toggle registration link")


class RegistrationService:
    """Service class for registration-related business logic"""

    def get_registration_by_id(self, registration_id: str, for_api=False) -> Optional[Registration]:
        """Get registration by ID"""
        try:
            registration_data = Registration.query.filter_by(id=registration_id).first()
            return registration_data
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_registration_by_id: {str(e)}"
            )
            return None

    def get_camp_registrations(self, camp_id: str, **kwargs) -> List[Registration]:
        """Get all registrations for a camp"""
        try:
            registrations = Registration.query.filter_by(camp_id=camp_id)
            if kwargs.get("checked_in"):
                registrations = registrations.filter_by(checked_in=True)
            if kwargs.get("church_id"):
                registrations = registrations.filter_by(church_id=kwargs["church_id"])
            if kwargs.get("category_id"):
                registrations = registrations.filter_by(
                    category_id=kwargs["category_id"]
                )
            return registrations.order_by(Registration.registration_date.desc()).all()

        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_camp_registrations: {str(e)}"
            )
            return []

    # @cached(timeout=600, key_prefix='registration_form')  # Cache for 10 minutes
    def get_registration_form(
        self, camp_id: str, link_token: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get registration form structure with caching"""
        try:
            current_app.logger.info(f"Fetching registration form for camp_id: {camp_id}, link_token: {link_token}")
            
            # Get camp
            camp = Camp.query.filter_by(id=camp_id, is_active=True).first()
            if not camp:
                current_app.logger.warning(f"Camp not found or inactive: {camp_id}")
                return None

            # TODO: fix this
            # Check if registration is still open
            # if datetime.now(timezone.utc) > camp.registration_deadline.replace(tzinfo=timezone.utc):
            #     return None

            # Get churches
            churches = (
                Church.query.filter_by(camp_id=camp_id).order_by(Church.name).all()
            )

            # Get custom fields
            custom_fields = (
                CustomField.query.filter_by(camp_id=camp_id)
                .order_by(CustomField.order, CustomField.field_name)
                .all()
            )

            # Get categories based on link type
            registration_link = None
            if link_token:
                registration_link = RegistrationLink.query.filter_by(
                    link_token=link_token
                ).first()
                if not registration_link or not registration_link.is_valid():
                    current_app.logger.warning(f"Invalid or expired registration link: {link_token}")
                    return None

                # Get only allowed categories
                categories = (
                    Category.query.filter(
                        Category.camp_id == camp_id,
                        Category.id.in_(registration_link.allowed_categories),
                    )
                    .order_by(Category.name)
                    .all()
                )
                link_type = "category_specific"
            else:
                # Get all categories
                categories = (
                    Category.query.filter_by(camp_id=camp_id)
                    .order_by(Category.name)
                    .all()
                )
                link_type = "general"

            form_data = {
                "camp": camp.to_dict(),
                "churches": [church.to_dict() for church in churches],
                "categories": [category.to_dict() for category in categories],
                "custom_fields": [field.to_dict() for field in custom_fields],
                "link_type": link_type,
                "registration_link": (
                    registration_link.to_dict() if registration_link else None
                ),
            }
            
            current_app.logger.info(f"Successfully fetched registration form for camp_id: {camp_id}")
            return form_data

        except Exception as e:
            current_app.logger.error(f"Error in get_registration_form: {str(e)}")
            return None

    def create_registration(
        self, registration_data: Dict[str, Any], link_token: str = None
    ) -> Optional[Registration]:
        """Create a new registration"""
        try:
            # Validate required fields
            required_fields = [
                "surname",
                "last_name",
                "age",
                "phone_number",
                "emergency_contact_name",
                "emergency_contact_phone",
                "church_id",
                "category_id",
                "camp_id",
            ]
            for field in required_fields:
                if field not in registration_data or registration_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Get camp and validate
            camp = Camp.query.filter_by(
                id=registration_data["camp_id"], is_active=True
            ).first()
            if not camp:
                raise ValueError("Camp not found or not active")

            # Check registration deadline
            if datetime.now(timezone.utc) > camp.registration_deadline.replace(
                tzinfo=timezone.utc
            ):
                raise ValueError("Registration deadline has passed")

            # Check capacity
            current_registrations = Registration.query.filter_by(
                camp_id=camp.id
            ).count()
            if current_registrations >= camp.capacity:
                raise ValueError("Camp is at full capacity")

            # Validate church exists
            church = Church.query.filter_by(
                id=registration_data["church_id"], camp_id=camp.id
            ).first()
            if not church:
                raise ValueError("Invalid church selection")

            # Validate category exists and is allowed
            category = Category.query.filter_by(
                id=registration_data["category_id"], camp_id=camp.id
            ).first()
            if not category:
                raise ValueError("Invalid category selection")

            # Check for duplicate registration (email, phone, camp_id combination)
            email = registration_data.get("email", "").strip() if registration_data.get("email") else None
            phone_number = registration_data["phone_number"].strip()
            
            if email:  # Only check for duplicates if email is provided
                existing_registration = Registration.query.filter_by(
                    email=email,
                    phone_number=phone_number,
                    camp_id=camp.id
                ).first()
                
                if existing_registration:
                    raise ValueError(
                        f"A registration already exists for this email ({email}) and phone number ({phone_number}) combination for this camp. "
                        f"Existing registration: {existing_registration.surname} {existing_registration.last_name}"
                    )

            # If using registration link, validate category is allowed
            registration_link = None
            if link_token:
                registration_link = RegistrationLink.query.filter_by(
                    link_token=link_token
                ).first()
                if not registration_link or not registration_link.is_valid():
                    raise ValueError("Invalid or expired registration link")

                if str(category.id) not in registration_link.allowed_categories:
                    raise ValueError(
                        "Selected category is not allowed for this registration link"
                    )

            # Calculate total amount
            base_fee = float(camp.base_fee)
            total_amount = base_fee

            if category.discount_amount and category.discount_amount > 0:
                total_amount = max(0, base_fee - float(category.discount_amount))
            elif category.discount_percentage and category.discount_percentage > 0:
                discount = base_fee * (float(category.discount_percentage) / 100)
                total_amount = max(0, base_fee - discount)

            # exiting camp codes
            campers: List[Registration] = Registration.query.filter_by(
                camp_id=camp.id
            ).all()
            existing_codes = [
                camper.to_dict(for_api=True)["camper_code"] for camper in campers
            ]

            camper_code = self._make_code(existing_codes)

            # Create registration
            new_registration = Registration(
                surname=registration_data["surname"].strip(),
                middle_name=registration_data.get("middle_name", "").strip(),
                last_name=registration_data["last_name"].strip(),
                age=int(registration_data["age"]),
                email=(
                    registration_data.get("email", "").strip()
                    if registration_data.get("email")
                    else None
                ),
                phone_number=registration_data["phone_number"].strip(),
                emergency_contact_name=registration_data[
                    "emergency_contact_name"
                ].strip(),
                emergency_contact_phone=registration_data[
                    "emergency_contact_phone"
                ].strip(),
                church_id=registration_data["church_id"],
                category_id=registration_data["category_id"],
                camp_id=registration_data["camp_id"],
                custom_field_responses=registration_data.get(
                    "custom_field_responses", {}
                ),
                total_amount=Decimal(str(total_amount)),
                registration_link_id=(
                    registration_link.id if registration_link else None
                ),
                camper_code=camper_code,
                sex=registration_data["sex"],
            )

            db.session.add(new_registration)

            # Update registration link usage count if applicable
            if registration_link:
                registration_link.usage_count += 1

            db.session.commit()

            current_app.logger.info(
                f"New registration created: {new_registration.surname} {new_registration.last_name} for camp {camp.name}"
            )
            return new_registration

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_registration: {str(e)}")
            raise Exception("Failed to create registration due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in create_registration: {str(e)}"
            )

    def _make_code(self, existing_codes: List[str]) -> str:
        import string
        import random

        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        numbers = "".join(random.choices(string.digits, k=3))
        code = f"{letters}{numbers}"

        if code in existing_codes:
            return self._make_code(existing_codes)

        return code

    def update_registration(
        self, registration_id: str, update_data: Dict[str, Any]
    ) -> Optional[Registration]:
        """Update registration information"""
        try:
            registration = self.get_registration_by_id(registration_id)
            if not registration:
                return None

            # Validate church if being updated
            if "church_id" in update_data:
                church = Church.query.filter_by(
                    id=update_data["church_id"], camp_id=registration.camp_id
                ).first()
                if not church:
                    raise ValueError("Invalid church selection")

            # Validate category if being updated
            if "category_id" in update_data:
                category = Category.query.filter_by(
                    id=update_data["category_id"], camp_id=registration.camp_id
                ).first()
                if not category:
                    raise ValueError("Invalid category selection")

                # Recalculate total amount if category changed
                if str(category.id) != str(registration.category_id):
                    base_fee = float(registration.camp.base_fee)
                    total_amount = base_fee

                    if category.discount_amount and category.discount_amount > 0:
                        total_amount = max(
                            0, base_fee - float(category.discount_amount)
                        )
                    elif (
                        category.discount_percentage
                        and category.discount_percentage > 0
                    ):
                        discount = base_fee * (
                            float(category.discount_percentage) / 100
                        )
                        total_amount = max(0, base_fee - discount)

                    registration.total_amount = Decimal(str(total_amount))

            # Validate age if being updated
            if "age" in update_data and update_data["age"] is not None:
                if int(update_data["age"]) < 1 or int(update_data["age"]) > 150:
                    raise ValueError("Age must be between 1 and 150")

            # Update fields
            updatable_fields = [
                "surname",
                "middle_name",
                "last_name",
                "age",
                "email",
                "phone_number",
                "emergency_contact_name",
                "emergency_contact_phone",
                "church_id",
                "category_id",
                "custom_field_responses",
                "has_paid",
                "has_checked_in",
            ]

            for field in updatable_fields:
                if field in update_data:
                    if (
                        field
                        in [
                            "surname",
                            "middle_name",
                            "last_name",
                            "emergency_contact_name",
                        ]
                        and update_data[field] is not None
                    ):
                        setattr(registration, field, update_data[field].strip())
                    elif field == "age" and update_data[field] is not None:
                        setattr(registration, field, int(update_data[field]))
                    elif field == "email" and update_data[field] is not None:
                        email = (
                            update_data[field].strip() if update_data[field] else None
                        )
                        setattr(registration, field, email)
                    else:
                        setattr(registration, field, update_data[field])

            db.session.commit()

            current_app.logger.info(
                f"Registration updated: {registration.surname} {registration.last_name}"
            )
            return registration

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_registration: {str(e)}")
            raise Exception("Failed to update registration due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in update_registration: {str(e)}"
            )
            raise Exception("Failed to update registration")

    def cancel_registration(self, registration_id: str) -> bool:
        """Cancel/delete a registration"""
        try:
            registration = self.get_registration_by_id(registration_id)
            if not registration:
                return False

            # Update registration link usage count if applicable
            if registration.registration_link_id:
                link = registration.registration_link
                if link and link.usage_count > 0:
                    link.usage_count -= 1

            db.session.delete(registration)
            db.session.commit()

            current_app.logger.info(
                f"Registration cancelled: {registration.surname} {registration.last_name}"
            )
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in cancel_registration: {str(e)}")
            raise Exception("Failed to cancel registration due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in cancel_registration: {str(e)}"
            )
            raise Exception("Failed to cancel registration")

    def update_payment_status(
        self, registration_id: str, payment_data: Dict[str, Any]
    ) -> Optional[Registration]:
        """Update registration payment status"""
        try:
            registration = self.get_registration_by_id(registration_id)
            if not registration:
                return None

            has_paid = payment_data.get("has_paid", False)
            registration.has_paid = has_paid

            # Log payment details for audit trail
            if has_paid:
                payment_method = payment_data.get("payment_method", "manual")
                transaction_id = payment_data.get("transaction_id", "")
                current_app.logger.info(
                    f"Payment marked as paid for registration {registration_id}: "
                    f"method={payment_method}, transaction={transaction_id}"
                )
            else:
                current_app.logger.info(
                    f"Payment marked as unpaid for registration {registration_id}"
                )

            db.session.commit()

            return registration

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in update_payment_status: {str(e)}"
            )
            raise Exception("Failed to update payment status due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in update_payment_status: {str(e)}"
            )
            raise Exception("Failed to update payment status")

    def update_checkin_status(
        self, registration_id: str, checkin_data: Dict[str, Any]
    ) -> Optional[Registration]:
        """Update registration check-in status"""
        try:
            registration = self.get_registration_by_id(registration_id)
            if not registration:
                return None

            has_checked_in = checkin_data.get("has_checked_in", False)
            registration.has_checked_in = has_checked_in

            status = "checked in" if has_checked_in else "checked out"
            current_app.logger.info(
                f"Registration {status}: {registration.surname} {registration.last_name}"
            )

            db.session.commit()

            return registration

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in update_checkin_status: {str(e)}"
            )
            raise Exception("Failed to update check-in status due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in update_checkin_status: {str(e)}"
            )
            raise Exception("Failed to update check-in status")

    def get_registration_by_camper_code(
        self, camper_code: str
    ) -> Optional[Registration]:
        """Get registration by camper code"""
        try:
            return Registration.query.filter_by(camper_code=camper_code).first()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_registration_by_camper_code: {str(e)}"
            )
            return None

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP code"""
        return "".join(random.choices(string.digits, k=6))

    def request_otp(self, camper_code: str) -> Optional[Dict[str, Any]]:
        """Request OTP for a camper using their camper code"""
        try:
            # Find registration by camper code
            registration = self.get_registration_by_camper_code(camper_code)
            if not registration:
                raise ValueError("Invalid camper code")

            # Generate OTP
            otp_code = self.generate_otp()

            # Update registration with OTP
            registration.otp_code = otp_code
            registration.otp_requested = True

            db.session.commit()

            current_app.logger.info(
                f"OTP requested for camper: {registration.surname} {registration.last_name} ({camper_code})"
            )

            return {
                "registration_id": str(registration.id),
                "camper_code": camper_code,
                "otp_code": otp_code,
                "phone_number": registration.phone_number,
                "email": registration.email,
                "camper_name": f"{registration.surname} {registration.last_name}",
            }

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in request_otp: {str(e)}")
            raise Exception("Failed to request OTP due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in request_otp: {str(e)}")
            raise Exception("Failed to request OTP")

    def verify_otp(self, camper_code: str, otp_code: str) -> Optional[Dict[str, Any]]:
        """Verify OTP for a camper and return registration data with payments"""
        try:
            # Find registration by camper code
            registration = self.get_registration_by_camper_code(camper_code)
            if not registration:
                raise ValueError("Invalid camper code")

            # Check if OTP was requested
            if not registration.otp_requested:
                raise ValueError("OTP not requested for this camper")

            # Verify OTP
            if registration.otp_code != otp_code:
                raise ValueError("Invalid OTP code")

            # Clear OTP after successful verification
            registration.otp_code = None
            registration.otp_requested = False

            db.session.commit()

            # Get registration data with payments
            registration_data = registration.to_dict(
                for_api=True, include_payments=True
            )

            # Add camp information
            # registration_data['camp'] = registration.camp.to_dict(for_api=True)
            registration_data["church"] = registration.church.to_dict(
                for_api=False, include_registrations=False
            )
            # registration_data['category'] = registration.category.to_dict(for_api=True)

            current_app.logger.info(
                f"OTP verified successfully for camper: {registration.surname} {registration.last_name} ({camper_code})"
            )

            return registration_data

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in verify_otp: {str(e)}")
            raise Exception("Failed to verify OTP due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in verify_otp: {str(e)}")
            raise Exception("Failed to verify OTP")


class PaymentService:
    """Service class for payment-related business logic"""

    def get_payments_by_camp(self, camp_id: str) -> List[Payment]:
        """Get all payments for a specific camp"""
        try:
            payments = Payment.query.filter_by(camp_id=camp_id).all()
            payments = [payment.to_dict() for payment in payments]
            for payment in payments:
                payment['recorded_by'] = User.query.get(payment['recorded_by']).full_name
            return payments
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in get_payments_by_camp: {str(e)}"
            )
            raise Exception("Failed to get payments due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in get_payments_by_camp: {str(e)}"
            )
            raise Exception("Failed to get payments")

    def get_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get a specific payment by ID"""
        try:
            payment = Payment.query.get(payment_id)
            return payment
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in get_payment_by_id: {str(e)}")
            raise Exception("Failed to get payment due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in get_payment_by_id: {str(e)}")
            raise Exception("Failed to get payment")

    def update_payment(
        self, payment_id: str, payment_data: Dict[str, Any]
    ) -> Optional[Payment]:
        """Update a specific payment by ID"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                return None

            # Update payment fields
            for field in payment_data:
                setattr(payment, field, payment_data[field])

            db.session.commit()

            return payment
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_payment: {str(e)}")
            raise Exception("Failed to update payment due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_payment: {str(e)}")
            raise Exception("Failed to update payment")

    def create_payment(self, payment_data: Dict[str, Any], user_id=None) -> Optional[Payment]:
        """Create a new payment with smart allocation logic"""
        try:
            # Validate required fields
            required_fields = [
                "amount",
                "payment_channel",
                "recorded_by",
                "registration_ids",
                "payment_metadata",
            ]
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"Missing required field: {field}")

            # Get all registrations
            registrations = []
            for registration_id in payment_data["registration_ids"]:
                registration = Registration.query.get(registration_id)
                if registration:
                    registrations.append(registration)

            if not registrations:
                raise ValueError("No valid registrations found")

            # Calculate outstanding balances for each registration
            registration_balances = []
            for registration in registrations:
                outstanding_balance = registration.get_outstanding_balance()
                registration_balances.append({
                    'registration': registration,
                    'outstanding_balance': outstanding_balance
                })

            # Check if all campers owe the same amount
            outstanding_amounts = [rb['outstanding_balance'] for rb in registration_balances]
            all_owe_same_amount = len(set(outstanding_amounts)) == 1

            # Generate financial reference
            financials_number = Financial.query.count()
            financials_referencee = FinancialService().generate_financial_reference(
                financials_number
            )

            # Create main financial record
            financial = Financial(
                camp_id=payment_data["camp_id"],
                amount=payment_data["amount"],
                received_by=payment_data["recorded_by"],
                transaction_type="income",
                transaction_category="camp_payment",
                description="Payment for camp registration",
                reference_number=financials_referencee,
                payment_method=payment_data["payment_channel"],
                recorded_by=payment_data["recorded_by"],
                approved_by=payment_data["recorded_by"],
            )
            db.session.add(financial)

            remaining_payment_amount = float(payment_data["amount"])
            payments_created = []

            if all_owe_same_amount and outstanding_amounts[0] > 0:
                # All campers owe the same amount - split equally and pay from least to largest balance
                amount_per_registration = remaining_payment_amount / len(registrations)
                
                # Sort registrations by current balance (least to largest)
                # Get current total payments for each registration to determine current balance
                registration_balances_with_current = []
                for rb in registration_balances:
                    current_total_paid = rb['registration'].get_total_payments()
                    registration_balances_with_current.append({
                        'registration': rb['registration'],
                        'outstanding_balance': rb['outstanding_balance'],
                        'current_total_paid': current_total_paid
                    })
                
                # Sort by current total paid (ascending) - least paid first
                registration_balances_with_current.sort(key=lambda x: x['current_total_paid'])
                
                for rb in registration_balances_with_current:
                    if remaining_payment_amount <= 0:
                        break
                        
                    registration = rb['registration']
                    payment_amount = min(amount_per_registration, remaining_payment_amount, rb['outstanding_balance'])
                    
                    if payment_amount > 0:
                        payment = Payment(
                            camp_id=payment_data["camp_id"],
                            amount=payment_amount,
                            payment_channel=payment_data["payment_channel"],
                            recorded_by=payment_data["recorded_by"],
                            payment_reference=financials_referencee,
                            payment_metadata=user_id or payment_data["payment_metadata"],
                        )
                        db.session.add(payment)
                        payment.registrations.append(registration)
                        payments_created.append(payment)
                        
                        remaining_payment_amount -= payment_amount
                        
                        # Update payment status
                        registration.has_paid = registration.is_fully_paid()
                        
                        # Send notification
                        self._send_payment_notification(registration, payment_amount)

            else:
                # Different amounts owed - distribute proportionally or handle differently
                # For now, let's use the original equal split logic
                amount_per_registration = remaining_payment_amount / len(registrations)
                
                for registration in registrations:
                    if remaining_payment_amount <= 0:
                        break
                        
                    outstanding_balance = registration.get_outstanding_balance()
                    payment_amount = min(amount_per_registration, remaining_payment_amount, outstanding_balance)
                    
                    if payment_amount > 0:
                        payment = Payment(
                            camp_id=payment_data["camp_id"],
                            amount=payment_amount,
                            payment_channel=payment_data["payment_channel"],
                            recorded_by=payment_data["recorded_by"],
                            payment_reference=financials_referencee,
                            payment_metadata=payment_data["payment_metadata"],
                        )
                        db.session.add(payment)
                        payment.registrations.append(registration)
                        payments_created.append(payment)
                        
                        remaining_payment_amount -= payment_amount
                        
                        # Update payment status
                        registration.has_paid = registration.is_fully_paid()
                        
                        # Send notification
                        self._send_payment_notification(registration, payment_amount)

            # Handle overflow - create new financial record if there's leftover money
            if remaining_payment_amount > 0.01:  # Using small threshold to handle floating point precision
                overflow_financial = Financial(
                    camp_id=payment_data["camp_id"],
                    amount=remaining_payment_amount,
                    received_by=payment_data["recorded_by"],
                    transaction_type="income",
                    transaction_category="camp_payment",
                    description=f"Overflow of Camp payment for ref {financials_referencee}",
                    reference_number=FinancialService().generate_financial_reference(
                        Financial.query.filter_by(camp_id=payment_data["camp_id"]).count() + random.randint(100, 999) + random.randint(100, 999) + random.randint(100, 999)
                    ),
                    payment_method=payment_data["payment_channel"],
                    recorded_by=payment_data["recorded_by"],
                    approved_by=payment_data["recorded_by"],
                )
                db.session.add(overflow_financial)
                
                current_app.logger.info(
                    f"Created overflow financial record: {remaining_payment_amount} for reference {financials_referencee}"
                )

            db.session.commit()

            # Return the first payment created, or create a dummy one if none were created
            if payments_created:
                payments_created = [payment.to_dict() for payment in payments_created]
                for payment in payments_created:
                    payment['recorded_by'] = User.query.get(payment['recorded_by']).full_name
                return payments_created
            else:
                # This shouldn't happen in normal cases, but just in case
                return None

        except ValueError as e:
            raise Exception(f"Failed to create payment due to validation error: {str(e)}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_payment: {str(e)}")
            raise Exception("Failed to create payment due to database error")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_payment: {str(e)}")
            raise Exception("Failed to create payment due to database error")

    def generate_payment_reference(self, payments_number: int) -> str:
        """Generate a random payment reference"""
        payments_number += 1
        random_caps = ''.join(random.choices(string.ascii_uppercase, k=5))
        return f"{random_caps}-{payments_number:05d}"

    def _send_payment_notification(
        self, registration: Registration, amount_received: float
    ) -> None:
        """Send payment notification to camper via SMS and email using threads"""
        try:
            from app.integrations.sms import sms
            from app.integrations.mailer import mailer
            from app.integrations.qr_service import qr_service
            from app.integrations.threading_utils import threaded_service, send_sms_threaded, send_email_threaded

            # Calculate current balance
            outstanding_balance = registration.get_outstanding_balance()
            is_fully_paid = outstanding_balance <= 0

            # Create notification message
            camper_name = f"{registration.surname} {registration.last_name}"
            camp_name = registration.camp.name

            # SMS message
            if is_fully_paid:
                sms_message = (
                    f"🎉 Hi {camper_name}! Payment complete for {camp_name}! "
                    f"You're fully paid (GHS {amount_received:.2f}). "
                    f"Check your email for your QR code. Camper Code: {registration.camper_code}. "
                    f"See you at camp!"
                )
            else:
                sms_message = (
                    f"Hi {camper_name}! We've received your payment of GHS {amount_received:.2f} "
                    f"for {camp_name}. Your outstanding balance is GHS {outstanding_balance:.2f}. "
                    f"See you at camp!"
                )

            # Send SMS notification in thread
            if registration.phone_number:
                threaded_service.execute_in_thread(
                    send_sms_threaded, 
                    sms, 
                    registration.phone_number, 
                    sms_message
                )

            # Send email notification in thread
            if registration.email:
                recipients = [registration.email]
                
                if is_fully_paid:
                    # Send QR code email for fully paid campers
                    try:
                        # Generate QR code
                        qr_code_html = qr_service.generate_camper_qr_code(
                            str(registration.id), 
                            registration.camper_code, 
                            'html'
                        )
                        
                        # Prepare template context
                        template_context = {
                            'camp_name': camp_name,
                            'camper_name': camper_name,
                            'camper_code': registration.camper_code,
                            'total_amount': f"{float(registration.total_amount):.2f}",
                            'camp_start_date': registration.camp.start_date.strftime('%B %d, %Y'),
                            'camp_end_date': registration.camp.end_date.strftime('%B %d, %Y'),
                            'camp_location': registration.camp.location,
                            'qr_code_html': qr_code_html,
                            'support_email': 'support@wedidtech.com'
                        }
                        
                        # Generate HTML email content
                        html_content = mailer.generate_email_text('qr-code-email.html', template_context)
                        
                        # Send QR code email in thread
                        email_subject = f"🎉 Payment Complete + QR Code - {camp_name}"
                        threaded_service.execute_in_thread(
                            send_email_threaded,
                            mailer,
                            recipients,
                            email_subject,
                            html_content,
                            None,
                            True
                        )
                        
                    except Exception as qr_error:
                        current_app.logger.error(f"Failed to prepare QR code email: {str(qr_error)}")
                        # Fallback to regular payment email
                        self._send_regular_payment_email_threaded(registration, amount_received, outstanding_balance, recipients, camp_name, camper_name)
                else:
                    # Send regular payment notification email
                    self._send_regular_payment_email_threaded(registration, amount_received, outstanding_balance, recipients, camp_name, camper_name)

        except Exception as e:
            current_app.logger.error(f"Error in _send_payment_notification: {str(e)}")
            # Don't raise the exception to avoid breaking the payment creation process

    def _send_regular_payment_email_threaded(self, registration: Registration, amount_received: float, outstanding_balance: float, recipients: list, camp_name: str, camper_name: str) -> None:
        """Send regular payment notification email in thread"""
        try:
            from app.integrations.mailer import mailer
            from app.integrations.threading_utils import threaded_service, send_email_threaded
            
            email_subject = f"Payment Received - {camp_name}"
            email_message = f"""
Dear {camper_name},

We're excited to confirm that we've received your payment of GHS {amount_received:.2f} for {camp_name}!

Payment Details:
- Amount Received: GHS {amount_received:.2f}
- Outstanding Balance: GHS {outstanding_balance:.2f}
- Camp: {camp_name}
- Camper Code: {registration.camper_code}

{"You're all set! Your registration is fully paid." if outstanding_balance <= 0 else f"Outstanding Balance: GHS {outstanding_balance:.2f}"}

We can't wait to see you at camp!

Best regards,
The Camp Management Team
            """

            threaded_service.execute_in_thread(
                send_email_threaded,
                mailer,
                recipients,
                email_subject,
                email_message,
                None,
                False
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send regular payment email: {str(e)}")


class FinancialService:  #
    """Service class for financial-related business logic"""

    def get_financial_by_id(self, financial_id: str) -> Optional[Financial]:
        """Get financial record by ID"""
        try:
            financial = Financial.query.filter_by(id=financial_id, is_deleted=False).first()
            if not financial:
                return None
            # Resolve user names for received_by and recorded_by (if stored as IDs)
            try:
                user = User.query.get(financial.received_by)
                financial.received_by = user.full_name if user else financial.received_by
            except Exception:
                pass
            if getattr(financial, "recorded_by", None):
                try:
                    recorder = User.query.get(financial.recorded_by)
                    financial.recorded_by = recorder.full_name if recorder else financial.recorded_by
                except Exception:
                    pass
            return financial
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_financial_by_id: {str(e)}")
            return None

    def create_financial(
        self, financial_data: Dict[str, Any], camp_id: str
    ) -> Optional[Financial]:
        """Create a new financial record"""
        try:
            # Validate required fields
            required_fields = [
                "amount",
                "received_by",
                "transaction_type",
                "transaction_category",
                "date",
                "description",
                "payment_method",
            ]
            for field in required_fields:
                if field not in financial_data or financial_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate transaction type
            valid_transaction_types = ["income", "expense"]
            if financial_data["transaction_type"] not in valid_transaction_types:
                raise ValueError(
                    f"Invalid transaction type. Must be one of: {', '.join(valid_transaction_types)}"
                )

            # Validate transaction category
            valid_categories = [
                "offering",
                "sales",
                "donation",
                "camp_payment",
                "camp_expense",
                "other",
                "pledge",
            ]
            if financial_data["transaction_category"] not in valid_categories:
                raise ValueError(
                    f"Invalid transaction category. Must be one of: {', '.join(valid_categories)}"
                )

            # Validate payment method
            valid_payment_methods = [
                "cash",
                "check",
                "momo",
                "bank_transfer",
                "card",
                "other",
            ]
            if financial_data["payment_method"] not in valid_payment_methods:
                raise ValueError(
                    f"Invalid payment method. Must be one of: {', '.join(valid_payment_methods)}"
                )

            # Validate amount
            if float(financial_data["amount"]) <= 0:
                raise ValueError("Amount must be greater than 0")

            financials_number = Financial.query.filter_by(camp_id=camp_id).count()
            financial_data["reference_number"] = self.generate_financial_reference(
                financials_number
            )
            financial_data["is_deleted"] = False
            financial_data["camp_id"] = camp_id

            # Convert date string to datetime if needed
            if isinstance(financial_data["date"], str):
                financial_data["date"] = datetime.fromisoformat(financial_data["date"])

            financial = Financial(**financial_data)

            db.session.add(financial)
            db.session.commit()

            current_app.logger.info(
                f"New financial record created: {financial.transaction_type} - {financial.description} for camp {camp_id}"
            )
            return financial

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_financial: {str(e)}")
            raise Exception("Failed to create financial record due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_financial: {str(e)}")
            raise Exception("Failed to create financial record")

    def get_financials_by_camp(self, camp_id: str) -> List[Financial]:
        """Get all financial records for a camp"""
        try:
            financials = (
                Financial.query.filter_by(camp_id=camp_id, is_deleted=False)
                .order_by(Financial.date.desc())
                .all()
            )
            financials = [financial.to_dict() for financial in financials]
            for financial in financials:
                user = User.query.get(financial['received_by']) if financial['received_by'] else None 
                financial['received_by'] = (
                    user.full_name if user else financial['received_by']
                )
                recorder = User.query.get(financial['recorded_by']) if financial['recorded_by'] else None
                financial['recorded_by'] = (
                    recorder.full_name if recorder else financial['recorded_by']
                )
            return financials
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_financials_by_camp: {str(e)}"
            )
            raise Exception("Failed to get financial records due to database error")
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error in get_financials_by_camp: {str(e)}"
            )
            raise Exception("Failed to get financial records")

    def update_financial(
        self, financial_id: str, update_data: Dict[str, Any]
    ) -> Optional[Financial]:
        """Update financial record information"""
        try:
            financial = self.get_financial_by_id(financial_id)
            if not financial:
                return None

            # Validate transaction type if being updated
            if "transaction_type" in update_data:
                valid_transaction_types = ["income", "expense"]
                if update_data["transaction_type"] not in valid_transaction_types:
                    raise ValueError(
                        f"Invalid transaction type. Must be one of: {', '.join(valid_transaction_types)}"
                    )

            # Validate transaction category if being updated
            if "transaction_category" in update_data:
                valid_categories = [
                    "offering",
                    "sales",
                    "donation",
                    "camp_payment",
                    "camp_expense",
                    "other",
                ]
                if update_data["transaction_category"] not in valid_categories:
                    raise ValueError(
                        f"Invalid transaction category. Must be one of: {', '.join(valid_categories)}"
                    )

            # Validate payment method if being updated
            if "payment_method" in update_data:
                valid_payment_methods = [
                    "cash",
                    "check",
                    "momo",
                    "bank_transfer",
                    "card",
                    "other",
                ]
                if update_data["payment_method"] not in valid_payment_methods:
                    raise ValueError(
                        f"Invalid payment method. Must be one of: {', '.join(valid_payment_methods)}"
                    )

            # Validate amount if being updated
            if "amount" in update_data and update_data["amount"] is not None:
                if float(update_data["amount"]) <= 0:
                    raise ValueError("Amount must be greater than 0")

            # Update fields
            updatable_fields = [
                "amount",
                "received_by",
                "transaction_type",
                "transaction_category",
                "date",
                "description",
                "payment_method",
                "approved_by",
            ]

            for field in updatable_fields:
                if field in update_data:
                    if field == "date" and update_data[field] is not None:
                        # Convert date string to datetime if needed
                        date_val = update_data[field]
                        if isinstance(date_val, str):
                            date_val = datetime.fromisoformat(date_val)
                        setattr(financial, field, date_val)
                    elif field == "amount" and update_data[field] is not None:
                        setattr(financial, field, Decimal(str(update_data[field])))
                    else:
                        if update_data[field] is not None:
                            value = (
                                update_data[field].strip()
                                if isinstance(update_data[field], str)
                                else update_data[field]
                            )
                            setattr(financial, field, value)

            db.session.commit()

            current_app.logger.info(
                f"Financial record updated: {financial.description}"
            )
            return financial

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_financial: {str(e)}")
            raise Exception("Failed to update financial record due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_financial: {str(e)}")
            raise Exception("Failed to update financial record")

    def delete_financial(self, financial_id: str) -> bool:
        """Soft delete a financial record"""
        try:
            financial = self.get_financial_by_id(financial_id)
            if not financial:
                return False

            # Soft delete by setting is_deleted to True
            financial.is_deleted = True
            db.session.commit()

            current_app.logger.info(
                f"Financial record deleted: {financial.description}"
            )
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_financial: {str(e)}")
            raise Exception("Failed to delete financial record due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_financial: {str(e)}")
            raise Exception("Failed to delete financial record")

    def generate_financial_reference(self, financials_number: int) -> str:
        """Generate a financial reference number"""
        financials_number += 1
        random_caps = ''.join(random.choices(string.ascii_uppercase, k=5))
        return f"{random_caps}-{financials_number:05d}"


class InventoryService:
    """Service class for inventory-related business logic"""

    def get_inventory_by_id(
        self, inventory_id: str, camp_id: str
    ) -> Optional[Inventory]:
        """Get inventory record by ID"""
        try:
            return Inventory.query.filter_by(
                id=inventory_id, camp_id=camp_id, is_deleted=False
            ).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_inventory_by_id: {str(e)}")
            return None

    def get_inventory_by_camp(self, camp_id: str) -> List[Inventory]:
        """Get all inventory records for a camp"""
        try:
            return Inventory.query.filter_by(camp_id=camp_id, is_deleted=False).all()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_inventory_by_camp: {str(e)}"
            )
            return []

    def create_inventory(self, inventory_data: Dict[str, Any]) -> Optional[Inventory]:
        """Create a new inventory record"""
        try:
            # Validate required fields
            required_fields = ["cost", "name", "inventory_type", "quantity", "camp_id"]
            for field in required_fields:
                if field not in inventory_data or inventory_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate cost and quantity
            if float(inventory_data["cost"]) < 0:
                raise ValueError("Cost must be non-negative")

            if int(inventory_data["quantity"]) < 0:
                raise ValueError("Quantity must be non-negative")

            # Validate inventory type
            valid_types = [
                "shirts",
                "hoodies",
                "wristbands",
                "sweat-shirts",
                "keychain",
                "caps",
                "other",
            ]
            if inventory_data["inventory_type"] not in valid_types:
                raise ValueError(
                    f"Invalid inventory type. Must be one of: {', '.join(valid_types)}"
                )

            inventory_data["is_deleted"] = False
            inventory = Inventory(**inventory_data)
            db.session.add(inventory)
            db.session.commit()

            current_app.logger.info(
                f"New inventory item created: {inventory.name} for camp {inventory_data['camp_id']}"
            )
            return inventory

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_inventory: {str(e)}")
            raise Exception("Failed to create inventory due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_inventory: {str(e)}")
            raise Exception("Failed to create inventory")

    def update_inventory(
        self, inventory_id: str, update_data: Dict[str, Any], camp_id: str
    ) -> Optional[Inventory]:
        """Update inventory record information"""
        try:
            inventory = self.get_inventory_by_id(inventory_id, camp_id)
            if not inventory:
                return None

            # Validate cost and quantity if being updated
            if "cost" in update_data and update_data["cost"] is not None:
                if float(update_data["cost"]) < 0:
                    raise ValueError("Cost must be non-negative")

            if "quantity" in update_data and update_data["quantity"] is not None:
                if int(update_data["quantity"]) < 0:
                    raise ValueError("Quantity must be non-negative")

            # Validate inventory type if being updated
            if "inventory_type" in update_data:
                valid_types = [
                    "shirts",
                    "hoodies",
                    "wristbands",
                    "sweat-shirts",
                    "keychain",
                    "caps",
                    "other",
                ]
                if update_data["inventory_type"] not in valid_types:
                    raise ValueError(
                        f"Invalid inventory type. Must be one of: {', '.join(valid_types)}"
                    )

            # Update fields
            updatable_fields = [
                "cost",
                "name",
                "description",
                "inventory_type",
                "quantity",
            ]
            for field in updatable_fields:
                if field in update_data:
                    if field == "cost" and update_data[field] is not None:
                        setattr(inventory, field, Decimal(str(update_data[field])))
                    elif field == "quantity" and update_data[field] is not None:
                        setattr(inventory, field, int(update_data[field]))
                    else:
                        if update_data[field] is not None:
                            value = (
                                update_data[field].strip()
                                if isinstance(update_data[field], str)
                                else update_data[field]
                            )
                            setattr(inventory, field, value)

            db.session.commit()

            current_app.logger.info(f"Inventory updated: {inventory.name}")
            return inventory

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_inventory: {str(e)}")
            raise Exception("Failed to update inventory due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_inventory: {str(e)}")
            raise Exception("Failed to update inventory")

    def delete_inventory(self, inventory_id: str, camp_id: str) -> bool:
        """Soft delete an inventory record"""
        try:
            inventory = self.get_inventory_by_id(inventory_id, camp_id)
            if not inventory:
                return False

            # Soft delete by setting is_deleted to True
            inventory.is_deleted = True
            db.session.commit()

            current_app.logger.info(f"Inventory deleted: {inventory.name}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_inventory: {str(e)}")
            raise Exception("Failed to delete inventory due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_inventory: {str(e)}")
            raise Exception("Failed to delete inventory")


class PurchaseService:
    """Service class for purchase-related business logic"""

    def get_purchase_by_id(
        self, purchase_id: str, camp_id: str
    ) -> Optional["Purchase"]:
        """Get purchase record by ID"""
        try:
            from .models import Purchase

            return Purchase.query.filter_by(id=purchase_id, camp_id=camp_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_purchase_by_id: {str(e)}")
            return None

    def get_purchases_by_camp(self, camp_id: str) -> List["Purchase"]:
        """Get all purchase records for a camp"""
        try:
            from .models import Purchase

            purchases = (
                Purchase.query.filter_by(camp_id=camp_id)
                .order_by(Purchase.purchase_date.desc())
                .all()
            )
            for purchase in purchases:
                user = User.query.get(purchase.sold_by)
                purchase.sold_by = user.full_name if user else purchase.sold_by
            return purchases
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_purchases_by_camp: {str(e)}"
            )
            return []

    def create_purchase(self, purchase_data: Dict[str, Any]) -> Optional["Purchase"]:
        """Create a new purchase record"""
        try:
            from .models import Purchase

            # Validate required fields - now supporting both old and new format
            if "items" in purchase_data and purchase_data["items"]:
                # New format with items and quantities
                required_fields = ["amount", "camp_id", "items", "sold_by"]
                for field in required_fields:
                    if field not in purchase_data or purchase_data[field] is None:
                        raise ValueError(f"Missing required field: {field}")

                # Validate items structure
                if (
                    not isinstance(purchase_data["items"], list)
                    or len(purchase_data["items"]) == 0
                ):
                    raise ValueError("Items must be a non-empty list")

                # Validate each item
                inventory_ids = []
                total_quantity = 0
                for item in purchase_data["items"]:
                    if not isinstance(item, dict):
                        raise ValueError("Each item must be a dictionary")
                    if "inventory_id" not in item or "quantity" not in item:
                        raise ValueError(
                            "Each item must have inventory_id and quantity"
                        )
                    if not isinstance(item["quantity"], int) or item["quantity"] < 1:
                        raise ValueError("Quantity must be a positive integer")

                    # Validate inventory exists
                    inventory_svc = InventoryService()
                    inventory = inventory_svc.get_inventory_by_id(
                        item["inventory_id"], purchase_data["camp_id"]
                    )
                    if not inventory:
                        raise ValueError(
                            f"Inventory item {item['inventory_id']} not found"
                        )

                    # Check if enough quantity is available
                    if inventory.quantity < item["quantity"]:
                        raise ValueError(
                            f"Not enough quantity available for {inventory.name}. Available: {inventory.quantity}, Requested: {item['quantity']}"
                        )

                    inventory_ids.append(item["inventory_id"])
                    total_quantity += item["quantity"]

                # Create backward-compatible inventory_ids string
                purchase_data["inventory_ids"] = ",".join(inventory_ids)

                # Update inventory quantities
                inventory_svc = InventoryService()
                for item in purchase_data["items"]:
                    inventory = inventory_svc.get_inventory_by_id(
                        item["inventory_id"], purchase_data["camp_id"]
                    )
                    inventory.quantity -= item["quantity"]

            else:
                # Old format with inventory_ids string - maintain backward compatibility
                required_fields = ["amount", "camp_id", "inventory_ids", "sold_by"]
                for field in required_fields:
                    if field not in purchase_data or purchase_data[field] is None:
                        raise ValueError(f"Missing required field: {field}")

                # Validate inventory_ids format (should be comma-separated string)
                if not isinstance(purchase_data["inventory_ids"], str):
                    raise ValueError("inventory_ids must be a comma-separated string")

                # Convert old format to new format for storage
                inventory_ids = purchase_data["inventory_ids"].split(",")
                items = []
                for inventory_id in inventory_ids:
                    inventory_id = inventory_id.strip()
                    if inventory_id:
                        items.append({"inventory_id": inventory_id, "quantity": 1})
                purchase_data["items"] = items

            # Validate amount
            if float(purchase_data["amount"]) <= 0:
                raise ValueError("Amount must be greater than 0")

            purchase = Purchase(**purchase_data)
            db.session.add(purchase)
            db.session.commit()

            current_app.logger.info(
                f"New purchase created: {purchase.amount} for camp {purchase_data['camp_id']}"
            )
            return purchase

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_purchase: {str(e)}")
            raise Exception("Failed to create purchase due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_purchase: {str(e)}")
            raise Exception("Failed to create purchase")

    def update_purchase(
        self, purchase_id: str, update_data: Dict[str, Any], camp_id: str
    ) -> Optional["Purchase"]:
        """Update purchase record information"""
        try:
            purchase = self.get_purchase_by_id(purchase_id, camp_id)
            if not purchase:
                return None

            # Validate amount if being updated
            if "amount" in update_data and update_data["amount"] is not None:
                if float(update_data["amount"]) <= 0:
                    raise ValueError("Amount must be greater than 0")

            # Validate inventory_ids format if being updated
            if (
                "inventory_ids" in update_data
                and update_data["inventory_ids"] is not None
            ):
                if not isinstance(update_data["inventory_ids"], str):
                    raise ValueError("inventory_ids must be a comma-separated string")

            # Update fields
            updatable_fields = ["amount", "inventory_ids", "sold_by"]
            for field in updatable_fields:
                if field in update_data:
                    if field == "amount" and update_data[field] is not None:
                        setattr(purchase, field, Decimal(str(update_data[field])))
                    else:
                        setattr(purchase, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Purchase updated: {purchase.id}")
            return purchase

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_purchase: {str(e)}")
            raise Exception("Failed to update purchase due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_purchase: {str(e)}")
            raise Exception("Failed to update purchase")

    def delete_purchase(self, purchase_id: str, camp_id: str) -> bool:
        """Delete a purchase record"""
        try:
            purchase = self.get_purchase_by_id(purchase_id, camp_id)
            if not purchase:
                return False

            db.session.delete(purchase)
            db.session.commit()

            current_app.logger.info(f"Purchase deleted: {purchase.id}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_purchase: {str(e)}")
            raise Exception("Failed to delete purchase due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_purchase: {str(e)}")
            raise Exception("Failed to delete purchase")


class PledgeService:
    """Service class for pledge-related business logic"""

    def get_pledge_by_id(self, pledge_id: str, camp_id: str) -> Optional[Pledge]:
        """Get pledge record by ID"""
        try:
            return Pledge.query.filter_by(id=pledge_id, camp_id=camp_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_pledge_by_id: {str(e)}")
            return None

    def get_pledges_by_camp(self, camp_id: str) -> List[Pledge]:
        """Get all pledge records for a camp"""
        try:
            return (
                Pledge.query.filter_by(camp_id=camp_id)
                .order_by(Pledge.pledge_date.desc())
                .all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_pledges_by_camp: {str(e)}")
            return []

    def get_pledges_by_camper(self, camper_id: str, camp_id: str) -> List[Pledge]:
        """Get all pledges for a specific camper"""
        try:
            return (
                Pledge.query.filter_by(camper_id=camper_id, camp_id=camp_id)
                .order_by(Pledge.pledge_date.desc())
                .all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_pledges_by_camper: {str(e)}"
            )
            return []

    def create_pledge(self, pledge_data: Dict[str, Any]) -> Optional[Pledge]:
        """Create a new pledge record"""
        try:
            # Validate required fields
            required_fields = ["amount", "camper_id", "camp_id", "status"]
            for field in required_fields:
                if field not in pledge_data or pledge_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate amount
            if float(pledge_data["amount"]) <= 0:
                raise ValueError("Amount must be greater than 0")

            # Validate status
            valid_statuses = ["pending", "fulfilled", "cancelled"]
            if pledge_data["status"] not in valid_statuses:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )

            # Validate camper exists and belongs to the camp
            camper = Registration.query.filter_by(
                id=pledge_data["camper_id"], camp_id=pledge_data["camp_id"]
            ).first()
            if not camper:
                raise ValueError(
                    "Invalid camper selection or camper does not belong to this camp"
                )

            pledge = Pledge(
                amount=Decimal(str(pledge_data["amount"])),
                camper_id=pledge_data["camper_id"],
                camp_id=pledge_data["camp_id"],
                status=pledge_data["status"],
            )

            db.session.add(pledge)
            db.session.commit()

            current_app.logger.info(
                f"New pledge created: {pledge.amount} for camper {pledge_data['camper_id']} in camp {pledge_data['camp_id']}"
            )
            return pledge

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_pledge: {str(e)}")
            raise Exception("Failed to create pledge due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_pledge: {str(e)}")
            raise Exception("Failed to create pledge")

    def update_pledge(
        self, pledge_id: str, update_data: Dict[str, Any], camp_id: str
    ) -> Optional[Pledge]:
        """Update pledge record information"""
        try:
            pledge = self.get_pledge_by_id(pledge_id, camp_id)
            if not pledge:
                return None

            # Validate amount if being updated
            if "amount" in update_data and update_data["amount"] is not None:
                if float(update_data["amount"]) <= 0:
                    raise ValueError("Amount must be greater than 0")

            # Validate status if being updated
            if "status" in update_data:
                valid_statuses = ["pending", "fulfilled", "cancelled"]
                if update_data["status"] not in valid_statuses:
                    raise ValueError(
                        f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                    )

            # Validate camper if being updated
            if "camper_id" in update_data:
                camper = Registration.query.filter_by(
                    id=update_data["camper_id"], camp_id=camp_id
                ).first()
                if not camper:
                    raise ValueError(
                        "Invalid camper selection or camper does not belong to this camp"
                    )

            # Update fields
            updatable_fields = ["amount", "camper_id", "status"]
            for field in updatable_fields:
                if field in update_data:
                    if field == "amount" and update_data[field] is not None:
                        setattr(pledge, field, Decimal(str(update_data[field])))
                    else:
                        setattr(pledge, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Pledge updated: {pledge.id}")
            return pledge

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_pledge: {str(e)}")
            raise Exception("Failed to update pledge due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_pledge: {str(e)}")
            raise Exception("Failed to update pledge")

    def delete_pledge(self, pledge_id: str, camp_id: str) -> bool:
        """Delete a pledge record"""
        try:
            pledge = self.get_pledge_by_id(pledge_id, camp_id)
            if not pledge:
                return False

            db.session.delete(pledge)
            db.session.commit()

            current_app.logger.info(f"Pledge deleted: {pledge.id}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_pledge: {str(e)}")
            raise Exception("Failed to delete pledge due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_pledge: {str(e)}")
            raise Exception("Failed to delete pledge")

    def get_camp_pledge_stats(self, camp_id: str) -> Dict[str, Any]:
        """Get pledge statistics for a camp"""
        try:
            pledges = self.get_pledges_by_camp(camp_id)

            total_pledges = len(pledges)
            total_amount = sum(float(pledge.amount) for pledge in pledges)

            pending_pledges = [p for p in pledges if p.status == "pending"]
            fulfilled_pledges = [p for p in pledges if p.status == "fulfilled"]
            cancelled_pledges = [p for p in pledges if p.status == "cancelled"]

            pending_amount = sum(float(pledge.amount) for pledge in pending_pledges)
            fulfilled_amount = sum(float(pledge.amount) for pledge in fulfilled_pledges)
            cancelled_amount = sum(float(pledge.amount) for pledge in cancelled_pledges)

            return {
                "total_pledges": total_pledges,
                "total_amount": total_amount,
                "pending_pledges": len(pending_pledges),
                "pending_amount": pending_amount,
                "fulfilled_pledges": len(fulfilled_pledges),
                "fulfilled_amount": fulfilled_amount,
                "cancelled_pledges": len(cancelled_pledges),
                "cancelled_amount": cancelled_amount,
                "fulfillment_rate": (
                    (len(fulfilled_pledges) / total_pledges * 100)
                    if total_pledges > 0
                    else 0
                ),
            }

        except Exception as e:
            current_app.logger.error(f"Error in get_camp_pledge_stats: {str(e)}")
            return {
                "total_pledges": 0,
                "total_amount": 0,
                "pending_pledges": 0,
                "pending_amount": 0,
                "fulfilled_pledges": 0,
                "fulfilled_amount": 0,
                "cancelled_pledges": 0,
                "cancelled_amount": 0,
                "fulfillment_rate": 0,
            }

    def change_pledge_status(
        self, pledge_id: str, new_status: str, camp_id: str
    ) -> Optional[Pledge]:
        """Change the status of a pledge between pending, fulfilled, and cancelled"""
        try:
            pledge = self.get_pledge_by_id(pledge_id, camp_id)
            if not pledge:
                return None

            # Validate status
            valid_statuses = ["pending", "fulfilled", "cancelled"]
            if new_status not in valid_statuses:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )

            # Check if status is actually changing
            if pledge.status == new_status:
                raise ValueError(f"Pledge is already {new_status}")

            old_status = pledge.status
            pledge.status = new_status

            # If changing to fulfilled, create a financial record for income
            if new_status == "fulfilled" and old_status != "fulfilled":
                financial_service = FinancialService()
                financial_data = {
                    "amount": float(pledge.amount),
                    "received_by": "System",  # You might want to pass the user who fulfilled it
                    "transaction_type": "income",
                    "transaction_category": "pledge",
                    "date": datetime.now(timezone.utc),
                    "description": f"Pledge fulfillment - {pledge.amount}",
                    "payment_method": "other",
                    "approved_by": "System",
                }
                financial_service.create_financial(financial_data, camp_id)

            # If changing from fulfilled to another status, you might want to reverse the financial record
            # This is optional based on your business logic
            elif old_status == "fulfilled" and new_status != "fulfilled":
                # Optional: Create a reversal financial record
                financial_service = FinancialService()
                financial_data = {
                    "amount": float(pledge.amount),
                    "received_by": "System",
                    "transaction_type": "expense",
                    "transaction_category": "other",
                    "date": datetime.now(timezone.utc),
                    "description": f"Pledge status change reversal - {pledge.amount}",
                    "payment_method": "other",
                    "approved_by": "System",
                }
                financial_service.create_financial(financial_data, camp_id)

            db.session.commit()

            current_app.logger.info(
                f"Pledge status changed: {pledge.id} from {old_status} to {new_status}"
            )
            return pledge

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Database error in change_pledge_status: {str(e)}"
            )
            raise Exception("Failed to change pledge status due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Unexpected error in change_pledge_status: {str(e)}"
            )
            raise Exception("Failed to change pledge status")


class RoomService:
    """Service class for room-related business logic"""

    def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        try:
            return Room.query.filter_by(id=room_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_room_by_id: {str(e)}")
            return None

    def get_camp_rooms(self, camp_id: str) -> List[Room]:
        """Get all rooms for a camp"""
        try:
            return Room.query.filter_by(camp_id=camp_id).order_by(Room.hostel_name, Room.block, Room.room_number).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_rooms: {str(e)}")
            return []

    def create_room(self, room_data: Dict[str, Any]) -> Optional[Room]:
        """Create a new room"""
        try:
            # Validate required fields
            required_fields = ["hostel_name", "room_number", "room_gender", "camp_id"]
            for field in required_fields:
                if field not in room_data or not room_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Validate room_gender
            valid_genders = ["male", "female", "other"]
            if room_data["room_gender"] not in valid_genders:
                raise ValueError(f"Invalid room gender. Must be one of: {', '.join(valid_genders)}")

            # Validate numeric fields
            if "room_capacity" in room_data and room_data["room_capacity"] is not None:
                if int(room_data["room_capacity"]) < 1:
                    raise ValueError("Room capacity must be at least 1")

            if "extra_beds" in room_data and room_data["extra_beds"] is not None:
                if int(room_data["extra_beds"]) < 0:
                    raise ValueError("Extra beds must be non-negative")

            # Check for duplicate room in the same camp
            existing_room = Room.query.filter_by(
                hostel_name=room_data["hostel_name"].strip(),
                block=room_data.get("block", "").strip() if room_data.get("block") else None,
                room_number=room_data["room_number"].strip(),
                camp_id=room_data["camp_id"]
            ).first()

            if existing_room:
                raise ValueError("A room with this hostel name, block, and room number already exists in this camp")

            new_room = Room(
                hostel_name=room_data["hostel_name"].strip(),
                block=room_data.get("block", "").strip() if room_data.get("block") else None,
                room_number=room_data["room_number"].strip(),
                room_capacity=int(room_data.get("room_capacity", 1)),
                is_special_room=room_data.get("is_special_room", False),
                extra_beds=int(room_data.get("extra_beds", 0)),
                room_gender=room_data["room_gender"],
                is_damaged=room_data.get("is_damaged", False),
                misc_info=room_data.get("misc_info"),
                camp_id=room_data["camp_id"],
                adjoining_to=room_data.get("adjoining_to")
            )

            db.session.add(new_room)
            db.session.commit()

            current_app.logger.info(f"New room created: {new_room.hostel_name} {new_room.block}-{new_room.room_number} for camp {room_data['camp_id']}")
            return new_room

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_room: {str(e)}")
            raise Exception("Failed to create room due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_room: {str(e)}")
            raise Exception("Failed to create room")

    def update_room(self, room_id: str, update_data: Dict[str, Any]) -> Optional[Room]:
        """Update room information"""
        try:
            room = self.get_room_by_id(room_id)
            if not room:
                return None

            # Validate room_gender if being updated
            if "room_gender" in update_data:
                valid_genders = ["male", "female", "other"]
                if update_data["room_gender"] not in valid_genders:
                    raise ValueError(f"Invalid room gender. Must be one of: {', '.join(valid_genders)}")

            # Validate numeric fields if being updated
            if "room_capacity" in update_data and update_data["room_capacity"] is not None:
                if int(update_data["room_capacity"]) < 1:
                    raise ValueError("Room capacity must be at least 1")

            if "extra_beds" in update_data and update_data["extra_beds"] is not None:
                if int(update_data["extra_beds"]) < 0:
                    raise ValueError("Extra beds must be non-negative")

            # Check for duplicate room if key fields are being updated
            if any(field in update_data for field in ["hostel_name", "block", "room_number"]):
                hostel_name = update_data.get("hostel_name", room.hostel_name).strip()
                block = update_data.get("block", room.block)
                if block:
                    block = block.strip()
                room_number = update_data.get("room_number", room.room_number).strip()

                existing_room = Room.query.filter_by(
                    hostel_name=hostel_name,
                    block=block,
                    room_number=room_number,
                    camp_id=room.camp_id
                ).filter(Room.id != room_id).first()

                if existing_room:
                    raise ValueError("A room with this hostel name, block, and room number already exists in this camp")

            # Update fields
            updatable_fields = [
                "hostel_name", "block", "room_number", "room_capacity", 
                "is_special_room", "extra_beds", "room_gender", "is_damaged", 
                "misc_info", "adjoining_to"
            ]
            
            for field in updatable_fields:
                if field in update_data:
                    if field in ["room_capacity", "extra_beds"] and update_data[field] is not None:
                        setattr(room, field, int(update_data[field]))
                    elif field in ["hostel_name", "room_number"] and update_data[field] is not None:
                        setattr(room, field, update_data[field].strip())
                    elif field == "block" and update_data[field] is not None:
                        setattr(room, field, update_data[field].strip() if update_data[field] else None)
                    else:
                        setattr(room, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Room updated: {room.hostel_name} {room.block}-{room.room_number}")
            return room

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_room: {str(e)}")
            raise Exception("Failed to update room due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_room: {str(e)}")
            raise Exception("Failed to update room")

    def delete_room(self, room_id: str) -> bool:
        """Delete a room"""
        try:
            room = self.get_room_by_id(room_id)
            if not room:
                return False

            # Check if room has active allocations
            active_allocations = [allocation for allocation in room.room_allocations if allocation.is_active]
            if active_allocations:
                raise ValueError("Cannot delete room with active allocations")

            db.session.delete(room)
            db.session.commit()

            current_app.logger.info(f"Room deleted: {room.hostel_name} {room.block}-{room.room_number}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_room: {str(e)}")
            raise Exception("Failed to delete room due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_room: {str(e)}")
            raise Exception("Failed to delete room")

    def get_available_rooms(self, camp_id: str, gender: str = None) -> List[Room]:
        """Get available rooms for a camp, optionally filtered by gender"""
        try:
            query = Room.query.filter_by(camp_id=camp_id, is_damaged=False)
            
            if gender:
                query = query.filter_by(room_gender=gender)
            
            rooms = query.order_by(Room.hostel_name, Room.block, Room.room_number).all()
            
            # Filter out full rooms
            available_rooms = [room for room in rooms if not room.is_full()]
            
            return available_rooms
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_available_rooms: {str(e)}")
            return []


class RoomAllocationService:
    """Service class for room allocation-related business logic"""

    def get_allocation_by_id(self, allocation_id: str) -> Optional[RoomAllocation]:
        """Get room allocation by ID"""
        try:
            return RoomAllocation.query.filter_by(id=allocation_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_allocation_by_id: {str(e)}")
            return None

    def get_camp_allocations(self, camp_id: str, active_only: bool = True) -> List[RoomAllocation]:
        """Get all room allocations for a camp"""
        try:
            query = RoomAllocation.query.filter_by(camp_id=camp_id)
            if active_only:
                query = query.filter_by(is_active=True)
            
            return query.order_by(RoomAllocation.allocation_date.desc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_allocations: {str(e)}")
            return []

    def get_registration_allocation(self, registration_id: str, camp_id: str) -> Optional[RoomAllocation]:
        """Get active room allocation for a registration"""
        try:
            return RoomAllocation.query.filter_by(
                registration_id=registration_id,
                camp_id=camp_id,
                is_active=True
            ).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_registration_allocation: {str(e)}")
            return None

    def allocate_room(self, allocation_data: Dict[str, Any], allocated_by: str) -> List[RoomAllocation]:
        """Allocate multiple registrations to a room"""
        try:
            # Validate required fields
            required_fields = ["room_id", "registration_ids", "camp_id"]
            for field in required_fields:
                if field not in allocation_data or not allocation_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Get room and validate
            room_service = RoomService()
            room = room_service.get_room_by_id(allocation_data["room_id"])
            if not room:
                raise ValueError("Room not found")

            if room.camp_id != allocation_data["camp_id"]:
                raise ValueError("Room does not belong to this camp")

            if room.is_damaged:
                raise ValueError("Cannot allocate to a damaged room")

            # Get registrations and validate
            registration_ids = allocation_data["registration_ids"]
            if not isinstance(registration_ids, list) or len(registration_ids) == 0:
                raise ValueError("At least one registration ID must be provided")

            registrations = []
            for reg_id in registration_ids:
                registration = Registration.query.filter_by(id=reg_id, camp_id=allocation_data["camp_id"]).first()
                if not registration:
                    raise ValueError(f"Registration {reg_id} not found or does not belong to this camp")
                
                # Check if registration already has an active allocation
                existing_allocation = self.get_registration_allocation(reg_id, allocation_data["camp_id"])
                if existing_allocation:
                    raise ValueError(f"Registration {reg_id} ({registration.surname} {registration.last_name}) already has an active room allocation")
                
                registrations.append(registration)

            # Check room capacity
            current_occupancy = room.get_current_occupancy()
            available_capacity = room.get_available_capacity()
            
            if len(registrations) > available_capacity:
                raise ValueError(f"Room has only {available_capacity} available spaces, but {len(registrations)} registrations were provided")

            # Check gender compatibility
            for registration in registrations:
                if room.room_gender != "other" and registration.sex != "other":
                    if room.room_gender != registration.sex:
                        raise ValueError(f"Gender mismatch: Room is for {room.room_gender} but registration {registration.surname} {registration.last_name} is {registration.sex}")

            # Create allocations
            allocations = []
            for registration in registrations:
                allocation = RoomAllocation(
                    room_id=allocation_data["room_id"],
                    registration_id=registration.id,
                    camp_id=allocation_data["camp_id"],
                    allocated_by=allocated_by,
                    notes=allocation_data.get("notes")
                )
                
                db.session.add(allocation)
                allocations.append(allocation)
                
                # Mark registration as checked in when allocated a room
                registration.has_checked_in = True

            db.session.commit()

            # Send notifications to allocated campers
            for allocation in allocations:
                self._send_allocation_notification(allocation)

            current_app.logger.info(f"Room allocated: {len(allocations)} registrations allocated to room {room.hostel_name} {room.block}-{room.room_number} and marked as checked in")
            return allocations

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in allocate_room: {str(e)}")
            raise Exception("Failed to allocate room due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in allocate_room: {str(e)}")
            raise Exception("Failed to allocate room")

    def update_allocation(self, allocation_id: str, update_data: Dict[str, Any]) -> Optional[RoomAllocation]:
        """Update room allocation information"""
        try:
            allocation = self.get_allocation_by_id(allocation_id)
            if not allocation:
                return None

            # Update fields
            updatable_fields = ["is_active", "notes"]
            for field in updatable_fields:
                if field in update_data:
                    setattr(allocation, field, update_data[field])

            db.session.commit()

            current_app.logger.info(f"Room allocation updated: {allocation.id}")
            return allocation

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_allocation: {str(e)}")
            raise Exception("Failed to update allocation due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_allocation: {str(e)}")
            raise Exception("Failed to update allocation")

    def deallocate_room(self, allocation_id: str) -> bool:
        """Deallocate a room (set allocation as inactive and mark registration as not checked in)"""
        try:
            allocation = self.get_allocation_by_id(allocation_id)
            if not allocation:
                return False

            # Mark registration as not checked in when deallocating room
            registration = allocation.registration
            if registration:
                registration.has_checked_in = False

            db.session.delete(allocation)
            db.session.commit()

            current_app.logger.info(f"Room deallocated: allocation {allocation.id} and registration marked as not checked in")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in deallocate_room: {str(e)}")
            raise Exception("Failed to deallocate room due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in deallocate_room: {str(e)}")
            raise Exception("Failed to deallocate room")

    def _send_allocation_notification(self, allocation: RoomAllocation) -> None:
        """Send room allocation notification to camper via SMS and email using threads"""
        try:
            from app.integrations.sms import sms
            from app.integrations.mailer import mailer
            from app.integrations.threading_utils import threaded_service, send_sms_threaded, send_email_threaded

            registration = allocation.registration
            room = allocation.room
            camp_name = registration.camp.name
            camper_name = f"{registration.surname} {registration.last_name}"

            # Create room description
            room_description = f"{room.hostel_name}"
            if room.block:
                room_description += f", Block {room.block}"
            room_description += f", Room {room.room_number}"

            # SMS message
            sms_message = (
                f"Hi {camper_name}! You've been allocated to {room_description} "
                f"for {camp_name}. Your camper code is {registration.camper_code}. "
                f"See you at service!"
            )

            # Email message
            email_subject = f"Room Allocation - {camp_name}"
            email_message = f"""
Dear {camper_name},

Great news! Your room has been allocated for {camp_name}.

Room Details:
- Hostel: {room.hostel_name}
- Block: {room.block or 'N/A'}
- Room Number: {room.room_number}
- Camper Code: {registration.camper_code}

Additional Information:
- Room Capacity: {room.room_capacity + room.extra_beds} people
{f"- Notes: {allocation.notes}" if allocation.notes else ""}

We're excited to have you at camp!

Best regards,
The Camp Management Team
            """

            # Send SMS notification in thread
            if registration.phone_number:
                threaded_service.execute_in_thread(
                    send_sms_threaded,
                    sms,
                    registration.phone_number,
                    sms_message
                )

            # Send email notification in thread
            if registration.email:
                recipients = [registration.email]
                threaded_service.execute_in_thread(
                    send_email_threaded,
                    mailer,
                    recipients,
                    email_subject,
                    email_message,
                    None,
                    False
                )

        except Exception as e:
            current_app.logger.error(f"Error in _send_allocation_notification: {str(e)}")
            # Don't raise the exception to avoid breaking the allocation process


class FoodService:
    """Service class for food-related business logic"""

    def get_food_by_id(self, food_id: str) -> Optional['Food']:
        """Get food by ID"""
        try:
            from .models import Food
            return Food.query.filter_by(id=food_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_food_by_id: {str(e)}")
            return None

    def get_camp_foods(self, camp_id: str, category: str = None, date: datetime = None) -> List['Food']:
        """Get all foods for a camp, optionally filtered by category and date"""
        try:
            from .models import Food
            query = Food.query.filter_by(camp_id=camp_id)
            
            if category:
                query = query.filter_by(category=category.lower())
            
            if date:
                # Filter by date (ignoring time)
                query = query.filter(db.func.date(Food.date) == date.date())
            
            return query.order_by(Food.date.desc(), Food.category).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_foods: {str(e)}")
            return []

    def create_food(self, food_data: Dict[str, Any]) -> Optional['Food']:
        """Create a new food entry"""
        try:
            from .models import Food
            
            # Validate required fields
            required_fields = ["name", "quantity", "vendor", "date", "category", "camp_id"]
            for field in required_fields:
                if field not in food_data or food_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate category
            valid_categories = ["lunch", "supper", "snacks", "breakfast"]
            if food_data["category"].lower() not in valid_categories:
                raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

            # Validate quantity
            if int(food_data["quantity"]) < 1:
                raise ValueError("Quantity must be at least 1")

            # Convert date string to datetime if needed
            if isinstance(food_data["date"], str):
                food_data["date"] = datetime.fromisoformat(food_data["date"])

            new_food = Food(
                name=food_data["name"].strip(),
                quantity=int(food_data["quantity"]),
                vendor=food_data["vendor"].strip(),
                date=food_data["date"],
                category=food_data["category"].lower(),
                camp_id=food_data["camp_id"]
            )

            db.session.add(new_food)
            db.session.commit()

            current_app.logger.info(f"New food created: {new_food.name} ({new_food.quantity}) for camp {food_data['camp_id']}")
            return new_food

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_food: {str(e)}")
            raise Exception("Failed to create food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_food: {str(e)}")
            raise Exception("Failed to create food")

    def update_food(self, food_id: str, update_data: Dict[str, Any]) -> Optional['Food']:
        """Update food information"""
        try:
            food = self.get_food_by_id(food_id)
            if not food:
                return None

            # Validate category if being updated
            if "category" in update_data:
                valid_categories = ["lunch", "supper", "snacks", "breakfast"]
                if update_data["category"].lower() not in valid_categories:
                    raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

            # Validate quantity if being updated
            if "quantity" in update_data and update_data["quantity"] is not None:
                if int(update_data["quantity"]) < 0:
                    raise ValueError("Quantity must be non-negative")

            # Update fields
            updatable_fields = ["name", "quantity", "vendor", "date", "category"]
            for field in updatable_fields:
                if field in update_data:
                    if field == "quantity" and update_data[field] is not None:
                        setattr(food, field, int(update_data[field]))
                    elif field == "category" and update_data[field] is not None:
                        setattr(food, field, update_data[field].lower())
                    elif field == "date" and update_data[field] is not None:
                        date_val = update_data[field]
                        if isinstance(date_val, str):
                            date_val = datetime.fromisoformat(date_val)
                        setattr(food, field, date_val)
                    elif field in ["name", "vendor"] and update_data[field] is not None:
                        setattr(food, field, update_data[field].strip())

            db.session.commit()

            current_app.logger.info(f"Food updated: {food.name}")
            return food

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_food: {str(e)}")
            raise Exception("Failed to update food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_food: {str(e)}")
            raise Exception("Failed to update food")

    def delete_food(self, food_id: str) -> bool:
        """Delete a food entry"""
        try:
            food = self.get_food_by_id(food_id)
            if not food:
                return False

            # Check if food has allocations
            from .models import FoodAllocation
            allocations = FoodAllocation.query.filter_by(food_id=food_id).count()
            if allocations > 0:
                allocations = FoodAllocation.query.filter_by(food_id=food_id).all()
                for allocation in allocations:
                    db.session.delete(allocation)
                # db.session.commit()
                # raise ValueError("Cannot delete food with existing allocations")

            db.session.delete(food)
            db.session.commit()

            current_app.logger.info(f"Food deleted: {food.name}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_food: {str(e)}")
            raise Exception("Failed to delete food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_food: {str(e)}")
            raise Exception("Failed to delete food")

    def get_food_with_allocation_stats(self, camp_id: str) -> List[Dict[str, Any]]:
        """Get foods with allocation statistics"""
        try:
            from .models import Food, FoodAllocation
            
            foods = self.get_camp_foods(camp_id)
            food_stats = []
            
            for food in foods:
                allocated_count = FoodAllocation.query.filter_by(food_id=food.id).count()
                available_quantity = food.quantity - allocated_count
                
                food_dict = food.to_dict()
                food_dict['allocated_quantity'] = allocated_count
                food_dict['available_quantity'] = available_quantity
                food_stats.append(food_dict)
            
            return food_stats
        except Exception as e:
            current_app.logger.error(f"Error in get_food_with_allocation_stats: {str(e)}")
            return []


class FoodAllocationService:
    """Service class for food allocation-related business logic with race condition protection"""

    def get_allocation_by_id(self, allocation_id: str) -> Optional['FoodAllocation']:
        """Get food allocation by ID"""
        try:
            from .models import FoodAllocation
            return FoodAllocation.query.filter_by(id=allocation_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_allocation_by_id: {str(e)}")
            return None

    def get_camp_allocations(self, camp_id: str, food_category: str = None) -> List['FoodAllocation']:
        """Get all food allocations for a camp"""
        try:
            from .models import FoodAllocation, Food
            
            query = FoodAllocation.query.filter_by(camp_id=camp_id)
            
            if food_category:
                query = query.join(Food).filter(Food.category == food_category.lower())
            
            return query.order_by(FoodAllocation.allocation_date.desc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_camp_allocations: {str(e)}")
            return []

    def get_registration_allocations(self, registration_id: str, camp_id: str) -> List['FoodAllocation']:
        """Get all food allocations for a registration"""
        try:
            from .models import FoodAllocation
            return FoodAllocation.query.filter_by(
                registration_id=registration_id,
                camp_id=camp_id
            ).order_by(FoodAllocation.allocation_date.desc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_registration_allocations: {str(e)}")
            return []

    def allocate_food(self, allocation_data: Dict[str, Any], allocated_by: str) -> Optional['FoodAllocation']:
        """Allocate food to a registration with race condition protection and daily category validation"""
        try:
            from .models import Food, FoodAllocation
            
            # Validate required fields
            required_fields = ["food_id", "registration_id", "camp_id"]
            for field in required_fields:
                if field not in allocation_data or not allocation_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Use SELECT FOR UPDATE to prevent race conditions
            food = Food.query.filter_by(
                id=allocation_data["food_id"],
                camp_id=allocation_data["camp_id"]
            ).with_for_update().first()
            
            if not food:
                raise ValueError("Food not found or does not belong to this camp")

            # Get registration and validate
            registration = Registration.query.filter_by(
                id=allocation_data["registration_id"],
                camp_id=allocation_data["camp_id"]
            ).first()
            
            if not registration:
                raise ValueError("Registration not found or does not belong to this camp")

            # Check if registration already has allocation for this food
            existing_allocation = FoodAllocation.query.filter_by(
                food_id=allocation_data["food_id"],
                registration_id=allocation_data["registration_id"]
            ).first()
            
            if existing_allocation:
                raise ValueError(f"Registration already has allocation for this food item")

            # Check if registration has already taken this food category today
            today = datetime.now(timezone.utc).date()
            existing_category_allocation = db.session.query(FoodAllocation).join(Food).filter(
                FoodAllocation.registration_id == allocation_data["registration_id"],
                FoodAllocation.camp_id == allocation_data["camp_id"],
                Food.category == food.category,
                db.func.date(FoodAllocation.allocation_date) == today
            ).first()
            
            if existing_category_allocation:
                raise ValueError(f"Registration has already received {food.category} today. You can only have {food.category} once per day.")

            # Check available quantity
            allocated_count = FoodAllocation.query.filter_by(food_id=food.id).count()
            available_quantity = food.quantity - allocated_count

            food.quantity = food.quantity - 1
            
            if available_quantity <= 0:
                raise ValueError(f"No more {food.name} available for allocation")

            # Create allocation
            new_allocation = FoodAllocation(
                food_id=allocation_data["food_id"],
                registration_id=allocation_data["registration_id"],
                camp_id=allocation_data["camp_id"],
                allocated_by=allocated_by
            )

            db.session.add(new_allocation)
            db.session.commit()

            current_app.logger.info(f"Food allocated: {food.name} to {registration.surname} {registration.last_name}")
            return new_allocation

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in allocate_food: {str(e)}")
            raise Exception("Failed to allocate food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in allocate_food: {str(e)}")
            raise Exception("Failed to allocate food")

    def bulk_allocate_food(self, allocation_data: Dict[str, Any], allocated_by: str) -> List['FoodAllocation']:
        """Bulk allocate food to multiple registrations with race condition protection and daily category validation"""
        try:
            from .models import Food, FoodAllocation
            
            # Validate required fields
            required_fields = ["food_id", "registration_ids", "camp_id"]
            for field in required_fields:
                if field not in allocation_data or not allocation_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Validate registration_ids is a list
            if not isinstance(allocation_data["registration_ids"], list) or len(allocation_data["registration_ids"]) == 0:
                raise ValueError("At least one registration ID must be provided")

            # Use SELECT FOR UPDATE to prevent race conditions
            food = Food.query.filter_by(
                id=allocation_data["food_id"],
                camp_id=allocation_data["camp_id"]
            ).with_for_update().first()
            
            if not food:
                raise ValueError("Food not found or does not belong to this camp")

            # Get today's date for category validation
            today = datetime.now(timezone.utc).date()

            # Get registrations and validate
            registrations = []
            for reg_id in allocation_data["registration_ids"]:
                registration = Registration.query.filter_by(
                    id=reg_id,
                    camp_id=allocation_data["camp_id"]
                ).first()
                
                if not registration:
                    raise ValueError(f"Registration {reg_id} not found or does not belong to this camp")

                # Check if registration already has allocation for this food
                existing_allocation = FoodAllocation.query.filter_by(
                    food_id=allocation_data["food_id"],
                    registration_id=reg_id
                ).first()
                
                if existing_allocation:
                    raise ValueError(f"Registration {reg_id} ({registration.surname} {registration.last_name}) already has allocation for this food item")
                
                # Check if registration has already taken this food category today
                existing_category_allocation = db.session.query(FoodAllocation).join(Food).filter(
                    FoodAllocation.registration_id == reg_id,
                    FoodAllocation.camp_id == allocation_data["camp_id"],
                    Food.category == food.category,
                    db.func.date(FoodAllocation.allocation_date) == today
                ).first()
                
                if existing_category_allocation:
                    raise ValueError(f"Registration {reg_id} ({registration.surname} {registration.last_name}) has already received {food.category} today. You can only have {food.category} once per day.")
                
                registrations.append(registration)

            # Check available quantity
            allocated_count = FoodAllocation.query.filter_by(food_id=food.id).count()
            available_quantity = food.quantity - allocated_count
            
            if len(registrations) > available_quantity:
                raise ValueError(f"Not enough {food.name} available. Available: {available_quantity}, Requested: {len(registrations)}")

            # Create allocations
            allocations = []
            for registration in registrations:
                allocation = FoodAllocation(
                    food_id=allocation_data["food_id"],
                    registration_id=registration.id,
                    camp_id=allocation_data["camp_id"],
                    allocated_by=allocated_by
                )
                
                db.session.add(allocation)
                allocations.append(allocation)

            db.session.commit()

            current_app.logger.info(f"Bulk food allocation: {food.name} allocated to {len(allocations)} registrations")
            return allocations

        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in bulk_allocate_food: {str(e)}")
            raise Exception("Failed to bulk allocate food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in bulk_allocate_food: {str(e)}")
            raise Exception("Failed to bulk allocate food")

    def allocate_food_by_category(self, allocation_data: Dict[str, Any], allocated_by: str) -> List['FoodAllocation']:
        """Allocate food to all registrations in a specific category"""
        try:
            # Validate required fields
            required_fields = ["food_id", "category_id", "camp_id"]
            for field in required_fields:
                if field not in allocation_data or not allocation_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Get all registrations in the category
            registrations = Registration.query.filter_by(
                category_id=allocation_data["category_id"],
                camp_id=allocation_data["camp_id"]
            ).all()

            if not registrations:
                raise ValueError("No registrations found for this category")

            # Use bulk allocation
            bulk_data = {
                "food_id": allocation_data["food_id"],
                "registration_ids": [reg.id for reg in registrations],
                "camp_id": allocation_data["camp_id"]
            }

            return self.bulk_allocate_food(bulk_data, allocated_by)

        except ValueError:
            raise
        except Exception as e:
            current_app.logger.error(f"Error in allocate_food_by_category: {str(e)}")
            raise Exception("Failed to allocate food by category")

    def deallocate_food(self, allocation_id: str) -> bool:
        """Remove a food allocation"""
        try:
            allocation = self.get_allocation_by_id(allocation_id)
            if not allocation:
                return False

            db.session.delete(allocation)
            db.session.commit()

            current_app.logger.info(f"Food allocation removed: {allocation.id}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in deallocate_food: {str(e)}")
            raise Exception("Failed to deallocate food due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in deallocate_food: {str(e)}")
            raise Exception("Failed to deallocate food")

    def get_daily_allocation_summary(self, camp_id: str, date: datetime) -> Dict[str, Any]:
        """Get daily food allocation summary"""
        try:
            from .models import Food, FoodAllocation
            
            # Get foods for the specific date
            foods = Food.query.filter_by(camp_id=camp_id).filter(
                db.func.date(Food.date) == date.date()
            ).all()

            summary = {
                "date": date.date(),
                "categories": {},
                "total_allocated": 0,
                "total_available": 0
            }

            for food in foods:
                category = food.category
                if category not in summary["categories"]:
                    summary["categories"][category] = {
                        "foods": [],
                        "total_allocated": 0,
                        "total_available": 0
                    }

                allocated_count = FoodAllocation.query.filter_by(food_id=food.id).count()
                available_quantity = food.quantity - allocated_count

                food_info = {
                    "id": food.id,
                    "name": food.name,
                    "vendor": food.vendor,
                    "total_quantity": food.quantity,
                    "allocated_quantity": allocated_count,
                    "available_quantity": available_quantity
                }

                summary["categories"][category]["foods"].append(food_info)
                summary["categories"][category]["total_allocated"] += allocated_count
                summary["categories"][category]["total_available"] += available_quantity
                summary["total_allocated"] += allocated_count
                summary["total_available"] += available_quantity

            return summary

        except Exception as e:
            current_app.logger.error(f"Error in get_daily_allocation_summary: {str(e)}")
            return {"error": str(e)}
