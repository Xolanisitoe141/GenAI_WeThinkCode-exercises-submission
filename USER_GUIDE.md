# User Guide: FastAPI User Management API

This guide walks through every feature of the API with practical examples.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Managing Users](#managing-users)
3. [Pagination](#pagination)
4. [Error Reference](#error-reference)
5. [Monitoring & Performance](#monitoring)
6. [Security Best Practices](#security)

---

## 1. Authentication

### Get a Token

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin_user&password=your_password"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Tokens expire after **15 minutes**. Request a new one when you receive a `401`.

### Use the Token

Add it to every request as a header:

```bash
curl http://localhost:8000/admin/users/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Python Example

```python
import requests

# Step 1: authenticate
login = requests.post(
    "http://localhost:8000/token",
    data={"username": "admin_user", "password": "secret"}
)
token = login.json()["access_token"]

# Step 2: use the token
headers = {"Authorization": f"Bearer {token}"}
users   = requests.get("http://localhost:8000/admin/users/", headers=headers)
print(users.json())
```

---

## 2. Managing Users

### List All Users (Admin Only)

```python
response = requests.get(
    "http://localhost:8000/admin/users/",
    headers={"Authorization": f"Bearer {token}"}
)

for user in response.json():
    print(f"{user['id']:3} | {user['username']:20} | {user['role']:10} | {user['status']}")
```

**Sample output:**
```
  1 | alice                | admin      | member
  2 | bob                  | user       | regular
  3 | carol                | user       | vip
```

---

## 3. Pagination

Use `skip` and `limit` to page through large result sets.

```python
def get_page(token, page=1, page_size=10):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(
        "http://localhost:8000/admin/users/",
        headers=headers,
        params={"skip": (page - 1) * page_size, "limit": page_size}
    ).json()

page1 = get_page(token, page=1)  # records 1-10
page2 = get_page(token, page=2)  # records 11-20
```

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `skip` | `0` | — | Records to skip |
| `limit` | `100` | `1000` | Records per page |

---

## 4. Error Reference

| Code | Meaning | Fix |
|------|---------|-----|
| `401 Unauthorized` | Token missing, expired, or invalid | Re-authenticate at `/token` |
| `403 Forbidden` | Valid token but wrong role | Use an admin account |
| `422 Unprocessable` | Invalid query parameter type | Check parameter types |
| `500 Internal Error` | Server-side error | Check server logs |

### Handling Errors in Python

```python
response = requests.get(url, headers=headers)

match response.status_code:
    case 200:
        return response.json()
    case 401:
        token = refresh_token()          # re-authenticate
        return get_users(token)          # retry once
    case 403:
        raise PermissionError("Admin access required")
    case _:
        raise RuntimeError(f"Unexpected error: {response.status_code}")
```

---

## 5. Monitoring & Performance

Every response includes an `X-Process-Time` header showing server processing
time in milliseconds:

```python
response = requests.get(url, headers=headers)
print(f"Server processed in: {response.headers['X-Process-Time']} ms")
```

Use this to:
- Monitor slow endpoints
- Compare performance before and after optimisations
- Set up alerting thresholds in your API gateway

---

## 6. Security Best Practices

**Change the SECRET_KEY before deploying:**
```python
# Generate a secure key
import secrets
print(secrets.token_hex(32))
# Set as environment variable — never hardcode in source
```

**Store tokens securely:**
- Never store tokens in localStorage (XSS vulnerable)
- Use httpOnly cookies or secure memory storage
- Always use HTTPS in production

**Rotate tokens:**
- Default expiry is 15 minutes — suitable for most use cases
- Implement refresh tokens for long-lived sessions

---

## Audit Log

Every call to `/admin/users/` automatically records an audit entry:

```json
{
  "user_id": 1,
  "action": "admin_list_users",
  "timestamp": "2026-06-10T10:30:00Z"
}
```

This provides a full trail of admin activity with no extra code required.
