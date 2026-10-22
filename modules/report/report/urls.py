from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path(
        "<str:report_name>/<str:report_format>/",
        views.report,
        name="report",
    ),
    path(
        "<str:report_name>/<str:report_format>/<str:alternate>/",
        views.report,
        name="report",
    ),
    path("reportbro/designer", views.reportbro_designer, name="reportbro_designer"),
    path(
        "reportbro/preview",
        csrf_exempt(views.reportbro_previewer),
        name="reportbro_previewer",
    ),
]
