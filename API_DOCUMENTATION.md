# CampManager API Documentation

## Overview

The CampManager API is a comprehensive camp management system designed for church camps. It provides endpoints for user authentication, camp management, registration handling, and administrative functions.

**Base URL:** `http://localhost:5000` (Development) | `https://api.campmanager.com` (Production)

**API Version:** 1.0.0

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Token Expiry
- **Access Token:** 24 hours (1 hour in development)
- **Refresh Token:** 30 days

## Response Format

All API responses follow a consistent format:

```json
{
  "data": {
    // Response data here
  }
}
```

### Error Response Format

```json
{
  "data": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details (optional)
    }
  }
}
```

## Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `500` - Internal Server Error

---

# Authentication Endpoints

## POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "data": {
    "email": "manager@example.com",
    "password": "password123",
    "full_name": "John Manager",
    "role": "camp_manager"
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "email": "manager@example.com",
    "full_name": "John Manager",
    "role": "camp_manager",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Validation Rules:**
- `email`: Valid email format, required
- `password`: Minimum 8 characters, required
- `full_name`: Minimum 2 characters, required
- `role`: Either "camp_manager" or "volunteer", optional (defaults to "camp_manager")

## POST /auth/login

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "data": {
    "email": "manager@example.com",
    "password": "password123"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "uuid",
      "email": "manager@example.com",
      "full_name": "John Manager",
      "role": "camp_manager"
    },
    "expires_in": 86400
  }
}
```

## POST /auth/refresh

Refresh access token using refresh token.

**Headers:** `Authorization: Bearer <refresh_token>`

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 86400
  }
}
```

## POST /auth/logout

Logout user (client should discard tokens).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Successfully logged out"
  }
}
```

## GET /auth/me

Get current user details.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "manager@example.com",
    "full_name": "John Manager",
    "role": "camp_manager",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /auth/me

Update current user details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "full_name": "John Updated Manager",
    "email": "updated@example.com"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "updated@example.com",
    "full_name": "John Updated Manager",
    "role": "camp_manager",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## PUT /auth/me/password

Change user password.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "current_password": "oldpassword123",
    "new_password": "newpassword123"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "message": "Password changed successfully"
  }
}
```

---

# Camp Management Endpoints

## GET /camps

Get all camps for the authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Summer Camp 2024",
      "start_date": "2024-07-01",
      "end_date": "2024-07-07",
      "location": "Camp Grounds, Accra",
      "base_fee": "250.00",
      "capacity": 100,
      "description": "Annual summer camp for youth",
      "registration_deadline": "2024-06-15T23:59:59Z",
      "is_active": true,
      "camp_manager_id": "uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## POST /camps

Create a new camp.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Summer Camp 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-07",
    "location": "Camp Grounds, Accra",
    "base_fee": "250.00",
    "capacity": 100,
    "description": "Annual summer camp for youth",
    "registration_deadline": "2024-06-15T23:59:59Z"
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Summer Camp 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-07",
    "location": "Camp Grounds, Accra",
    "base_fee": "250.00",
    "capacity": 100,
    "description": "Annual summer camp for youth",
    "registration_deadline": "2024-06-15T23:59:59Z",
    "is_active": true,
    "camp_manager_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## GET /camps/{camp_id}

Get details of a specific camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Summer Camp 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-07",
    "location": "Camp Grounds, Accra",
    "base_fee": "250.00",
    "capacity": 100,
    "description": "Annual summer camp for youth",
    "registration_deadline": "2024-06-15T23:59:59Z",
    "is_active": true,
    "camp_manager_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /camps/{camp_id}

Update camp details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Updated Summer Camp 2024",
    "capacity": 120,
    "description": "Updated description"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Updated Summer Camp 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-07",
    "location": "Camp Grounds, Accra",
    "base_fee": "250.00",
    "capacity": 120,
    "description": "Updated description",
    "registration_deadline": "2024-06-15T23:59:59Z",
    "is_active": true,
    "camp_manager_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/{camp_id}

Delete a camp and all related data.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Camp deleted successfully"
  }
}
```

## GET /camps/{camp_id}/stats

Get camp statistics including registrations and financial data.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "total_registrations": 45,
    "total_revenue": "11250.00",
    "paid_registrations": 40,
    "unpaid_registrations": 5,
    "checked_in_count": 35,
    "capacity_utilization": 45,
    "registration_by_category": {
      "Regular": 25,
      "Early Bird": 15,
      "Campus Leader": 5
    },
    "registration_by_church": {
      "Central Baptist Church": 20,
      "Grace Methodist Church": 15,
      "Unity Presbyterian Church": 10
    }
  }
}
```

