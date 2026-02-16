from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('ingredients/', views.IngredientsView.as_view(), name='ingredients'),
    path('sales/', views.SalesView.as_view(), name='sales'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
]
