from django.contrib import admin
from django.urls import include, path

from hub_core.views import workbench_view

urlpatterns = [
    path("", workbench_view, name="root_workbench"),
    path("admin/", admin.site.urls),
    path("api/vnxbox/", include("hub_core.urls")),
]