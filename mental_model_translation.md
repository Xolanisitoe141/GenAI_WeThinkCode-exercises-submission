# Exercise: Contextual Learning with FastAPI
# Mental Model Translation — Django/Flask → FastAPI

---

## Part 4: Mental Model Translation Table

*Mapping familiar web framework concepts to FastAPI equivalents*

| Concept | Django | Flask | FastAPI | Key Difference |
|---------|--------|-------|---------|----------------|
| **Route definition** | `urls.py` + `views.py` | `@app.route()` | `@app.get/post/put/delete()` | FastAPI separates HTTP method at decorator level |
| **Middleware** | `MIDDLEWARE` list in settings | `@app.before_request` | Class with `__call__` + `app.middleware("http")` | FastAPI uses ASGI middleware — wraps entire request/response |
| **Request validation** | Django Forms / DRF Serializers | Manual `request.json` | Pydantic `BaseModel` in function signature | FastAPI validates automatically — no `.is_valid()` call needed |
| **Database ORM** | Django ORM (`models.py`) | SQLAlchemy (manual setup) | SQLAlchemy async (`AsyncSession`) | FastAPI has no built-in ORM — SQLAlchemy async is the standard |
| **Authentication** | `django.contrib.auth` | Flask-Login / JWT manually | `OAuth2PasswordBearer` + `Depends()` | FastAPI auth is just a dependency — highly composable |
| **Permissions / Roles** | `@permission_required` | Custom decorator | `Depends(require_role("admin"))` | FastAPI uses DI factory pattern — same power, more flexible |
| **Response serialization** | DRF Serializers | `jsonify()` | Pydantic `response_model=` | FastAPI serializes and validates output automatically |
| **Async support** | Limited (Django 3.1+) | Limited | First-class `async def` everywhere | FastAPI built on Starlette — async is the default, not an add-on |
| **Auto API docs** | DRF Browsable API | Flask-Swagger (manual) | `/docs` and `/redoc` built in | FastAPI generates OpenAPI docs from code with zero config |
| **Controllers** | Class-Based Views | Blueprints | APIRouter | FastAPI routers group related routes into separate files |
| **Config / Settings** | `settings.py` | `app.config` | Pydantic `BaseSettings` | FastAPI settings use Pydantic — type-safe, env-var aware |
| **Error handling** | Custom exception handlers | `@app.errorhandler` | `HTTPException` + `@app.exception_handler` | FastAPI uses standard HTTP exceptions with detail field |

---

## Key Differences in Approach and Philosophy

### 1. Everything is a Type Annotation
FastAPI reads Python type hints to do validation, serialization, and
documentation automatically. In Django/Flask you configure these separately.

```python
# Flask — manual validation
@app.route("/users/<int:user_id>")
def get_user(user_id):
    if not isinstance(user_id, int):  # Flask already handled this
        return jsonify({"error": "invalid"}), 400
    ...

# FastAPI — type hint IS the validation
@app.get("/users/{user_id}")
async def get_user(user_id: int):  # int enforced automatically, 422 if not
    ...
```

### 2. Dependency Injection Over Decorators
Django and Flask use decorators for cross-cutting concerns.
FastAPI uses `Depends()` — this makes dependencies composable and testable.

```python
# Django pattern — decorator stacking
@login_required
@permission_required("admin")
def my_view(request):
    ...

# FastAPI pattern — dependency chain
async def my_route(user: User = Depends(require_role("admin"))):
    ...
```

### 3. Async by Default
FastAPI routes are `async def` — they don't block the event loop.
This means thousands of concurrent requests can be handled with a
single process, unlike Django/Flask which block per request by default.

---

## Updated Mental Model for FastAPI

```
FastAPI Application
│
├── @app.get/post/...()    ← Route + HTTP method together (vs urls.py + views.py)
│
├── Pydantic Models        ← Request validation + Response serialization (vs Forms/Serializers)
│
├── Depends()              ← Cross-cutting concerns: DB, auth, roles (vs decorators)
│   ├── get_db()           ← Session lifecycle (yield pattern)
│   ├── get_current_user() ← JWT decode + DB lookup
│   └── require_role()     ← RBAC factory
│
├── APIRouter              ← Group related routes (vs Blueprints / Django apps)
│
├── ASGI Middleware        ← Wrap all requests (vs Django MIDDLEWARE list)
│
└── Lifespan (async)       ← Startup/shutdown (vs Django AppConfig.ready())
```

---

## JWT Patterns Identified Across Frameworks

| Framework | JWT Library | Token Storage | Verification Pattern |
|-----------|-------------|---------------|---------------------|
| Django | `djangorestframework-simplejwt` | DB blacklist | Middleware |
| Flask | `flask-jwt-extended` | In-memory / Redis | Decorator `@jwt_required` |
| FastAPI | `python-jose` or `pyjwt` | Stateless | `Depends(get_current_user)` |

FastAPI's approach is the most composable — the JWT verification is
a plain async function that can be tested independently and combined
with other dependencies without decorators.
