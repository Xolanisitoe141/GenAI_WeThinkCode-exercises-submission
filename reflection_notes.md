# Exercise: Code Documentation — Reflection Notes

## What Was Documented

The `documented_fastapi_app.py` file contains the complete FastAPI application
with comprehensive inline documentation added using AI prompting.

---

## AI Prompts Used

**Prompt 1 — Module and class docstrings:**
> "Add comprehensive docstrings to every class and method in this FastAPI code.
> For each docstring explain not just WHAT the code does but WHY it is structured
> this way. Include parameter descriptions and any security considerations."

**Prompt 2 — Inline comments:**
> "Add inline comments to the complex sections of this code — specifically the
> JWT flow, the Generic[T] pattern, and the dependency injection chain.
> Comments should explain the reasoning, not just restate the code."

**Prompt 3 — Type hints and examples:**
> "Review the documentation for completeness. Are there any return types, edge
> cases, or error conditions that aren't documented? Add anything missing."

---

## Most Challenging Parts to Document

- **Generic[T] repository** — Hard to explain why TypeVar is needed without
  showing the alternative (copy-pasted classes per model).
- **JWT security trade-offs** — The single 401 error for all auth failures
  needed explanation because it looks like a bug but is intentional.
- **Middleware vs decorator** — Why TimingMiddleware wraps everything rather
  than being applied per-route needed a clear "why" comment.

---

## Most Effective Documentation Format

Docstrings with a **"Why" section** had the biggest impact. Knowing that
`get_db()` uses try/finally to prevent connection leaks is far more useful
than just "yields a database session."

---

## How to Incorporate into Development Workflow

1. Write code first, then ask AI: *"Add docstrings explaining the why behind
   each design decision in this code"*
2. Use AI to check: *"What parts of this code would confuse a new developer?
   What documentation is missing?"*
3. Commit documentation alongside code — never as an afterthought.
