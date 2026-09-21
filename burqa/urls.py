from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from hr_budget.views import (
    CustomLoginView,
    dashboard_view,
    employees_view,
    budget_view,
    simulator_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', dashboard_view, name='dashboard'),
    path('employees/', employees_view, name='employees'),
    path('budget/', budget_view, name='budget'),
    path('simulator/', simulator_view, name='simulator'),
]
