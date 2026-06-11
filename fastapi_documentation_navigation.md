# Exercise: Documentation Navigation for FastAPI
# Part 1: Learning Roadmap | Part 2: Deep Dive | Part 3: Reference Guide | Part 4: Blog Mini-App

---

## Part 1: FastAPI Learning Roadmap

*Goal: Personalized reading guide for FastAPI documentation*

### Recommended Reading Order for a New Developer

| Step | Documentation Section | Why Read It First |
|------|-----------------------|-------------------|
| 1 | First Steps | Understand the minimal viable FastAPI app |
| 2 | Path Parameters & Query Parameters | How URLs and inputs work |
| 3 | Request Body with Pydantic | FastAPI's core data validation system |
| 4 | Dependencies (Depends) | The most distinctive FastAPI feature |
| 5 | Security / OAuth2 | Authentication patterns |
| 6 | SQL Databases (Async) | Persistent data storage |
| 7 | Middleware | Cross-cutting concerns |
| 8 | Background Tasks | Async work after responses |

### 5 Most Important Sections for Building a REST API Quickly

1. **Path Operations** — defines your routes and HTTP methods
2. **Pydantic Models** — request/response validation with zero boilerplate
3. **Dependency Injection** — reusable auth, DB sessions, permissions
4. **HTTPException** — standardised error responses
5. **Async/Await** — non-blocking I/O for database and external calls

### Key Points from Dependency Injection Documentation

- `Depends()` resolves dependencies automatically before the route runs
- Dependencies can depend on other dependencies (layered chain)
- The same dependency instance is reused within a single request
- Use `yield` in a dependency for setup/teardown (e.g. DB sessions)
- Dependencies appear in OpenAPI docs automatically

---

## Part 2: Documentation Deep Dive — Dependency Injection

*Goal: Deep understanding of FastAPI's most distinctive feature*

### What is Dependency Injection in FastAPI?

FastAPI's `Depends()` system automatically resolves and injects values
into route functions. Instead of calling functions manually, you declare
what a route needs and FastAPI provides it.

### Three Levels of Dependencies in This Application

```
GET /admin/users/
    │
    ├── Depends(get_db)
    │       └── Opens AsyncSession, yields it, closes on exit
    │
    ├── Depends(get_current_user)
    │       ├── Depends(oauth2_scheme)   ← extracts Bearer token
    │       ├── Depends(get_db)          ← reuses same session
    │       └── Decodes JWT, fetches User from DB
    │
    └── Depends(require_role("admin"))
            └── Depends(get_current_user)  ← reuses same User
                    └── Checks user.role == "admin"
```

### Dependency Injection vs Manual Calls

```python
# WITHOUT DI — repeated in every route
async def list_users():
    db = AsyncSession()
    token = extract_token_from_request()
    user = decode_and_fetch_user(token, db)
    check_role(user, "admin")
    ...

# WITH DI — clean, testable, reusable
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    ...  # db and current_user are already validated and injected
```

---

## Part 3: FastAPI Concepts Reference Guide

*Goal: Map abstract documentation concepts to concrete code implementations*

### Dependency Injection Patterns

```python
# Pattern 1: Simple value injection
async def get_settings() -> Settings:
    return Settings()

@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name}

# Pattern 2: Database session (yield pattern)
async def get_db():
    async with AsyncSession() as session:
        yield session          # setup
    # teardown happens automatically after yield

# Pattern 3: Role-based access (factory pattern)
def require_role(role: str):
    async def checker(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(403, "Forbidden")
        return user
    return checker
```

### Path Operation Decorators

```python
@app.get("/items/{id}")        # Read one
@app.get("/items/")            # Read many
@app.post("/items/")           # Create
@app.put("/items/{id}")        # Replace
@app.patch("/items/{id}")      # Partial update
@app.delete("/items/{id}")     # Delete
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # runs after the response is sent — non-blocking
    ...

@app.post("/register/")
async def register(background_tasks: BackgroundTasks, email: str):
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"message": "Registered"}  # response sent immediately
```

---

## Part 4: Comprehensive Documentation Challenge
## FastAPI Blog API — Mini Application

*Challenge: RESTful API for a blog with auth, CRUD posts, comments, search*

```python
"""
FastAPI Blog API
================
Implements: user registration/auth, CRUD blog posts,
            comments on posts, basic search.
Built following FastAPI official documentation patterns.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import jwt

app = FastAPI(title="Blog API")

# ── PYDANTIC SCHEMAS ───────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    author_id: int
    post_id: int
    created_at: datetime

# ── AUTH ───────────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register/", status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user. Hashes password before storing."""
    # Check username not already taken
    existing = await UserRepository(User).get_by_username(db, user_data.username)
    if existing:
        raise HTTPException(400, "Username already registered")
    hashed = hash_password(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed)
    return await UserRepository(User).create(db, new_user)

@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    user = await UserService().authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ── BLOG POSTS ─────────────────────────────────────────────────────────────
@app.get("/posts/", response_model=List[PostResponse])
async def list_posts(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Return paginated list of all blog posts. Public endpoint."""
    return await PostRepository(Post).list(db, skip=skip, limit=limit)

@app.post("/posts/", response_model=PostResponse, status_code=201)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new blog post. Authentication required."""
    post = Post(title=post_data.title, content=post_data.content, author_id=current_user.id)
    return await PostRepository(Post).create(db, post)

@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single post by ID."""
    post = await PostRepository(Post).get(db, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    return post

@app.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a post. Only the author can update their own post."""
    post = await PostRepository(Post).get(db, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(403, "You can only edit your own posts")
    post.title   = post_data.title
    post.content = post_data.content
    await db.commit()
    return post

@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a post. Author or admin only."""
    post = await PostRepository(Post).get(db, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "Not authorised to delete this post")
    await db.delete(post)
    await db.commit()

# ── COMMENTS ───────────────────────────────────────────────────────────────
@app.get("/posts/{post_id}/comments/", response_model=List[CommentResponse])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    """List all comments on a post. Public endpoint."""
    return await CommentRepository(Comment).list_by_post(db, post_id)

@app.post("/posts/{post_id}/comments/", response_model=CommentResponse, status_code=201)
async def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a post. Authentication required."""
    post = await PostRepository(Post).get(db, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    comment = Comment(content=comment_data.content, author_id=current_user.id, post_id=post_id)
    return await CommentRepository(Comment).create(db, comment)

# ── SEARCH ─────────────────────────────────────────────────────────────────
@app.get("/posts/search/", response_model=List[PostResponse])
async def search_posts(
    q: str = Query(..., min_length=2, description="Search term"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search posts by title or content.
    Uses ILIKE for case-insensitive partial matching.
    """
    return await PostRepository(Post).search(db, query=q)
```

### How Documentation Informed Implementation Choices

- **Pydantic schemas** — docs showed separating Create/Response schemas to control
  what fields are required vs returned (e.g. password in, never out)
- **yield in get_db** — docs explained this is required for proper session lifecycle
- **OAuth2PasswordRequestForm** — docs showed this is the standard way to handle
  form-based login compatible with the Swagger UI
- **Query(...)** — docs showed how to add validation and description to query params
- **status_code=201/204** — docs showed correct HTTP semantics for create/delete
