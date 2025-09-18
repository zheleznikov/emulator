import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import renderers, permissions, response, status
from datetime import datetime



class OrderStubView(APIView):

    renderer_classes = [renderers.JSONRenderer]
    def post(self, request):
        # --- тестовые данные ---
        time.sleep(3)
        return response.Response(
            status=status.HTTP_201_CREATED, data=None
        )