---

# Church Management Endpoints

## GET /camps/{camp_id}/churches

Get all churches for a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Central Baptist Church",
      "camp_id": "uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## POST /camps/{camp_id}/churches

Add a new church to a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "New Baptist Church"
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "name": "New Baptist Church",
    "camp_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /camps/churches/{church_id}

Update church details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Updated Church Name"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Updated Church Name",
    "camp_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/churches/{church_id}

Remove a church from a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Church removed successfully"
  }
}
```

---

# Category Management Endpoints

## GET /camps/{camp_id}/categories

Get all registration categories for a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Regular",
      "discount_percentage": "0.00",
      "discount_amount": "0.00",
      "camp_id": "uuid",
      "is_default": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "Early Bird",
      "discount_percentage": "15.00",
      "discount_amount": "0.00",
      "camp_id": "uuid",
      "is_default": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## POST /camps/{camp_id}/categories

Create a new registration category.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Student Discount",
    "discount_percentage": "20.00",
    "is_default": false
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Student Discount",
    "discount_percentage": "20.00",
    "discount_amount": "0.00",
    "camp_id": "uuid",
    "is_default": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /camps/categories/{category_id}

Update category details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Updated Category Name",
    "discount_percentage": "25.00"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Updated Category Name",
    "discount_percentage": "25.00",
    "discount_amount": "0.00",
    "camp_id": "uuid",
    "is_default": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/categories/{category_id}

Delete a category.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Category deleted successfully"
  }
}
```

---

# Custom Fields Management Endpoints

## GET /camps/{camp_id}/custom-fields

Get all custom fields for a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "field_name": "T-Shirt Size",
      "field_type": "dropdown",
      "is_required": true,
      "options": ["S", "M", "L", "XL", "XXL"],
      "camp_id": "uuid",
      "order": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "field_name": "Dietary Restrictions",
      "field_type": "text",
      "is_required": false,
      "options": null,
      "camp_id": "uuid",
      "order": 2,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## POST /camps/{camp_id}/custom-fields

Create a new custom field.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "field_name": "Medical Conditions",
    "field_type": "text",
    "is_required": false,
    "order": 3
  }
}
```

**Field Types:**
- `text` - Single line text input
- `number` - Numeric input
- `dropdown` - Select from predefined options
- `checkbox` - Multiple selection checkboxes
- `date` - Date picker

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "field_name": "Medical Conditions",
    "field_type": "text",
    "is_required": false,
    "options": null,
    "camp_id": "uuid",
    "order": 3,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /camps/custom-fields/{field_id}

Update custom field details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "field_name": "Updated Field Name",
    "is_required": true,
    "options": ["Option 1", "Option 2", "Option 3"]
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "field_name": "Updated Field Name",
    "field_type": "dropdown",
    "is_required": true,
    "options": ["Option 1", "Option 2", "Option 3"],
    "camp_id": "uuid",
    "order": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/custom-fields/{field_id}

Delete a custom field.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Custom field deleted successfully"
  }
}
```

---

# Registration Links Management Endpoints

## GET /camps/{camp_id}/registration-links

Get all registration links for a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "camp_id": "uuid",
      "link_token": "ear_abc123def456",
      "name": "Early Bird Registration",
      "allowed_categories": ["uuid1", "uuid2"],
      "is_active": true,
      "expires_at": "2024-06-01T23:59:59Z",
      "usage_limit": 50,
      "usage_count": 25,
      "created_by": "uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## POST /camps/{camp_id}/registration-links

Create a new registration link.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Student Registration Link",
    "allowed_categories": ["uuid1", "uuid2"],
    "expires_at": "2024-06-15T23:59:59Z",
    "usage_limit": 30
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "camp_id": "uuid",
    "link_token": "stu_xyz789abc123",
    "name": "Student Registration Link",
    "allowed_categories": ["uuid1", "uuid2"],
    "is_active": true,
    "expires_at": "2024-06-15T23:59:59Z",
    "usage_limit": 30,
    "usage_count": 0,
    "created_by": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## GET /camps/registration-links/{link_id}

Get details of a specific registration link.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "camp_id": "uuid",
    "link_token": "ear_abc123def456",
    "name": "Early Bird Registration",
    "allowed_categories": ["uuid1", "uuid2"],
    "is_active": true,
    "expires_at": "2024-06-01T23:59:59Z",
    "usage_limit": 50,
    "usage_count": 25,
    "created_by": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## PUT /camps/registration-links/{link_id}

