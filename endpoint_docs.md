# Endpoint Documentation: GET /admin/users/

> Generated using Prompt 1: Comprehensive endpoint documentation

---

## Overview

| Property        | Value                          |
|----------------|-------------------------------|
| **Method**      | GET                            |
| **Path**        | `/admin/users/`                |
| **Description** | Retrieves a paginated list of all registered users. Restricted to admin users only. |
| **Auth Required** | Yes — Bearer JWT token       |
| **Role Required** | `admin`                      |

---

## Authentication

This endpoint uses **OAuth2 Bearer Token** authentication.

Every request must include a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

Tokens are obtained by calling the `/token` endpoint with valid credentials.
Tokens are signed with HS256 and expire after 15 minutes by default.

---

## Query Parameters

| Parameter | Type    | Required | Default | Description                          |
|-----------|---------|----------|---------|--------------------------------------|
| `skip`    | integer | No       | `0`     | Number of records to skip (for pagination) |
| `limit`   | integer | No       | `100`   | Maximum number of records to return  |

---

## Request Headers

| Header          | Required | Value                        |
|-----------------|----------|------------------------------|
| `Authorization` | Yes      | `Bearer <token>`             |
| `Content-Type`  | No       | `application/json`           |

---

## Response

### Success — HTTP 200 OK

Returns a JSON array of user objects.

```json
[
  {
    "id": 1,
    "username": "alice",
    "role": "admin",
    "status": "member",
    "months": 14
  },
  {
    "id": 2,
    "username": "bob",
    "role": "user",
    "status": "regular",
    "months": 3
  }
]
```

### Response Fields

| Field      | Type    | Description                              |
|------------|---------|------------------------------------------|
| `id`       | integer | Unique user identifier                   |
| `username` | string  | The user's login name                    |
| `role`     | string  | User role: `"user"` or `"admin"`         |
| `status`   | string  | Membership status: `"regular"`, `"member"`, `"vip"` |
| `months`   | integer | Number of months as a member             |

### Response Headers

| Header            | Description                                    |
|-------------------|------------------------------------------------|
| `X-Process-Time`  | Request processing time in milliseconds        |

---

## Error Responses

| HTTP Status | Error Code            | Cause                                              |
|-------------|----------------------|----------------------------------------------------|
| `401`       | `UNAUTHORIZED`        | Missing, expired, or invalid JWT token             |
| `403`       | `FORBIDDEN`           | Valid token but user does not have `admin` role    |
| `500`       | `INTERNAL_SERVER_ERROR` | Unexpected server or database error              |

### Example 401 Response
```json
{
  "detail": "Invalid authentication credentials"
}
```

### Example 403 Response
```json
{
  "detail": "Role 'admin' required."
}
```

---

## Execution Flow

When a request hits `GET /admin/users/`, the following happens in order:

1. **TimingMiddleware** records the request start time
2. **get_db()** opens an async database session
3. **oauth2_scheme** extracts the Bearer token from the `Authorization` header
4. **get_current_user()** decodes and validates the JWT; fetches the user from the database
5. **require_role("admin")** checks the user's role; raises 403 if not admin
6. **Handler** queries the database via `UserRepository.list()`
7. **AuditRepository.log()** records the action `"admin_list_users"` to the audit log
8. **TimingMiddleware** stamps `X-Process-Time` on the response
9. JSON response is returned to the client

---

## Side Effects

- Every successful call writes an entry to the `audit_logs` table recording:
  - `user_id` — the admin who made the request
  - `action` — `"admin_list_users"`
  - `timestamp` — UTC time of the request

---

## Notes

- Results are ordered by database insertion order by default
- Use `skip` and `limit` together for pagination: page 2 of 10 = `skip=10&limit=10`
- The `SECRET_KEY` used for JWT signing must be kept secret and rotated regularly in production
