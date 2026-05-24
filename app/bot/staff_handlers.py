"""Обработчики для операторов и исполнителей + callback-кнопки."""

from __future__ import annotations

import logging
from typing import List, Optional

from telegram import CallbackQuery, Message, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from app.bot import api_client
from app.bot.profile import sync_profile
from app.bot.formatters import (
    format_proof,
    format_proof_notification_for_citizen,
    format_request,
    request_list_line,
    types_by_id,
    users_by_id,
)
from app.bot.keyboards import (
    executor_assign_keyboard,
    proof_review_keyboard,
    proof_view_back_keyboard,
    request_card_keyboard,
    request_list_keyboard,
    request_type_assign_keyboard,
)
from app.bot.notify import notify_user_id
from app.labels import proof_status_ru, request_status_ru

logger = logging.getLogger(__name__)

PROOF_PUBLIC_WARNING = (
    "⚠️ Пруф будет ПУБЛИЧНЫМ: его увидят оператор и гражданин, подавший заявку. "
    "Не указывайте личные данные, если не готовы ими поделиться.\n\n"
)


async def safe_send(
    message: Optional[Message],
    text: str,
    *,
    photo_file_id: Optional[str] = None,
    reply_markup=None,
) -> None:
    if not message:
        return
    try:
        if photo_file_id:
            await message.reply_photo(
                photo=photo_file_id,
                caption=text[:1024],
                reply_markup=reply_markup,
            )
        else:
            await message.reply_text(text, reply_markup=reply_markup)
    except TelegramError:
        logger.exception("Не удалось отправить сообщение")


async def safe_edit_or_send(query: CallbackQuery, text: str, reply_markup=None) -> None:
    if not query.message:
        return
    try:
        if query.message.photo:
            await query.message.edit_caption(caption=text[:1024], reply_markup=reply_markup)
        else:
            await query.edit_message_text(text, reply_markup=reply_markup)
    except TelegramError:
        await query.message.reply_text(text, reply_markup=reply_markup)


def filter_requests_for_user(me: dict, reqs: List[dict]) -> List[dict]:
    role = me["role"]
    if role == "citizen":
        return [r for r in reqs if r["user_id"] == me["id"]]
    if role == "superuser":
        return reqs
    if role == "operator":
        return [
            r
            for r in reqs
            if r.get("assigned_operator_id") == me["id"]
            or (r.get("assigned_operator_id") is None and r.get("status") == "created")
        ]
    if role == "executor":
        return [r for r in reqs if r.get("assigned_executor_id") == me["id"]]
    return []


async def send_request_list(message: Message, me: dict, context: ContextTypes.DEFAULT_TYPE) -> None:
    reqs = await api_client.list_requests()
    my = filter_requests_for_user(me, reqs)
    if not my:
        await safe_send(message, "У вас пока нет заявок.")
        return
    context.user_data["list_requests"] = [r["id"] for r in my[:15]]
    lines = [request_list_line(r) for r in my[:15]]
    hint = "Нажмите на заявку, чтобы открыть карточку с фото и действиями."
    await safe_send(
        message,
        "Ваши заявки:\n" + "\n".join(lines) + f"\n\n{hint}",
        reply_markup=request_list_keyboard(my[:15]),
    )


async def show_request_card(
    message: Message,
    me: dict,
    req: dict,
    *,
    edit_message: bool = False,
    query: Optional[CallbackQuery] = None,
) -> None:
    users = await api_client.list_users()
    types = await api_client.list_request_types()
    users_map = users_by_id(users)
    types_map = types_by_id(types)
    text = format_request(req, users_map, types_map, viewer_role=me["role"])
    proofs = await api_client.list_proofs(req["id"])
    kb = request_card_keyboard(me["role"], req, proof_count=len(proofs))

    photo_id = req.get("photo_file_id")
    if edit_message and query:
        if photo_id and not query.message.photo:
            await query.message.reply_photo(photo=photo_id, caption=text[:1024], reply_markup=kb)
        else:
            await safe_edit_or_send(query, text, reply_markup=kb)
    else:
        await safe_send(message, text, photo_file_id=photo_id, reply_markup=kb)


