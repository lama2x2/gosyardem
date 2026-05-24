"""Русские подписи для значений enum (отображение в боте и UI)."""

REQUEST_STATUS_RU = {
    "created": "Создана",
    "in_progress": "В работе",
    "proof_under_review": "На проверке пруфов",
    "completed": "Выполнена",
    "rejected": "Отклонена",
}

PROOF_STATUS_RU = {
    "pending": "На проверке",
    "approved": "Подтверждён",
    "rejected": "Отклонён",
}


def request_status_ru(status: str) -> str:
    return REQUEST_STATUS_RU.get(status, status)


def proof_status_ru(status: str) -> str:
    return PROOF_STATUS_RU.get(status, status)
