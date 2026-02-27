"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """Registered user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    words = relationship("Word", back_populates="owner", cascade="all, delete-orphan")


class Category(Base):
    """Word category table."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    words = relationship("Word", back_populates="category")


class Word(Base):
    """Vocabulary entry owned by one user."""

    __tablename__ = "words"
    __table_args__ = (
        UniqueConstraint("user_id", "word_text", name="uq_words_user_word_text"),
    )

    id = Column(Integer, primary_key=True, index=True)
    word_text = Column(String(120), index=True, nullable=False)
    meaning = Column(String(500), nullable=False)  # Korean meaning used for classification.
    language = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    owner = relationship("User", back_populates="words")
    category = relationship("Category", back_populates="words")
