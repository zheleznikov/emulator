from datetime import datetime, timedelta
from typing import Iterator

import orjson
from django.http import StreamingHttpResponse, HttpResponseBadRequest
from rest_framework.decorators import api_view

# количество esim
COUNT = 5  # целевое - 100_000

BASE_IMSI = 260010191300000  # 260010191309999
BASE_ICCID = 8948010000038400000  # 8948010000038409999


MSISDN = "48890001002"
SMDP_SERVER = "smdp.io"
ACTIVATION_CODE = "K2-1QQM6T-AAAAAA"
BALANCE = 20.0

# Поднимаю на 8001 порту через pycharm
# Обратиться из постмана - http://127.0.0.1:8001/api/esims/snapshots/
#
# Чтобы обращаться локально из бэкенда из контейнера, добавил в локальный docker-compose в unisim-api extra_hosts,
#   unisim_api:
#    extra_hosts:
#      - "host.docker.internal:host-gateway"
@api_view(['GET'])
def esims_snapshot_list(_request):
    start_activation = datetime(2025, 8, 16, 8, 22, 26)

    mcc_mnc_pool = [
        (260, 1),   # PL
        (260, 2),   # PL
        (260, 6),   # PL
        (250, 99),  # RU
        (234, 15),  # UK
    ]

    dumps = orjson.dumps

    def make_row(i: int):
        imsi = str(BASE_IMSI + i)
        iccid = str(BASE_ICCID + i)

        activation_date = start_activation + timedelta(days=i)

        last_usage_date = activation_date + timedelta(
            days=30 + (i % 600),
            hours=(i % 24),
            minutes=(i * 7) % 60,
            seconds=(i * 13) % 60
        )

        mcc, mnc = mcc_mnc_pool[i % len(mcc_mnc_pool)]

        return {
            "ICCID": iccid,
            "IMSI": imsi,
            "MSISDN": MSISDN,
            "SMDP_SERVER": SMDP_SERVER,
            "ACTIVATION_CODE": ACTIVATION_CODE,
            "BALANCE": BALANCE,
            "ACTIVATION_DATE": activation_date.isoformat(timespec="seconds"),
            "LAST_USAGE_DATE": last_usage_date.isoformat(timespec="seconds"),
            "LAST_MCC": mcc,
            "LAST_MNC": mnc,
        }

    def make_dirty_row(i: int):
        imsi = str(BASE_IMSI + i)
        iccid = str(BASE_ICCID + i)

        return {
            "ICCID": iccid,
            "IMSI": imsi,
            "MSISDN": MSISDN,
            "SMDP_SERVER": SMDP_SERVER,
            "ACTIVATION_CODE": ACTIVATION_CODE,
            "BALANCE": BALANCE,
            "ACTIVATION_DATE": "Never",
            "LAST_USAGE_DATE": "Never",
            "LAST_MCC": "Empty",
            "LAST_MNC": "Empty",
        }

    def stream_json_object():
        yield b'{"esims_snapshot_list":['
        first = True
        for i in range(COUNT):
            if not first:
                yield b","
            else:
                first = False

            row = make_dirty_row(i) if (i % 5 == 0) else make_row(i)
            # row = make_row(i)
            yield dumps(row)
        yield b"]}"

    return StreamingHttpResponse(stream_json_object(), content_type="application/json")



MCC_MNC_INFO = [
    # (mcc, mnc, country, network)
    ("530", "1",   "New Zealand", "One New Zealand Group Limited"),
    ("262", "2",   "Germany",     "Vodafone GmbH"),
    ("260", "1",   "Poland",      "Orange Polska S.A."),
    ("234", "15",  "United Kingdom", "Vodafone UK"),
    ("208", "1",   "France",      "Orange France"),
]

CDR_USAGES_COUNT = 10


def _validate_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise



@api_view(["GET"])
def cdr_usages(request, date_str: str):
    """
    Пример: GET /b2b/cdr_usages/2025-06-07
    Вернёт JSON:
    {
      "usages": [...],
      "summary": {...},
      "meta": {...}      # rows и total_available = запрошенному количеству
    }
    """
    try:
        base_date = _validate_date(date_str)
    except ValueError:
        return HttpResponseBadRequest('Path param must be date in format YYYY-MM-DD')

    dumps = orjson.dumps

    def make_usage(i: int) -> dict:
        """
        Формируем одну запись usage.
        - Date — на базе date_str + небольшое смещение во времени
        - MCC/MNC, country, network — из пула
        - IMSI — BASE_IMSI + i
        - Bytes — строкой, как в примере
        - Charge — float
        """
        # Немного разнообразим время: 03:00:02 + i секунд (циклически)
        dt = base_date + timedelta(hours=3, seconds=i % 86400)
        date_fmt = dt.strftime("%Y-%m-%d %H:%M:%S")

        mcc, mnc, country, network = MCC_MNC_INFO[i % len(MCC_MNC_INFO)]

        imsi = str(BASE_IMSI + i)
        bytes_val = 41_944_087 + (i * 997)  # псевдо-рост, но не обязательно
        charge = 0.05896147178459168 * (1 + (i % 3) * 0.1)  # слегка варьируем

        return {
            "Date": date_fmt,
            "mcc": mcc,
            "mnc": mnc,
            "IMSI": imsi,
            "Bytes": str(bytes_val),  # именно строкой, как в примере
            "Charge": float(charge),
            "country": country,
            "network": network,
        }

    # summary — можно отдавать константой (как вы просили),
    # при желании легко посчитать реальные итоги.
    summary_obj = {
        "total_records": 1000,
        "total_bytes": 2056190.0,
        "total_kb": 2007.3320312,
        "total_mb": 19.2268867493,
        "total_gb": 1.976784069091,
        "total_charge": 29.5312405683912,
    }

    # meta — сделаем динамичными поля rows и total_available под запрошенный размер.
    meta_obj = {
        "rows": CDR_USAGES_COUNT,
        "total_available": CDR_USAGES_COUNT,
    }

    def stream_payload() -> Iterator[bytes]:
        yield b'{"usages":['
        first = True
        for i in range(CDR_USAGES_COUNT):
            if not first:
                yield b","
            first = False
            yield dumps(make_usage(i))
        yield b'],"summary":'
        yield dumps(summary_obj)
        yield b',"meta":'
        yield dumps(meta_obj)
        yield b"}"

    return StreamingHttpResponse(stream_payload(), content_type="application/json")
