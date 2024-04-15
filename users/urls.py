from django.urls import path
from .views import SignUpView, ShowCodeView, LoginView, GrantAccessView

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),
    path('grant-access/', GrantAccessView.as_view(), name='grant_access'),
]
