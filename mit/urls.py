from django.urls import path
from .views import esims_snapshot_list, cdr_usages

urlpatterns = [
    path('esims/snapshots/', esims_snapshot_list, name='esims-snapshot-list'),
    path("b2b/cdr_usages/<str:date_str>", cdr_usages, name="cdr_usages"),
]
