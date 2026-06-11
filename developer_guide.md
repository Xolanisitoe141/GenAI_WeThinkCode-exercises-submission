# Developer Usage Guide: GET /admin/users/

> Generated using Prompt 3: Practical developer usage guide

---

## Quick Start

This guide shows you how to authenticate and call the `GET /admin/users/` endpoint
step by step, with real code examples.

---

## Step 1 — Install Dependencies

```bash
pip install requests pyjwt
```

---

## Step 2 — Get an Access Token

Before calling the endpoint you need a JWT token. Call `/token` with admin credentials:

```python
import requests

response = requests.post(
    "http://localhost:8000/token",
    data={"username": "admin_user", "password": "your_password"}
)

token = response.json()["access_token"]
print("Token:", token)
```

---

## Step 3 — Call the Endpoint

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN    = "paste_your_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

response = requests.get(f"{BASE_URL}/admin/users/", headers=headers)

if response.status_code == 200:
    users = response.json()
    for user in users:
        print(f"ID: {user['id']} | Username: {user['username']} | Role: {user['role']}")
else:
    print(f"Error {response.status_code}: {response.json()['detail']}")
```

**Expected output:**
```
ID: 1 | Username: alice | Role: admin
ID: 2 | Username: bob   | Role: user
ID: 3 | Username: carol | Role: user
```

---

## Step 4 — Use Pagination

Fetch users in pages of 10:

```python
def get_users_page(token, page=1, page_size=10):
    headers = {"Authorization": f"Bearer {token}"}
    skip    = (page - 1) * page_size

    response = requests.get(
        f"{BASE_URL}/admin/users/",
        headers=headers,
        params={"skip": skip, "limit": page_size}
    )
    return response.json()

# Get page 1
page1 = get_users_page(token, page=1)

# Get page 2
page2 = get_users_page(token, page=2)
```

---

## Step 5 — Check Processing Time

Every response includes an `X-Process-Time` header (milliseconds):

```python
response = requests.get(f"{BASE_URL}/admin/users/", headers=headers)
print("Processed in:", response.headers.get("X-Process-Time"), "ms")
```

---

## Handling Errors

Always handle the three possible error states:

```python
response = requests.get(f"{BASE_URL}/admin/users/", headers=headers)

if response.status_code == 200:
    users = response.json()
    # process users...

elif response.status_code == 401:
    # Token is missing, expired, or invalid
    # Action: re-authenticate and get a new token
    print("Authentication failed — please log in again.")

elif response.status_code == 403:
    # Token is valid but user is not an admin
    # Action: contact your administrator for elevated access
    print("Access denied — admin role required.")

else:
    print(f"Unexpected error: {response.status_code}")
```

---

## Using with curl (Command Line)

**Get a token:**
```bash
curl -X POST http://localhost:8000/token \
  -d "username=admin_user&password=your_password"
```

**Call the endpoint:**
```bash
curl -X GET http://localhost:8000/admin/users/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**With pagination:**
```bash
curl -X GET "http://localhost:8000/admin/users/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Forgetting `Bearer ` prefix in the header | Always use `Authorization: Bearer <token>` |
| Using an expired token | Tokens expire in 15 minutes — re-authenticate |
| Calling with a non-admin account | Only users with `role = "admin"` can access this endpoint |
| Not handling pagination | Default limit is 100 — use `skip` + `limit` for large datasets |

---

## What Gets Logged

Every successful call automatically writes to the audit log:

```json
{
  "user_id": 1,
  "action": "admin_list_users",
  "timestamp": "2026-06-10T10:30:00Z"
}
```

This means all admin activity on this endpoint is traceable — no extra code needed.

---

## Running the App Locally

```bash
cd fastapi_patterns
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI
where you can test the endpoint directly in your browser.
