from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.db.session import get_session

DbSession = Annotated[Session, Depends(get_session)]

