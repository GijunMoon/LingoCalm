"""Category list and category-word endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..utils import DEFAULT_CATEGORY, get_rule_category_names

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[schemas.CategorySummaryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List category names and word counts for current user.

    Includes categories from rule dictionary even when count is zero.
    """
    rows = (
        db.query(models.Category.name, func.count(models.Word.id))
        .outerjoin(
            models.Word,
            (models.Word.category_id == models.Category.id)
            & (models.Word.user_id == current_user.id),
        )
        .group_by(models.Category.name)
        .all()
    )
    counts = {name: int(count) for name, count in rows}

    rule_categories = set(get_rule_category_names())
    rule_categories.add(DEFAULT_CATEGORY)
    all_names = sorted(rule_categories.union(counts.keys()))

    return [
        schemas.CategorySummaryResponse(name=name, count=counts.get(name, 0))
        for name in all_names
    ]


@router.get("/{category_name}/words", response_model=list[schemas.WordResponse])
def list_words_by_category(
    category_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List words filtered by one category name."""
    words = (
        db.query(models.Word)
        .join(models.Category)
        .filter(
            models.Word.user_id == current_user.id,
            models.Category.name == category_name.strip().lower(),
        )
        .order_by(models.Word.created_at.desc())
        .all()
    )

    return [
        schemas.WordResponse(
            id=word.id,
            word_text=word.word_text,
            meaning=word.meaning,
            language=word.language,
            category=word.category.name,
            created_at=word.created_at,
        )
        for word in words
    ]
