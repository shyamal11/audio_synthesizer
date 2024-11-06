from django.urls import path
from .views import synthesize_speech , home_view # Replace with your actual import


urlpatterns = [
    path('', home_view, name='home'),
    path('synthesize/', synthesize_speech, name='synthesize_speech'),
]
