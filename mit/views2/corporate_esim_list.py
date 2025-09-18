# views.py
import time
import uuid
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils.http import urlencode
from rest_framework.decorators import api_view
from rest_framework.request import Request

# --- Константы для генерации данных (как в твоём примере snapshot) ---
BASE_IMSI = 260010191300000  # 260010191309999
BASE_ICCID = 8948010000038400000  # 8948010000038409999

MSISDN = "48890001002"
SMDP_SERVER = "smdp.io"
ACTIVATION_CODE = "K2-1QQM6T-AAAAAA"
BALANCE = 20.0

# Сколько всего eSIM «в мире» заглушки.
# Можно изменить тут или переопределить ?mock_total=
TOTAL_ESIMS_DEFAULT = 50

# Параметры пагинации как у DRF LimitOffsetPagination
DEFAULT_LIMIT = 10
MAX_LIMIT = 100


def _build_url(request: Request, **override_params) -> str:
    """
    Собрать абсолютный URL на основе текущего запроса, переопределив часть query-параметров.
    """
    params = request.GET.copy()
    for k, v in override_params.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = str(v)
    query = urlencode(params, doseq=True)
    base = request.build_absolute_uri(request.path)
    return f"{base}?{query}" if query else base


def _make_item(i: int, created_base: datetime) -> dict:
    """
    Сгенерировать один объект eSIM по требуемой схеме ответа.
    created_at — внутреннее поле для сортировки (в ответ не включаем).
    """
    imsi = str(BASE_IMSI + i)
    iccid = str(BASE_ICCID + i)

    activation_date = created_base + timedelta(days=i)
    last_balance_at = activation_date + timedelta(days=30)
    balance_last_synced = datetime.utcnow()
    comment = f"Auto-generated eSIM {i+1}" if i % 3 == 0 else ""

    was_active_at_least_once = True if (i % 2 == 0) else 0
    alias = f"ESIM-{i+1}-Григорьаева Алена" if (i % 2 == 0) else f"ESIM-{i}"


    item = {
        "id": str(uuid.uuid4()),
        "favourite": activation_date.isoformat() + "Z",
        "imsi": imsi,
        "alias": alias,
        "last_balance": f"{BALANCE}",
        "last_balance_at": last_balance_at.isoformat() + "Z",
        "is_active_now": (i % 2 == 0),
        "current_price": "10.5",
        "current_gb_estimated": "1.2",
        "current_network_name": "TestNet",
        "balance_last_synced": balance_last_synced.isoformat() + "Z",
        "smdp": SMDP_SERVER,
        "activation_code": f"{ACTIVATION_CODE}-{i}",
        "connection_string": iccid,  # для примера кладём ICCID
        "was_active_at_least_once": was_active_at_least_once,
        "corporate_user_email": f"user{i}@example.com",
        "corporate_comment": comment,
    }

    item["_created_at"] = activation_date
    return item


@api_view(["GET"])
def corporate_esims_list(request: Request):
    """
    Заглушка списка eSIM, совместимая с поведением оригинального ViewSet:
    - ?search=...
    - ?ordering=created_at|-created_at|alias|-alias|corporate_user_email|-corporate_user_email
    - ?limit=, ?offset=
    Возвращает count/next/previous/results.
    """
    # --- Объём данных для заглушки ---
    time.sleep(1.5)
    try:
        total_esims = int(request.GET.get("mock_total", TOTAL_ESIMS_DEFAULT))
    except ValueError:
        total_esims = TOTAL_ESIMS_DEFAULT

    # --- Генерация пула записей ---
    created_base = datetime(2025, 8, 16, 8, 22, 26)
    all_items = [_make_item(i, created_base) for i in range(total_esims)]

    # --- Поиск (как SearchFilter) ---
    # Оригинал: search по ["alias", "sim__imsi", "corporate_user_email", "corporate_comment"]
    # У нас поле imsi, поэтому ищем по: alias, imsi, corporate_user_email, corporate_comment
    q = (request.GET.get("search") or "").strip().lower()
    if q:
        def match(it: dict) -> bool:
            return (
                (it.get("alias") or "").lower().find(q) >= 0
                or (it.get("imsi") or "").lower().find(q) >= 0
                or (it.get("corporate_user_email") or "").lower().find(q) >= 0
                or (it.get("corporate_comment") or "").lower().find(q) >= 0
            )
        all_items = [it for it in all_items if match(it)]

    # --- Сортировка (как OrderingFilter) ---
    # Разрешённые поля
    allowed = {
        "created_at": "_created_at",
        "alias": "alias",
        "corporate_user_email": "corporate_user_email",
    }
    ordering_param = (request.GET.get("ordering") or "-created_at").strip()
    reverse = ordering_param.startswith("-")
    key_name = ordering_param.lstrip("-")

    sort_key = allowed.get(key_name, "_created_at")  # если невалидно — используем дефолт
    all_items.sort(key=lambda it: it.get(sort_key) or "", reverse=reverse)

    # --- Пагинация (LimitOffset) ---
    try:
        limit = int(request.GET.get("limit", DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))

    try:
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        offset = 0
    offset = max(0, offset)

    count = len(all_items)
    page = all_items[offset: offset + limit]

    # --- next/previous ---
    next_url = None
    prev_url = None

    if offset + limit < count:
        next_url = _build_url(request, offset=offset + limit, limit=limit)
    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_url = _build_url(request, offset=prev_offset, limit=limit)

    # --- Убираем служебные поля и отдаём ответ ---
    for it in page:
        it.pop("_created_at", None)

    return JsonResponse({
        "count": count,
        "next": next_url,
        "previous": prev_url,
        "results": page,
    })

@api_view(["PATCH"])
def corporate_esim_set_comment(request: Request, id: str):
    time.sleep(1.5)

    new_comment = request.data.get("corporate_comment")

    return JsonResponse(
        {
            "corporate_comment": new_comment,
        },
        status=200,
    )


