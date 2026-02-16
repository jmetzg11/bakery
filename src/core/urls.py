from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('ingredients/', views.ingredients, name='ingredients'),
    path('orders/', views.orders, name='orders'),
    path('reports/', views.reports, name='reports'),
]
