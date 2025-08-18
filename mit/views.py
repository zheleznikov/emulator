from datetime import datetime, timedelta

import orjson
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view

# количество esim
COUNT = 100  # целевое - 100_000

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
    start_activation = datetime(2025, 7, 14, 8, 22, 26)

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

    def stream_json_object():
        yield b'{"esims_snapshot_list":['
        first = True
        for i in range(COUNT):
            if not first:
                yield b","
            else:
                first = False
            yield dumps(make_row(i))
        yield b"]}"

    return StreamingHttpResponse(stream_json_object(), content_type="application/json")

