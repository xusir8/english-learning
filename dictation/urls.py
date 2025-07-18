from django.urls import path
from . import views

app_name = 'dictation'

urlpatterns = [
    path('', views.dictation_home, name='home'),
    path('start/<int:list_id>/', views.start_dictation, name='start_dictation'),
    path('session/<int:session_id>/', views.dictation_session, name='dictation_session'),
    path('session/<int:session_id>/submit/', views.submit_answer, name='submit_answer'),
    path('session/<int:session_id>/skip/', views.skip_word, name='skip_word'),
    path('result/<int:session_id>/', views.dictation_result, name='dictation_result'),
    path('progress/', views.progress_report, name='progress'),
] 