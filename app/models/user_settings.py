import uuid
from datetime import time

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    
    # Theme settings
    theme: Mapped[str] = mapped_column(default="system")  # light, dark, system
    
    # Notification settings
    daily_reminder: Mapped[bool] = mapped_column(default=True)
    reminder_time: Mapped[time] = mapped_column(default=time(20, 0))  # 20:00 by default
    
    # Habit settings
    default_mastery_goal: Mapped[int] = mapped_column(default=100)  # Default mastery goal in percent
    default_period: Mapped[int] = mapped_column(default=30)  # Default period in days
    
    # Relationship with User
    user: Mapped["User"] = relationship(back_populates="settings") 