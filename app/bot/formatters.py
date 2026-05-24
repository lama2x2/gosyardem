"""Форматирование карточек заявок и пруфов для Telegram."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.labels import proof_status_ru, request_status_ru

CITIZEN_ROLES = frozenset({"citizen"})


def users_by_id(users: List[dict]) -> Dict[int, dict]:
    return {u["id"]: u for u in users}


def types_by_id(types: List[dict]) -> Dict[int, dict]:
    return {t["id"]: t for t in types}


def type_label(type_id: Optional[int], types_map: Dict[int, dict]) -> str:
    if not type_id:
        return "Не указан"
    item = types_map.get(type_id)
    return item["name"] if item else "Не указан"


def user_label(user: Optional[dict]) -> str:
    if not user:
        return "—"
    if user.get("telegram_name"):
        return user["telegram_name"]
    return "—"


def format_request(
    req: dict,
    users_map: Dict[int, dict],
    types_map: Dict[int, dict],
    *,
    viewer_role: str,
) -> str:
    lines = [
        f"Заявка №{req['id']}",
        f"Статус: {request_status_ru(req['status'])}",
        f"Тип: {type_label(req.get('type_id'), types_map)}",
        f"Название: {req['title']}",
    ]
    if req.get("address"):
        lines.append(f"Адрес: {req['address']}")
    if req.get("description"):
        lines.append(f"Описание: {req['description']}")

    if viewer_role not in CITIZEN_ROLES:
        citizen = users_map.get(req.get("user_id") or 0)
        operator = users_map.get(req.get("assigned_operator_id") or 0)
        executor = users_map.get(req.get("assigned_executor_id") or 0)
        lines.append(f"Гражданин: {user_label(citizen)}")
        lines.append(f"Оператор: {user_label(operator)}")
        lines.append(f"Исполнитель: {user_label(executor)}")

    if req.get("rating"):
        lines.append(f"Оценка: {req['rating']}/5")
    if req.get("citizen_review"):
        lines.append(f"Отзыв: {req['citizen_review']}")
    return "\n".join(lines)


def format_proof(
    proof: dict,
    users_map: Dict[int, dict],
    *,
    viewer_role: str,
) -> str:
    lines = [
        f"Пруф №{proof['id']} к заявке №{proof['request_id']}",
        f"Статус: {proof_status_ru(proof['status'])}",
    ]
    if viewer_role not in CITIZEN_ROLES:
        executor = users_map.get(proof.get("executor_id") or 0)
        lines.append(f"Исполнитель: {user_label(executor)}")
    if proof.get("comment"):
        lines.append(f"Описание: {proof['comment']}")
    return "\n".join(lines)


def format_proof_notification_for_citizen(
    req_id: int,
    proof: dict,
    *,
    verdict_line: str,
) -> str:
    lines = [verdict_line, f"Заявка №{req_id}."]
    if proof.get("comment"):
        lines.append(f"\nОписание работы:\n{proof['comment']}")
    return "\n".join(lines)


def request_list_line(req: dict) -> str:
    return f"№{req['id']} — {req['title']} ({request_status_ru(req['status'])})"
