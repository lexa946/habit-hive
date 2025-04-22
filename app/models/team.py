import uuid
from datetime import datetime

from sqlalchemy import UUID, ForeignKey, Column, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(nullable=True)
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    daily_completions: Mapped[list] = mapped_column(JSON, default=list)

    habits: Mapped[list["Habit"]] = relationship(back_populates="team", cascade="all, delete-orphan")

    owner: Mapped["User"] = relationship(back_populates="teams", foreign_keys=[owner_id])
    members: Mapped[list["User"]] = relationship(back_populates="team", foreign_keys="[User.team_id]")

    @property
    def members_count(self) -> int:
        """Return the total number of team members including the owner."""
        return len(self.members) + 1  # +1 for the owner