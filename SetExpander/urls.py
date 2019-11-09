from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('search/', views.search_result, name='search_result'),
    path('about/', views.about, name='about')
]