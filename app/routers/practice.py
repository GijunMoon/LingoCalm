"""Practice endpoint for random words by category."""

import random

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/{category_name}", response_model=schemas.PracticeResponse)
def get_practice_words(
    category_name: str,
    count: int = Query(3, ge=3, le=20),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return random words for a category.

    Requirement: at least 3 words must be available.
    """
    words = (
        db.query(models.Word)
        .join(models.Category)
        .filter(
            models.Word.user_id == current_user.id,
            models.Category.name == category_name.strip().lower(),
        )
        .all()
    )

    if len(words) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 words are required for practice",
        )

    if len(words) < count:
        # Keep API explicit about available volume if caller asks for too many.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested {count}, but only {len(words)} words exist in this category",
        )

    sampled = random.sample(words, k=count)
    return schemas.PracticeResponse(
        category=category_name.strip().lower(),
        requested_count=count,
        words=[
            schemas.PracticeWordResponse(
                id=word.id,
                word_text=word.word_text,
                meaning=word.meaning,
                language=word.language,
            )
            for word in sampled
        ],
    )