Update registration link details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "name": "Updated Link Name",
    "usage_limit": 75,
    "expires_at": "2024-07-01T23:59:59Z"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "camp_id": "uuid",
    "link_token": "ear_abc123def456",
    "name": "Updated Link Name",
    "allowed_categories": ["uuid1", "uuid2"],
    "is_active": true,
    "expires_at": "2024-07-01T23:59:59Z",
    "usage_limit": 75,
    "usage_count": 25,
    "created_by": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## PATCH /camps/registration-links/{link_id}/toggle

Toggle registration link active status.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "camp_id": "uuid",
    "link_token": "ear_abc123def456",
    "name": "Early Bird Registration",
    "allowed_categories": ["uuid1", "uuid2"],
    "is_active": false,
    "expires_at": "2024-06-01T23:59:59Z",
    "usage_limit": 50,
    "usage_count": 25,
    "created_by": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/registration-links/{link_id}

Delete a registration link.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Registration link deleted successfully"
  }
}
```

---

# Registration Management Endpoints

## GET /camps/{camp_id}/registrations

Get all registrations for a camp.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "surname": "John",
      "middle_name": "Michael",
      "last_name": "Doe",
      "age": 25,
      "email": "john.doe@example.com",
      "phone_number": "+233123456789",
      "emergency_contact_name": "Jane Doe",
      "emergency_contact_phone": "+233987654321",
      "church_id": "uuid",
      "category_id": "uuid",
      "custom_field_responses": {
        "t_shirt_size": "L",
        "dietary_restrictions": "Vegetarian"
      },
    "total_amount": "212.50",
    "has_paid": true,
    "has_checked_in": true,
    "camp_id": "uuid",
    "registration_link_id": "uuid",
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## DELETE /camps/registrations/{registration_id}

Cancel/delete a registration.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "message": "Registration cancelled successfully"
  }
}
```

---

# Public Registration Endpoints

## GET /camps/{camp_id}/register

Get general registration form (all categories available).

**Response (200):**
```json
{
  "data": {
    "camp": {
      "id": "uuid",
      "name": "Summer Camp 2024",
      "start_date": "2024-07-01",
      "end_date": "2024-07-07",
      "location": "Camp Grounds, Accra",
      "base_fee": "250.00",
      "description": "Annual summer camp for youth",
      "registration_deadline": "2024-06-15T23:59:59Z"
    },
    "churches": [
      {
        "id": "uuid",
        "name": "Central Baptist Church"
      }
    ],
    "categories": [
      {
        "id": "uuid",
        "name": "Regular",
        "discount_percentage": "0.00",
        "discount_amount": "0.00",
        "calculated_fee": "250.00"
      },
      {
        "id": "uuid",
        "name": "Early Bird",
        "discount_percentage": "15.00",
        "discount_amount": "0.00",
        "calculated_fee": "212.50"
      }
    ],
    "custom_fields": [
      {
        "id": "uuid",
        "field_name": "T-Shirt Size",
        "field_type": "dropdown",
        "is_required": true,
        "options": ["S", "M", "L", "XL", "XXL"],
        "order": 1
      }
    ]
  }
}
```

## POST /camps/{camp_id}/register

Submit general registration.

**Request Body:**
```json
{
  "data": {
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    }
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    },
    "total_amount": "212.50",
    "has_paid": false,
    "has_checked_in": false,
    "camp_id": "uuid",
    "registration_link_id": null,
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

## GET /register/{link_token}

Get category-specific registration form via registration link.

**Response (200):**
```json
{
  "data": {
    "camp": {
      "id": "uuid",
      "name": "Summer Camp 2024",
      "start_date": "2024-07-01",
      "end_date": "2024-07-07",
      "location": "Camp Grounds, Accra",
      "base_fee": "250.00",
      "description": "Annual summer camp for youth",
      "registration_deadline": "2024-06-15T23:59:59Z"
    },
    "churches": [
      {
        "id": "uuid",
        "name": "Central Baptist Church"
      }
    ],
    "categories": [
      {
        "id": "uuid",
        "name": "Early Bird",
        "discount_percentage": "15.00",
        "discount_amount": "0.00",
        "calculated_fee": "212.50"
      }
    ],
    "custom_fields": [
      {
        "id": "uuid",
        "field_name": "T-Shirt Size",
        "field_type": "dropdown",
        "is_required": true,
        "options": ["S", "M", "L", "XL", "XXL"],
        "order": 1
      }
    ],
    "link_info": {
      "name": "Early Bird Registration",
      "expires_at": "2024-06-01T23:59:59Z",
      "usage_count": 25,
      "usage_limit": 50
    }
  }
}
```

## POST /register/{link_token}

Submit registration via category-specific link.

**Request Body:**
```json
{
  "data": {
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    }
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    },
    "total_amount": "212.50",
    "has_paid": false,
    "has_checked_in": false,
    "camp_id": "uuid",
    "registration_link_id": "uuid",
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

