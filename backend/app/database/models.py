import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id = Column(Text, unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text)
    avatar_url = Column(Text)
    timezone = Column(Text, default="UTC")
    digest_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")
    drive_webhooks = relationship("DriveWebhook", back_populates="user", cascade="all, delete-orphan")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    scope = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    user = relationship("User", back_populates="oauth_tokens")


class DriveWebhook(Base):
    __tablename__ = "drive_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    channel_id = Column(Text, unique=True, nullable=False)
    resource_id = Column(Text)
    expiry = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    user = relationship("User", back_populates="drive_webhooks")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(Text)
    meeting_date = Column(Date)
    duration_minutes = Column(Integer)
    drive_file_id = Column(Text, unique=True, nullable=False)
    summary = Column(Text)
    participant_names = Column(ARRAY(Text))
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    user = relationship("User", back_populates="meetings")
    chunks = relationship("Chunk", back_populates="meeting", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    pinecone_id = Column(Text, unique=True, nullable=False)
    speaker = Column(Text)
    start_time = Column(Text)
    end_time = Column(Text)
    text_preview = Column(Text)
    chunk_index = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    meeting = relationship("Meeting", back_populates="chunks")
