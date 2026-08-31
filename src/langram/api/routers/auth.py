"""Registration, sign in, and guest accounts.

Guest mode exists because asking for an email before someone has seen a single
exercise loses them. A guest is a real row with a placeholder address, so their
history is already durable when they decide to claim it.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ...db.models import User
from ..deps import SessionDep, UserDep
from ..schemas import Credentials, TokenOut
from ..security import create_access_token, hash_password, needs_rehash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

GUEST_DOMAIN = "guest.invalid"


def _is_guest(user: User) -> bool:
    return user.email.endswith("@" + GUEST_DOMAIN)


def _token(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user.id), user_id=user.id,
                    is_guest=_is_guest(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: Credentials, session: SessionDep) -> TokenOut:
    existing = session.scalars(select(User).where(User.email == body.email)).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "that email is already registered")
    user = User(email=body.email, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    return _token(user)


@router.post("/login", response_model=TokenOut)
def login(body: Credentials, session: SessionDep) -> TokenOut:
    user = session.scalars(select(User).where(User.email == body.email)).first()
    # Verify even when there is no such user, so the response time does not
    # reveal which emails exist.
    stored = user.password_hash if user else hash_password("not-a-real-password")
    if not verify_password(body.password, stored) or user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "email or password is wrong")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
        session.commit()
    return _token(user)


@router.post("/guest", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def guest(session: SessionDep) -> TokenOut:
    user = User(email=f"guest-{uuid.uuid4().hex}@{GUEST_DOMAIN}", password_hash="")
    session.add(user)
    session.commit()
    return _token(user)


@router.post("/claim", response_model=TokenOut)
def claim(body: Credentials, session: SessionDep, user: UserDep) -> TokenOut:
    """Turn the current guest into a real account, keeping their history."""
    if not _is_guest(user):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "this account is already registered")
    taken = session.scalars(select(User).where(User.email == body.email)).first()
    if taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "that email is already registered")
    user.email = body.email
    user.password_hash = hash_password(body.password)
    session.commit()
    return _token(user)
