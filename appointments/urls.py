from django.urls import path
from . import views
from .views import AppointmentListCreateAPIView, AppointmentSetLinkAPIView, \
 appointments_for_day_api

urlpatterns = [
    path('', views.week_view, name='week_view'),
    path('api/appointments/<int:year>/<int:month>/<int:day>/', appointments_for_day_api, name='appointments_for_day_api'),
    path('api/appointments/', AppointmentListCreateAPIView.as_view(), name='appointment-list-create'),
    path('api/appointments/<int:pk>/set-link/', AppointmentSetLinkAPIView.as_view(), name='appointment-set-link'),
]