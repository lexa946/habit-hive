from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.congratulation import Congratulation
from app.schemas.congratulation import Congratulation as CongratulationSchema
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[CongratulationSchema])
def get_congratulations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все поздравления пользователя"""
    congratulations = db.query(Congratulation).filter(
        Congratulation.user_id == current_user.id
    ).order_by(Congratulation.created_at.desc()).all()
    return congratulations


@router.post("/mark-as-read/{congratulation_id}")
def mark_as_read(
    congratulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отметить поздравление как прочитанное"""
    congratulation = db.query(Congratulation).filter(
        Congratulation.id == congratulation_id,
        Congratulation.user_id == current_user.id
    ).first()
    
    if not congratulation:
        raise HTTPException(status_code=404, detail="Поздравление не найдено")
    
    congratulation.is_read = True
    db.commit()
    return {"message": "Поздравление отмечено как прочитанное"} 