async def show_proofs_for_request(query: CallbackQuery, me: dict, request_id: int) -> None:
    proofs = await api_client.list_proofs(request_id)
    if not proofs:
        await query.answer("Пруфов пока нет.")
        return
    users = await api_client.list_users()
    users_map = users_by_id(users)
    can_review = me["role"] in ("operator", "superuser")
    await query.answer()
    for proof in proofs:
        text = format_proof(proof, users_map, viewer_role=me["role"])
        if can_review and proof["status"] == "pending":
            kb = proof_review_keyboard(proof["id"], request_id)
        else:
            kb = proof_view_back_keyboard(request_id)
        if query.message:
            await safe_send(
                query.message,
                text,
                photo_file_id=proof.get("file_ref"),
                reply_markup=kb,
            )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await sync_profile(update)
    data = query.data
    if data == "noop":
        await query.answer()
        return

    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await api_client.get_user_by_telegram_id(telegram_id)
    if not me:
        await query.answer("Пользователь не найден. /start")
        return

    if data == "list":
        await query.answer()
        if query.message:
            await send_request_list(query.message, me, context)
        return

    if data.startswith("r:"):
        request_id = int(data.split(":")[1])
        req = await api_client.get_request(request_id)
        if not req:
            await query.answer("Заявка не найдена.")
            return
        await query.answer()
        if query.message:
            await show_request_card(query.message, me, req, edit_message=True, query=query)
        return

    if data.startswith("picktype:"):
        request_id = int(data.split(":")[1])
        types = await api_client.list_request_types()
        if not types:
            await query.answer("Типы заявок не настроены. Запустите seed_request_types.")
            return
        await query.answer()
        await safe_edit_or_send(
            query,
            f"Заявка №{request_id}: выберите тип:",
            reply_markup=request_type_assign_keyboard(request_id, types),
        )
        return

    if data.startswith("sett:"):
        _, req_id_s, type_id_s = data.split(":")
        request_id, type_id = int(req_id_s), int(type_id_s)
        patch = {"type_id": type_id}
        existing = await api_client.get_request(request_id)
        if existing and not existing.get("assigned_operator_id"):
            patch["assigned_operator_id"] = me["id"]
        req = await api_client.patch_request(request_id, patch)
        if not req:
            await query.answer("Не удалось назначить тип.")
            return
        types = await api_client.list_request_types()
        type_name = next((t["name"] for t in types if t["id"] == type_id), str(type_id))
        await query.answer(f"Тип: {type_name}")
        if req.get("user_id"):
            await notify_user_id(
                req["user_id"],
                f"Заявке №{request_id} присвоен тип: {type_name}.",
                request_id=request_id,
            )
        if query.message:
            await show_request_card(query.message, me, req, query=query)
        return

    if data.startswith("pick:"):
        request_id = int(data.split(":")[1])
        executors = await api_client.list_users(role="executor")
        if not executors:
            await query.answer("Нет исполнителей в системе.")
            return
        await query.answer()
        await safe_edit_or_send(
            query,
            f"Заявка №{request_id}: выберите исполнителя:",
            reply_markup=executor_assign_keyboard(request_id, executors),
        )
        return

    if data.startswith("ae:"):
        _, req_id_s, exec_id_s = data.split(":")
        request_id, executor_id = int(req_id_s), int(exec_id_s)
        patch = {"assigned_executor_id": executor_id}
        existing = await api_client.get_request(request_id)
        if existing and not existing.get("assigned_operator_id"):
            patch["assigned_operator_id"] = me["id"]
        req = await api_client.patch_request(request_id, patch)
        if not req:
            await query.answer("Не удалось назначить.")
            return
        await query.answer("Исполнитель назначен.")
        await notify_user_id(
            executor_id,
            f"Вам назначена заявка №{request_id}: {req['title']}.",
            req.get("photo_file_id"),
            request_id=request_id,
        )
        await notify_user_id(
            req["user_id"],
            f"Заявка №{request_id} принята в работу. Статус: {request_status_ru(req['status'])}.",
            request_id=request_id,
        )
        if query.message:
            await show_request_card(query.message, me, req, query=query)
        return

    if data.startswith("viewp:") or data.startswith("proofs:"):
        request_id = int(data.split(":")[1])
        await show_proofs_for_request(query, me, request_id)
        return

    if data.startswith("ps:") or data.startswith("pr:"):
        proof_id = int(data.split(":")[1])
        approved = data.startswith("ps:")
        proof = None
        for p in await api_client.list_proofs():
            if p["id"] == proof_id:
                proof = p
                break
        if not proof:
            await query.answer("Пруф не найден.")
            return
        result = await api_client.decide_proof(
            proof_id,
            {
                "operator_id": me["id"],
                "status": "approved" if approved else "rejected",
            },
        )
        if not result:
            await query.answer("Не удалось обновить пруф.")
            return
        req = await api_client.get_request(proof["request_id"])
        verdict = "подтверждён" if approved else "отклонён"
        await query.answer(f"Пруф {verdict}.")
        if req:
            verdict_line = (
                f"Работа по заявке №{req['id']} подтверждена. Статус: {request_status_ru(req['status'])}."
                if approved
                else f"Материалы по заявке №{req['id']} не приняты. Статус: {request_status_ru(req['status'])}."
            )
            citizen_text = format_proof_notification_for_citizen(
                req["id"],
                proof,
                verdict_line=verdict_line,
            )
            await notify_user_id(
                req["user_id"],
                citizen_text,
                proof.get("file_ref"),
                request_id=req["id"],
            )
            if req.get("assigned_executor_id"):
                await notify_user_id(
                    req["assigned_executor_id"],
                    f"Ваш пруф по заявке №{req['id']} {verdict} ({proof_status_ru(result['status'])}).",
                    request_id=req["id"],
                )
        if query.message:
            await safe_send(
                query.message,
                f"Пруф №{proof_id} {verdict}. Заявка №{proof['request_id']}: "
                f"{request_status_ru(req['status']) if req else '—'}.",
            )
        return

    if data.startswith("st:"):
        _, req_id_s, status = data.split(":")
        request_id = int(req_id_s)
        req = await api_client.patch_request(request_id, {"status": status})
        if not req:
            await query.answer("Не удалось сменить статус.")
            return
        await query.answer("Статус обновлён.")
        await notify_user_id(
            req["user_id"],
            f"Заявка №{request_id}: {request_status_ru(req['status'])}.",
            request_id=request_id,
        )
        if req.get("assigned_operator_id"):
            await notify_user_id(
                req["assigned_operator_id"],
                f"Заявка №{request_id} — {request_status_ru(req['status'])}.",
                request_id=request_id,
            )
        if query.message:
            await show_request_card(query.message, me, req, query=query)
        return

    if data.startswith("pf:"):
        request_id = int(data.split(":")[1])
        context.user_data["uploading_proof"] = {"request_id": request_id, "step": "comment"}
        await query.answer()
        await safe_edit_or_send(
            query,
            PROOF_PUBLIC_WARNING
            + f"Заявка №{request_id}.\n"
            "Шаг 1 из 2. Опишите выполненную работу текстом (обязательно).",
        )
        return

    if data.startswith("rt:"):
        _, req_id_s, rating_s = data.split(":")
        request_id, rating = int(req_id_s), int(rating_s)
        req = await api_client.patch_request(request_id, {"rating": rating})
        if not req:
            await query.answer("Не удалось сохранить оценку.")
            return
        context.user_data["rating_request"] = {"request_id": request_id, "step": "review"}
        await query.answer("Спасибо!")
        await safe_edit_or_send(
            query,
            f"Оценка {rating}/5 сохранена. Напишите отзыв текстом или /skip.",
        )
        return

    await query.answer()


