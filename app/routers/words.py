"""Word CRUD, list, and search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..utils import classify_word

router = APIRouter(prefix="/words", tags=["words"])


def _word_to_schema(word: models.Word) -> schemas.WordResponse:
    """Convert ORM model to response schema."""
    return schemas.WordResponse(
        id=word.id,
        word_text=word.word_text,
        meaning=word.meaning,
        language=word.language,
        category=word.category.name,
        created_at=word.created_at,
    )


def _get_or_create_category(db: Session, name: str) -> models.Category:
    """Get category by name; create it if missing."""
    category = db.query(models.Category).filter(models.Category.name == name).first()
    if category:
        return category

    category = models.Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _normalize_category_name(name: str) -> str:
    """Normalize category name for stable storage/filtering."""
    normalized = name.strip().lower()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name is required")
    return normalized


def _resolve_category(
    db: Session,
    word_text: str,
    meaning: str,
    category_mode: str,
    category_name: str | None,
) -> models.Category:
    """
    Resolve category by mode.

    Modes:
    - auto: classify from rule dictionary
    - existing: use user-selected existing category only
    - new: create (or reuse) user-entered category name
    """
    if category_mode == "auto":
        auto_name = classify_word(word_text, meaning)
        return _get_or_create_category(db, _normalize_category_name(auto_name))

    if category_mode == "existing":
        if not category_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category_name is required when category_mode is 'existing'",
            )
        selected = _normalize_category_name(category_name)
        category = db.query(models.Category).filter(models.Category.name == selected).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Selected category '{selected}' does not exist",
            )
        return category

    if category_mode == "new":
        if not category_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category_name is required when category_mode is 'new'",
            )
        return _get_or_create_category(db, _normalize_category_name(category_name))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="category_mode must be one of: auto, existing, new",
    )


@router.post("/", response_model=schemas.WordResponse, status_code=status.HTTP_201_CREATED)
def create_word(
    payload: schemas.WordCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create word with automatic category classification."""
    duplicate = (
        db.query(models.Word)
        .filter(
            models.Word.user_id == current_user.id,
            func.lower(models.Word.word_text) == payload.word_text.strip().lower(),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate word for this user")

    category = _resolve_category(
        db=db,
        word_text=payload.word_text,
        meaning=payload.meaning,
        category_mode=payload.category_mode,
        category_name=payload.category_name,
    )

    word = models.Word(
        word_text=payload.word_text.strip(),
        meaning=payload.meaning.strip(),
        language=payload.language.strip().lower(),
        user_id=current_user.id,
        category_id=category.id,
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return _word_to_schema(word)


@router.get("/", response_model=list[schemas.WordResponse])
def list_words(
    category: str | None = None,
    sort: str = Query("created_at", pattern="^(created_at|alphabet)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List words by user, optional category filter and sort."""
    query = (
        db.query(models.Word)
        .join(models.Category)
        .filter(models.Word.user_id == current_user.id)
    )

    if category:
        query = query.filter(models.Category.name == category.strip().lower())

    if sort == "alphabet":
        query = query.order_by(models.Word.word_text.asc())
    else:
        query = query.order_by(models.Word.created_at.desc())

    return [_word_to_schema(word) for word in query.all()]


@router.get("/search", response_model=list[schemas.WordResponse])
def search_words(
    q: str = Query(..., min_length=1, description="Partial word search"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Search words with partial text match."""
    words = (
        db.query(models.Word)
        .join(models.Category)
        .filter(
            models.Word.user_id == current_user.id,
            models.Word.word_text.ilike(f"%{q.strip()}%"),
        )
        .order_by(models.Word.created_at.desc())
        .all()
    )
    return [_word_to_schema(word) for word in words]


@router.get("/{word_id}", response_model=schemas.WordResponse)
def get_word(
    word_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get one word detail."""
    word = (
        db.query(models.Word)
        .join(models.Category)
        .filter(models.Word.id == word_id, models.Word.user_id == current_user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    return _word_to_schema(word)


@router.put("/{word_id}", response_model=schemas.WordResponse)
def update_word(
    word_id: int,
    payload: schemas.WordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Edit a word and re-run automatic classification."""
    word = (
        db.query(models.Word)
        .filter(models.Word.id == word_id, models.Word.user_id == current_user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

    duplicate = (
        db.query(models.Word)
        .filter(
            models.Word.user_id == current_user.id,
            func.lower(models.Word.word_text) == payload.word_text.strip().lower(),
            models.Word.id != word_id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate word for this user")

    category = _resolve_category(
        db=db,
        word_text=payload.word_text,
        meaning=payload.meaning,
        category_mode=payload.category_mode,
        category_name=payload.category_name,
    )

    word.word_text = payload.word_text.strip()
    word.meaning = payload.meaning.strip()
    word.language = payload.language.strip().lower()
    word.category_id = category.id

    db.commit()
    db.refresh(word)
    return _word_to_schema(word)


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a word that belongs to the current user."""
    word = (
        db.query(models.Word)
        .filter(models.Word.id == word_id, models.Word.user_id == current_user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

    db.delete(word)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