## GET /register/check/{link_token}

Check registration link status and availability.

**Response (200):**
```json
{
  "data": {
    "is_valid": true,
    "camp_name": "Summer Camp 2024",
    "link_name": "Early Bird Registration",
    "expires_at": "2024-06-01T23:59:59Z",
    "usage_count": 25,
    "usage_limit": 50,
    "registration_deadline": "2024-06-15T23:59:59Z",
    "camp_capacity": 100,
    "current_registrations": 45
  }
}
```

---

# Utility Endpoints

## GET /health

Health check endpoint.

**Response (200):**
```json
{
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0"
  }
}
```

## GET /

API information endpoint.

**Response (200):**
```json
{
  "data": {
    "name": "CampManager API",
    "version": "1.0.0",
    "description": "A comprehensive camp management system API for church camps",
    "documentation": "/docs",
    "openapi_spec": "/openapi.json",
    "endpoints": {
      "authentication": "/auth",
      "camps": "/camps",
      "public_registration": "/register",
      "health": "/health"
    }
  }
}
```

---

# Data Models

## User Model
```json
{
  "id": "string (UUID)",
  "email": "string (email format)",
  "full_name": "string",
  "role": "string (camp_manager|volunteer)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Camp Model
```json
{
  "id": "string (UUID)",
  "name": "string",
  "start_date": "string (YYYY-MM-DD)",
  "end_date": "string (YYYY-MM-DD)",
  "location": "string",
  "base_fee": "string (decimal)",
  "capacity": "integer",
  "description": "string",
  "registration_deadline": "string (ISO 8601 datetime)",
  "is_active": "boolean",
  "camp_manager_id": "string (UUID)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Church Model
```json
{
  "id": "string (UUID)",
  "name": "string",
  "camp_id": "string (UUID)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Category Model
```json
{
  "id": "string (UUID)",
  "name": "string",
  "discount_percentage": "string (decimal)",
  "discount_amount": "string (decimal)",
  "camp_id": "string (UUID)",
  "is_default": "boolean",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Custom Field Model
```json
{
  "id": "string (UUID)",
  "field_name": "string",
  "field_type": "string (text|number|dropdown|checkbox|date)",
  "is_required": "boolean",
  "options": "array of strings (nullable)",
  "camp_id": "string (UUID)",
  "order": "integer",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Registration Link Model
```json
{
  "id": "string (UUID)",
  "camp_id": "string (UUID)",
  "link_token": "string",
  "name": "string",
  "allowed_categories": "array of UUIDs",
  "is_active": "boolean",
  "expires_at": "string (ISO 8601 datetime, nullable)",
  "usage_limit": "integer (nullable)",
  "usage_count": "integer",
  "created_by": "string (UUID)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

## Registration Model
```json
{
  "id": "string (UUID)",
  "surname": "string",
  "middle_name": "string",
  "last_name": "string",
  "age": "integer",
  "email": "string (email format, nullable)",
  "phone_number": "string",
  "emergency_contact_name": "string",
  "emergency_contact_phone": "string",
  "church_id": "string (UUID)",
  "category_id": "string (UUID)",
  "custom_field_responses": "object (key-value pairs)",
  "total_amount": "string (decimal)",
  "has_paid": "boolean",
  "has_checked_in": "boolean",
  "camp_id": "string (UUID)",
  "registration_link_id": "string (UUID, nullable)",
  "registration_date": "string (ISO 8601 datetime)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

---

# Error Codes

## Authentication Errors
- `USER_EXISTS` - User with email already exists
- `INVALID_CREDENTIALS` - Invalid email or password
- `USER_NOT_FOUND` - User not found
- `INVALID_PASSWORD` - Current password is incorrect
- `EMAIL_EXISTS` - Email already exists for another user

## Authorization Errors
- `AUTHORIZATION_ERROR` - Access denied
- `TOKEN_EXPIRED` - JWT token has expired
- `INVALID_TOKEN` - Invalid JWT token

## Validation Errors
- `VALIDATION_ERROR` - Request validation failed
- `BAD_REQUEST` - Malformed request

## Resource Errors
- `CAMP_NOT_FOUND` - Camp not found
- `CHURCH_NOT_FOUND` - Church not found
- `CATEGORY_NOT_FOUND` - Category not found
- `CUSTOM_FIELD_NOT_FOUND` - Custom field not found
- `REGISTRATION_NOT_FOUND` - Registration not found
- `LINK_NOT_FOUND` - Registration link not found

## Registration Link Errors
- `INVALID_LINK` - Invalid registration link
- `LINK_EXPIRED` - Registration link has expired or reached usage limit
- `INVALID_CATEGORY` - Selected category not allowed for this link

## General Errors
- `INTERNAL_ERROR` - Internal server error
- `REGISTRATION_UNAVAILABLE` - Registration not available

---

# Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit:** 1000 requests per hour
- **Burst Limit:** 100 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit` - Request limit per window
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Time when the rate limit resets

---

# CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS):

- **Development:** All origins allowed (`*`)
- **Production:** Specific origins configured via environment variables
- **Allowed Methods:** GET, POST, PUT, PATCH, DELETE, OPTIONS
- **Allowed Headers:** Authorization, Content-Type, Accept

---

# OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI Spec:** `/openapi.json`

---

# Frontend Development Notes

## Authentication Flow
1. Register user with `/auth/register`
2. Login with `/auth/login` to get tokens
3. Store access token and refresh token securely
4. Include access token in Authorization header for protected endpoints
5. Use refresh token to get new access token when needed
6. Handle token expiry and refresh automatically

## Registration Flow
1. **General Registration:**
   - Get form structure with `GET /camps/{camp_id}/register`
   - Submit registration with `POST /camps/{camp_id}/register`

2. **Link-based Registration:**
   - Check link validity with `GET /register/check/{link_token}`
   - Get form structure with `GET /register/{link_token}`
   - Submit registration with `POST /register/{link_token}`

## Camp Management Flow
1. Create camp with `POST /camps`
2. Add churches with `POST /camps/{camp_id}/churches`
3. Create categories with `POST /camps/{camp_id}/categories`
4. Add custom fields with `POST /camps/{camp_id}/custom-fields`
5. Create registration links with `POST /camps/{camp_id}/registration-links`
6. Monitor registrations with `GET /camps/{camp_id}/registrations`
7. View statistics with `GET /camps/{camp_id}/stats`

## Error Handling
- Always check response status codes
- Parse error responses for specific error codes and messages
- Implement retry logic for network errors
- Handle validation errors by showing field-specific messages

## Data Validation
- Validate email formats on frontend
- Enforce minimum password length (8 characters)
- Validate phone number formats
- Check required fields before submission
- Validate date ranges (start_date < end_date)
- Ensure registration deadline is before camp start date

This comprehensive API documentation provides all the information needed to build a frontend application for the CampManager system.
      "has_paid": true,
      "has_checked_in": false,
      "camp_id": "uuid",
      "registration_link_id": "uuid",
      "registration_date": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

## GET /camps/registrations/{registration_id}

Get details of a specific registration.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    },
    "total_amount": "212.50",
    "has_paid": true,
    "has_checked_in": false,
    "camp_id": "uuid",
    "registration_link_id": "uuid",
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

## PUT /camps/registrations/{registration_id}

Update registration details.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "email": "updated.email@example.com",
    "phone_number": "+233111222333",
    "custom_field_responses": {
      "t_shirt_size": "XL",
      "dietary_restrictions": "No restrictions"
    }
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "updated.email@example.com",
    "phone_number": "+233111222333",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "XL",
      "dietary_restrictions": "No restrictions"
    },
    "total_amount": "212.50",
    "has_paid": true,
    "has_checked_in": false,
    "camp_id": "uuid",
    "registration_link_id": "uuid",
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## PATCH /camps/registrations/{registration_id}/payment

Update payment status.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "has_paid": true,
    "payment_method": "Mobile Money",
    "transaction_id": "MM123456789"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    },
    "total_amount": "212.50",
    "has_paid": true,
    "has_checked_in": false,
    "camp_id": "uuid",
    "registration_link_id": "uuid",
    "registration_date": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## PATCH /camps/registrations/{registration_id}/checkin

Update check-in status.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "data": {
    "has_checked_in": true
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "surname": "John",
    "middle_name": "Michael",
    "last_name": "Doe",
    "age": 25,
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+233987654321",
    "church_id": "uuid",
    "category_id": "uuid",
    "custom_field_responses": {
      "t_shirt_size": "L",
      "dietary_restrictions": "Vegetarian"
    },
    "total_amount": "212.50",
