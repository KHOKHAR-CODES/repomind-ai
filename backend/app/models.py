from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="owner", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(1024), nullable=False)
    branch = Column(String(255), default="main")
    local_path = Column(String(1024), default="")
    last_commit_hash = Column(String(64), default="")
    indexing_status = Column(String(32), default="pending")  # pending | indexing | completed | failed
    file_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="repositories")
    chats = relationship("Chat", back_populates="repository", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    title = Column(String(512), default="New chat")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="chats")
    repository = relationship("Repository", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String(16), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    source_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, server_default=func.now())

    chat = relationship("Chat", back_populates="messages")
