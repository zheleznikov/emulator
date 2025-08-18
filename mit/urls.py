from django.urls import path
from .views import esims_snapshot_list

urlpatterns = [
    path('esims/snapshots/', esims_snapshot_list, name='esims-snapshot-list'),
]
