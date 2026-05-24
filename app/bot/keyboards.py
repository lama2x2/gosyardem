"""Inline-клавиатуры бота."""

from __future__ import annotations

from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.formatters import user_label


def request_list_keyboard(requests: List[dict], prefix: str = "r") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"№{r['id']} — {r['title'][:40]}", callback_data=f"{prefix}:{r['id']}")]
        for r in requests[:15]
    ]
    return InlineKeyboardMarkup(rows or [[InlineKeyboardButton("Нет заявок", callback_data="noop")]])


def request_type_assign_keyboard(request_id: int, types: List[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(t["name"][:40], callback_data=f"sett:{request_id}:{t['id']}")]
        for t in types[:20]
    ]
    rows.append([InlineKeyboardButton("« Назад", callback_data=f"r:{request_id}")])
    return InlineKeyboardMarkup(rows)


def executor_assign_keyboard(request_id: int, executors: List[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                user_label(e),
                callback_data=f"ae:{request_id}:{e['id']}",
            )
        ]
        for e in executors[:20]
    ]
    rows.append([InlineKeyboardButton("« Назад", callback_data=f"r:{request_id}")])
    return InlineKeyboardMarkup(rows)


def open_request_alert_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"Открыть заявку №{request_id}", callback_data=f"r:{request_id}")]]
    )


def proof_view_back_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("« К заявке", callback_data=f"r:{request_id}")]])


def proof_review_keyboard(proof_id: int, request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Подтвердить", callback_data=f"ps:{proof_id}"),
                InlineKeyboardButton("Отклонить", callback_data=f"pr:{proof_id}"),
            ],
            [InlineKeyboardButton("« К заявке", callback_data=f"r:{request_id}")],
        ]
    )


def _proof_button_row(request_id: int, proof_count: int) -> List[InlineKeyboardButton]:
    if proof_count > 1:
        label = f"Пруфы ({proof_count})"
    else:
        label = "Пруф"
    return [InlineKeyboardButton(label, callback_data=f"viewp:{request_id}")]


def request_card_keyboard(
    role: str,
    req: dict,
    *,
    proof_count: int = 0,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки заявки: ролевые действия + просмотр пруфа для всех."""
    rows: List[List[InlineKeyboardButton]] = []

    if role in ("operator", "superuser"):
        type_btn = "Изменить тип" if req.get("type_id") else "Назначить тип"
        rows.append([InlineKeyboardButton(type_btn, callback_data=f"picktype:{req['id']}")])
        if not req.get("assigned_executor_id"):
            rows.append(
                [InlineKeyboardButton("Назначить исполнителя", callback_data=f"pick:{req['id']}")]
            )
    elif role == "executor":
        status = req.get("status")
        if status == "created" and req.get("assigned_executor_id"):
            rows.append([InlineKeyboardButton("В работу", callback_data=f"st:{req['id']}:in_progress")])
        if status in ("created", "in_progress"):
            rows.append([InlineKeyboardButton("Прикрепить пруф", callback_data=f"pf:{req['id']}")])
    elif role == "citizen" and req.get("status") == "completed" and not req.get("rating"):
        rows.append(
            [
                InlineKeyboardButton(str(n), callback_data=f"rt:{req['id']}:{n}")
                for n in range(1, 6)
            ]
        )

    rows.append(_proof_button_row(req["id"], proof_count))
    rows.append([InlineKeyboardButton("« К списку", callback_data="list")])
    return InlineKeyboardMarkup(rows)
