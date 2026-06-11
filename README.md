# Using GenAI to Support Software Development
## Complete Exercise Submissions

---

## Exercise 4 — Code Readability Challenge (`exercise4_discount/`)
Refactored a poorly formatted Python discount calculator.
- `discount.py` — refactored code with helper functions and docstrings
- `test_discount.py` — 5 passing unit tests

**Run:** `cd exercise4_discount && python -m pytest test_discount.py -v`

---

## FastAPI Code Patterns (`fastapi_patterns/`)
Analysed and extended a FastAPI application with Repository pattern, DI, JWT auth, RBAC, middleware, audit logging.
- `main.py` — full application
- `models.py`, `database.py`, `requirements.txt`

**Run:** `cd fastapi_patterns && pip install -r requirements.txt && uvicorn main:app --reload`

---

## Exercise: Code Documentation (`code_documentation/`)
Added comprehensive inline documentation to the FastAPI app using AI prompting.
- `documented_fastapi_app.py` — fully documented source with "why" comments
- `reflection_notes.md` — prompts used and lessons learned

---

## Exercise: API Documentation (`api_documentation/`)
Documented the `GET /admin/users/` endpoint using 3 prompt strategies.
- `endpoint_code.py` — original endpoint code
- `endpoint_docs.md` — comprehensive Markdown docs (Prompt 1)
- `endpoint_openapi.yaml` — OpenAPI 3.0 specification (Prompt 2)
- `developer_guide.md` — practical usage guide with curl + Python examples (Prompt 3)

---

## Exercise: README & User Guide (`readme_user_guide/`)
Created professional project documentation using AI.
- `README.md` — project overview, quick start, features table
- `USER_GUIDE.md` — full guide with auth, pagination, error handling, security

---

## Exercise: Documentation Navigation (`documentation_navigation/`)
Used FastAPI official docs to build a learning roadmap and a complete blog API.
- `fastapi_documentation_navigation.md` — Parts 1–4: roadmap, deep dive, reference guide, blog mini-app

---

## Exercise: Contextual Learning (`contextual_learning/`)
Mapped Django/Flask mental models to FastAPI equivalents.
- `mental_model_translation.md` — full comparison table + philosophy differences

---

*Course: Using GenAI to Support Software Development*
