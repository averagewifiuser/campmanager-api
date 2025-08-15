from typing import Optional, Dict, Any, List
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from decimal import Decimal

from .models import (
    Camp,
    CampWorker,
    Church,
    Category,
    CustomField,
    RegistrationLink,
    Registration,
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
            print(camp_ids)
            camps = Camp.query.filter(Camp.id.in_([camp.camp_id for camp in camp_ids])).order_by(Camp.created_at.desc()).all()
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
                user_id=camp_data['camp_manager_id'],
                camp_id=new_camp.id,
                role='camp_manager'
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

            # Calculate revenue
            total_revenue = sum(
                float(reg.total_amount) for reg in camp.registrations if reg.has_paid
            )

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
                name=church_data["name"].strip(), camp_id=church_data["camp_id"],
                area=church_data["area"].strip() if "area" in church_data else None,
                district=church_data["district"].strip() if "district" in church_data else None,
            ).first()

            if existing_church:
                return existing_church

            new_church = Church(
                name=church_data["name"].strip(), camp_id=church_data["camp_id"],
                area=church_data["area"].strip() if "area" in church_data else None,
                district=church_data["district"].strip() if "district" in church_data else None,
            )

            db.session.add(new_church)
            db.session.commit()

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

    def get_registration_by_id(self, registration_id: str) -> Optional[Registration]:
        """Get registration by ID"""
        try:
            return Registration.query.filter_by(id=registration_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_registration_by_id: {str(e)}"
            )
            return None

    def get_camp_registrations(self, camp_id: str) -> List[Registration]:
        """Get all registrations for a camp"""
        try:
            return (
                Registration.query.filter_by(camp_id=camp_id)
                .order_by(Registration.registration_date.desc())
                .all()
            )
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in get_camp_registrations: {str(e)}"
            )
            return []

    def get_registration_form(
        self, camp_id: str, link_token: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get registration form structure"""
        try:
            # Get camp
            camp = Camp.query.filter_by(id=camp_id, is_active=True).first()
            if not camp:
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

            return {
                "camp": camp.to_dict(),
                "churches": [church.to_dict() for church in churches],
                "categories": [category.to_dict() for category in categories],
                "custom_fields": [field.to_dict() for field in custom_fields],
                "link_type": link_type,
                "registration_link": (
                    registration_link.to_dict() if registration_link else None
                ),
            }

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
            campers: List[Registration] = Registration.query.filter_by(camp_id=camp.id).all()
            existing_codes = [camper.to_dict(for_api=True)['camper_code'] for camper in campers]

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
                camper_code=camper_code
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
        
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=3))
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
