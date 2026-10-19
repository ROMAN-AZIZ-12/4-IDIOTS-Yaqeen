"""GET /banks route (authenticated, no role restriction)."""
from __future__ import annotations

from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models import Bank

router = APIRouter()


class BankResponse(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/banks", response_model=list[BankResponse])
def list_banks(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[object, Depends(get_current_user)],
) -> Sequence[Bank]:
    return db.execute(select(Bank).order_by(Bank.name)).scalars().all()
