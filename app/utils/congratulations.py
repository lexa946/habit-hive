from sqlalchemy.orm import Session
from app.models.congratulation import Congratulation
from app.models.user import User
import uuid


def create_all_habits_completed_congratulation(db: Session, user: User) -> None:
    """Создать поздравление за выполнение всех привычек"""
    congratulation = Congratulation(
        id=uuid.uuid4(),
        user_id=user.id,
        message="Поздравляем! Вы выполнили все свои привычки за сегодня! 🎉",
        type="all_habits_completed"
    )
    db.add(congratulation)
    db.commit() 