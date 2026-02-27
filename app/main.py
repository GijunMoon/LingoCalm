"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .database import SessionLocal, engine
from .models import Base, Category
from .routers import categories, practice, users, words
from .utils import DEFAULT_CATEGORY, get_rule_category_names

# Create DB tables on startup (Alembic can be added later if needed).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vocabulary Learning API",
    version="1.0.0",
    description="FastAPI + SQLite + JWT + rule/FastText category classification",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Allow front-end clients to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets if present.
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# REST routers.
app.include_router(users.router)
app.include_router(words.router)
app.include_router(categories.router)
app.include_router(practice.router)


@app.on_event("startup")
def seed_predefined_categories():
    """Ensure predefined categories from rule dictionary exist in DB."""
    db = SessionLocal()
    try:
        existing = {name for (name,) in db.query(Category.name).all()}
        required = set(get_rule_category_names())
        required.add(DEFAULT_CATEGORY)

        for name in sorted(required):
            if name not in existing:
                db.add(Category(name=name))
        db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    """UI entrypoint."""
    return RedirectResponse(url="/login", status_code=302)


def _serve_static_file(filename: str) -> FileResponse:
    """Serve one static HTML page."""
    target = STATIC_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    return FileResponse(str(target))


@app.get("/login")
def login_page():
    return _serve_static_file("login.html")


@app.get("/register")
def register_page():
    return _serve_static_file("register.html")


@app.get("/dashboard")
def dashboard_page():
    return _serve_static_file("dashboard.html")


@app.get("/word-list")
def word_list_page():
    return _serve_static_file("word_list.html")


@app.get("/word-add")
def word_add_page():
    return _serve_static_file("word_add.html")


@app.get("/word-details")
def word_details_page():
    return _serve_static_file("word_details.html")


@app.get("/practice")
def practice_page():
    return _serve_static_file("practice.html")


@app.get("/health")
def health():
    """Health check endpoint for deployment probes."""
    return {"status": "ok"}