async def handle_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    data = context.user_data.get("uploading_proof")
    if not data or data.get("step") != "photo":
        return False
    if not update.message or not update.message.photo:
        return True
    data["file_ref"] = update.message.photo[-1].file_id
    await finalize_proof(update, context)
    return True


async def handle_proof_comment_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    data = context.user_data.get("uploading_proof")
    if not data or data.get("step") != "comment":
        return False
    if not update.message or not update.message.text:
        return True
    comment = update.message.text.strip()
    if not comment:
        await safe_send(update.message, "Текст обязателен. Опишите выполненную работу.")
        return True
    data["comment"] = comment
    data["step"] = "photo"
    await safe_send(
        update.message,
        "Шаг 2 из 2. Отправьте фото выполненной работы или /skip, если фото не нужно.",
    )
    return True


async def skip_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.get("uploading_proof")
    if not data:
        return
    if data.get("step") == "photo":
        await finalize_proof(update, context)
        return
    if data.get("step") == "comment":
        await safe_send(
            update.message,
            "Текст описания обязателен. Введите, что было сделано по заявке.",
        )
        return


async def finalize_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.pop("uploading_proof", None)
    if not data or not data.get("comment"):
        await safe_send(
            update.message,
            "Пруф не сохранён: нужен текст описания. /list → заявка → Прикрепить пруф.",
        )
        return
    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await api_client.get_user_by_telegram_id(telegram_id)
    if not me or me["role"] != "executor":
        await safe_send(update.message, "Только исполнитель может загружать пруфы.")
        return
    payload = {
        "request_id": data["request_id"],
        "executor_id": me["id"],
        "comment": data["comment"],
    }
    if data.get("file_ref"):
        payload["file_ref"] = data["file_ref"]
    proof = await api_client.create_proof(payload)
    if not proof:
        await safe_send(update.message, "Не удалось сохранить пруф.")
        return
    req = await api_client.get_request(data["request_id"])
    await safe_send(update.message, f"Пруф №{proof['id']} отправлен на проверку.")
    if req and req.get("assigned_operator_id"):
        await notify_user_id(
            req["assigned_operator_id"],
            f"Новый пруф по заявке №{req['id']}.",
            proof.get("file_ref"),
            request_id=req["id"],
        )


