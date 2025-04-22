import uuid
from datetime import datetime, date

from sqlalchemy import UUID, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base



class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    description: Mapped[str]
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    team_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_completed: Mapped[bool] = mapped_column(default=False)
    target_date: Mapped[date | None] = mapped_column(nullable=True)  # Целевая дата завершения
    mastery_progress: Mapped[int] = mapped_column(default=0)  # Прогресс освоения в процентах
    mastery_goal: Mapped[int] = mapped_column(default=100)  # Целевой процент освоения

    user: Mapped["User"] = relationship(back_populates="habits")
    team: Mapped["Team"] = relationship(back_populates="habits", lazy="joined")
    trackings: Mapped[list["Tracking"]] = relationship(back_populates="habit", cascade="all, delete-orphan")