from django.urls import path
from . import views

urlpatterns = [
    path('', views.process_csv, name='process_csv'),  # Atualize para usar a função correta
]
