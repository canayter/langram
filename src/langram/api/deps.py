"""Shared dependencies: the database session, the loaded language, the caller."""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Iterator

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..db.models import User
from ..loader import Language, load_language
from .config import Settings, get_settings
from .security import read_access_token


@lru_cache(maxsize=1)
def _sessionmaker() -> sessionmaker:
    settings = get_settings()
    kwargs = {}
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return sessionmaker(create_engine(settings.database_url, **kwargs), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with _sessionmaker()() as session:
        yield session


@lru_cache(maxsize=1)
def get_language() -> Language:
    """Loaded once. The grammar does not change while the process runs."""
    return load_language("tr")


def current_user(
    session: Annotated[Session, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not signed in")
    try:
        user_id = read_access_token(authorization.split(" ", 1)[1])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session expired") from None
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no such account")
    return user


SessionDep = Annotated[Session, Depends(get_session)]
LanguageDep = Annotated[Language, Depends(get_language)]
UserDep = Annotated[User, Depends(current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
