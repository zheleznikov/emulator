from django.urls import path

from .views import esims_snapshot_list, cdr_usages
from .views2.corp_account import CorporateAccountInfoStubView
from .views2.corporate_esim_list import corporate_esims_list
from .views2.corporate_esim_list import corporate_esim_set_comment
from .views2.order import OrderStubView

urlpatterns = [
    path('esims/snapshots/', esims_snapshot_list, name='esims-snapshot-list'),
    path("b2b/cdr_usages/<str:date_str>", cdr_usages, name="cdr_usages"),
    path("corporate_account/api/esims/", corporate_esims_list),
    path("corporate_account/api/account_info/", CorporateAccountInfoStubView.as_view()),
    path("corporate_account/api/esims/<uuid:id>/set_comment/", corporate_esim_set_comment),
    path("corporate_account/api/create-order/", OrderStubView.as_view()),

]
