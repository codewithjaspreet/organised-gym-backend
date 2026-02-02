# Organised Gym

A comprehensive gym management system built with FastAPI, providing role-based access control for gym owners, members, trainers, and staff.

## Tech Stacks

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLModel
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Python Version**: 3.11+

## Project Structure

```
organised-gym/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py          # User management endpoints
│   │       ├── gyms.py           # Gym management endpoints
│   │       ├── plans.py          # Gym plan management endpoints
│   │       ├── memberships.py    # Membership management endpoints
│   │       ├── billing.py        # Payment management endpoints
│   │       └── og_plans.py       # OG plan management endpoints
│   ├── core/
│   │   ├── config.py             # Application configuration
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   ├── permissions.py        # Role-based access control
│   │   ├── security.py           # Password hashing and JWT
│   │   └── exceptions.py         # Custom exceptions
│   ├── db/
│   │   ├── db.py                 # Database session and engine
│   │   └── migrations/           # Database migrations
│   ├── models/
│   │   ├── user.py               # User model
│   │   ├── gym.py                # Gym model
│   │   ├── plan.py                # Gym plan model
│   │   ├── membership.py         # Membership model
│   │   ├── billing.py            # Payment model
│   │   ├── attendance.py         # Attendance model
│   │   ├── notification.py      # Notification model
│   │   ├── og_plan.py            # OG plan model
│   │   └── gym_subscription.py   # Gym subscription model
│   ├── schemas/
│   │   ├── auth.py               # Authentication schemas
│   │   ├── user.py               # User schemas
│   │   ├── gym.py                # Gym schemas
│   │   ├── plan.py               # Plan schemas
│   │   ├── membership.py         # Membership schemas
│   │   ├── billing.py            # Payment schemas
│   │   └── og_plan.py            # OG plan schemas
│   ├── services/
│   │   ├── auth_service.py       # Authentication business logic
│   │   ├── user_service.py       # User business logic
│   │   ├── gym_service.py        # Gym business logic
│   │   ├── plan_service.py       # Plan business logic
│   │   ├── membership_service.py # Membership business logic
│   │   ├── billing_service.py    # Payment business logic
│   │   └── og_plan_service.py    # OG plan business logic
│   └── utils/
│       ├── datetime.py           # Date/time utilities
│       ├── email.py              # Email utilities
│       └── sms.py                # SMS utilities
├── tests/                        # Test files
├── main.py                       # FastAPI application entry point
├── pyproject.toml                # Project dependencies
└── README.md                     # This file
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database
- uv package manager (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd organised-gym
```

2. Install dependencies:
```bash
uv sync
```

3. Create a `.env` file in the root directory:
```env
DB_CONNECTION_URL=postgresql://username:password@localhost:5432/dbname
APP_NAME=Organised Gym
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

4. Run the application:
```bash
fastapi dev main.py
```

The API will be available at `http://localhost:8000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_CONNECTION_URL` | PostgreSQL connection string | Yes |
| `APP_NAME` | Application name | Yes |
| `SECRET_KEY` | JWT secret key | Yes |
| `ALGORITHM` | JWT algorithm (default: HS256) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration (default: 30) | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration (default: 7) | No |

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. All endpoints except `/api/v1/auth/register` and `/api/v1/auth/login` require authentication.

### Register

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "user_name": "johndoe",
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "phone": "1234567890",
  "gender": "MALE",
  "address_line1": "123 Main St",
  "address_line2": "Apt 4B",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "dob": "1990-01-01",
  "role": "MEMBER"
}
```

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}
```

Response includes `access_token` and `refresh_token`. Include the access token in subsequent requests:

```bash
Authorization: Bearer <access_token>
```

## Role-Based Access Control

The system supports five user roles with different access levels:

### OG (Platform Owner)
- Full access to OG plans (create, read, update, delete)
- Can access any gym
- Platform-level administration

### ADMIN (Gym Owner)
- Full control over their gym
- Manage members, trainers, and staff profiles
- Create and manage gym plans
- Manage memberships
- Verify and manage payments
- Delete users within their gym

### MEMBER
- Access own profile
- View and create own memberships
- Create own payments
- View own payment history

### TRAINER
- Access own profile
- Limited access based on gym assignment

### STAFF
- Access own profile
- Verify payments for their gym
- Limited access based on gym assignment

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get tokens

### Users

- `GET /api/v1/users/{user_id}` - Get user (own profile or ADMIN)
- `PUT /api/v1/users/{user_id}` - Update user (own profile or ADMIN)
- `DELETE /api/v1/users/{user_id}` - Delete user (ADMIN only)

### Gyms

- `POST /api/v1/gyms` - Create gym (authenticated, must be for self unless OG)
- `GET /api/v1/gyms/{gym_id}` - Get gym (authenticated)
- `PUT /api/v1/gyms/{gym_id}` - Update gym (gym owner or OG)
- `DELETE /api/v1/gyms/{gym_id}` - Delete gym (gym owner or OG)

### Plans

- `POST /api/v1/plans` - Create plan (gym owner only)
- `GET /api/v1/plans/{plan_id}` - Get plan (authenticated)
- `PUT /api/v1/plans/{plan_id}` - Update plan (gym owner only)
- `DELETE /api/v1/plans/{plan_id}` - Delete plan (gym owner only)

### Memberships

- `POST /api/v1/memberships` - Create membership (gym owner or member for self)
- `GET /api/v1/memberships/{membership_id}` - Get membership (own or gym admin)
- `PUT /api/v1/memberships/{membership_id}` - Update membership (gym owner only)
- `DELETE /api/v1/memberships/{membership_id}` - Delete membership (gym owner only)

### Payments

- `POST /api/v1/payments` - Create payment (member for self)
- `GET /api/v1/payments/{payment_id}` - Get payment (own or gym admin/staff)
- `PUT /api/v1/payments/{payment_id}` - Update payment (gym admin/staff for verification)
- `DELETE /api/v1/payments/{payment_id}` - Delete payment (gym admin only)

### OG Plans

- `POST /api/v1/og-plans` - Create OG plan (OG role only)
- `GET /api/v1/og-plans/{og_plan_id}` - Get OG plan (OG role only)
- `PUT /api/v1/og-plans/{og_plan_id}` - Update OG plan (OG role only)
- `DELETE /api/v1/og-plans/{og_plan_id}` - Delete OG plan (OG role only)

## Database Models

### User
- User accounts with role-based access
- Supports OG, ADMIN, MEMBER, TRAINER, STAFF roles
- Linked to gyms, memberships, payments, attendance, and notifications

### Gym
- Gym information and settings
- Owned by ADMIN users
- Contains plans, memberships, and subscriptions

### Plan
- Gym-specific membership plans
- Linked to a specific gym

### Membership
- User memberships to gym plans
- Links users to plans within a gym

### Payment
- Payment records for memberships
- Can be verified by gym admin/staff
- Linked to user, membership, and gym

### OG Plan
- Platform-level plans offered by the system
- Managed by OG role users
- Can be subscribed to by gyms

### Gym Subscription
- Links gyms to OG plans
- Allows gyms to subscribe to platform plans

### Attendance
- Tracks user check-in and check-out at gyms
- Linked to user and gym

### Notification
- User notifications
- Linked to specific users

## Security Features

- Password hashing using bcrypt (72 character limit)
- JWT-based authentication
- Role-based access control
- Ownership verification for resources
- Active user status checking

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Database tables are automatically created on application startup. For production, use Alembic migrations located in `app/db/migrations/`.

## License

[Add your license here]

