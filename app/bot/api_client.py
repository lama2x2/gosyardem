"""HTTP-клиент бота к API бэкенда."""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

API_BASE = f"{settings.api_base_url.rstrip('/')}/api"
_TIMEOUT = 30.0


async def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        return await getattr(client, method)(f"{API_BASE}{path}", **kwargs)


async def sync_telegram_profile(telegram_id: int, telegram_name: str) -> None:
    try:
        r = await _request(
            "patch",
            f"/users/by-telegram/{telegram_id}/profile",
            json={"telegram_name": telegram_name},
        )
        if r.status_code != 200:
            return
    except httpx.HTTPError:
        logger.debug("Не удалось обновить telegram_name для %s", telegram_id)


async def register_citizen(telegram_id: int, telegram_name: Optional[str] = None) -> Optional[dict]:
    try:
        payload: dict = {"telegram_id": telegram_id, "role": "citizen"}
        if telegram_name:
            payload["telegram_name"] = telegram_name
        r = await _request(
            "post",
            "/users/",
            json=payload,
        )
        if r.status_code in (200, 201):
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API register_citizen")
    return None


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    try:
        r = await _request("get", f"/users/by-telegram/{telegram_id}")
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API при поиске пользователя")
    return None


async def get_user(user_id: int) -> Optional[dict]:
    try:
        r = await _request("get", f"/users/{user_id}")
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API get_user id=%s", user_id)
    return None


async def list_users(role: Optional[str] = None) -> List[dict]:
    try:
        params = {"role": role} if role else None
        r = await _request("get", "/users/", params=params)
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API list_users")
    return []


async def list_request_types() -> List[dict]:
    try:
        r = await _request("get", "/request-types/")
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API list_request_types")
    return []


async def list_requests() -> List[dict]:
    try:
        r = await _request("get", "/requests/")
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API list_requests")
    return []


async def get_request(request_id: int) -> Optional[dict]:
    try:
        r = await _request("get", f"/requests/{request_id}")
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API get_request id=%s", request_id)
    return None


async def create_request(payload: dict) -> Optional[dict]:
    try:
        r = await _request("post", "/requests/", json=payload)
        if r.status_code in (200, 201):
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API create_request")
    return None


async def patch_request(request_id: int, payload: dict) -> Optional[dict]:
    try:
        r = await _request("patch", f"/requests/{request_id}", json=payload)
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API patch_request id=%s", request_id)
    return None


async def list_proofs(request_id: Optional[int] = None) -> List[dict]:
    try:
        params = {"request_id": request_id} if request_id is not None else None
        r = await _request("get", "/proofs/", params=params)
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API list_proofs")
    return []


async def create_proof(payload: dict) -> Optional[dict]:
    try:
        r = await _request("post", "/proofs/", json=payload)
        if r.status_code in (200, 201):
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API create_proof")
    return None


async def decide_proof(proof_id: int, payload: dict) -> Optional[dict]:
    try:
        r = await _request("patch", f"/proofs/{proof_id}/decide", json=payload)
        if r.status_code == 200:
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API decide_proof id=%s", proof_id)
    return None
