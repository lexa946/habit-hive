from datetime import datetime
import uuid
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class Congratulation(Base):
    __tablename__ = "congratulations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    message: Mapped[str]
    type: Mapped[str]  # Тип поздравления (например, "all_habits_completed")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_read: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="congratulations") 