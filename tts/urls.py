from django.urls import path
from . import views

app_name = 'tts'
 
urlpatterns = [
    path('speak/', views.text_to_speech, name='text_to_speech'),
    path('voices/', views.get_voice_options, name='get_voice_options'),
] 