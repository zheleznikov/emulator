import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import renderers, permissions
from datetime import datetime


class CorporateAccountInfoStubView(APIView):
    """
    Заглушка для корпоративного аккаунта.

    GET /corporate_account/api/account_info/
    """

    renderer_classes = [renderers.JSONRenderer]
    def get(self, request):
        # --- тестовые данные ---
        time.sleep(3)
        data = {
            "id": 123,
            "email": "corporate@example.com",
            "balance": 1500.75,
            "date_joined": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
            "currency": "USD",
            "organization": "ООО «Корпоративные связи»",
            "phone": "+7 900 123-45-67",
            "contact": "Иван Иванов",
            "esim_count": 42,
            "total_balance": 3800.55,
        }
        return Response(data)