async def handle_rating_review_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    data = context.user_data.get("rating_request")
    if not data or data.get("step") != "review":
        return False
    if not update.message or not update.message.text:
        return True
    request_id = data["request_id"]
    req = await api_client.patch_request(
        request_id,
        {"citizen_review": update.message.text, "citizen_confirmed": True},
    )
    context.user_data.pop("rating_request", None)
    if req:
        await safe_send(update.message, f"Спасибо за отзыв по заявке №{request_id}!")
    else:
        await safe_send(update.message, "Не удалось сохранить отзыв.")
    return True


async def skip_rating_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.get("rating_request")
    if not data or data.get("step") != "review":
        return
    request_id = data["request_id"]
    await api_client.patch_request(request_id, {"citizen_confirmed": True})
    context.user_data.pop("rating_request", None)
    await safe_send(update.message, f"Заявка №{request_id}: оценка сохранена без отзыва.")


def role_help(role: str) -> str:
    base = (
        "Общие команды:\n"
        "/start — начать\n"
        "/list — заявки (кнопки + фото в карточке)\n"
        "/help — справка\n"
    )
    if role == "citizen":
        return (
            base
            + "/new — создать заявку\n"
            "/skip — пропустить фото или отзыв\n"
        )
    if role == "operator":
        return (
            base
            + "Оператор: назначить тип и исполнителя, проверить пруфы (фото + кнопки).\n"
        )
    if role == "executor":
        return (
            base
            + "Исполнитель: «В работу», «Прикрепить пруф» — сначала текст (обязательно), "
            "затем фото (/skip). Пруф публичный: его видят оператор и гражданин.\n"
        )
    if role == "superuser":
        return base + "Суперпользователь: видит все заявки, как оператор.\n"
    return base
