from django.urls import path
from . import views

app_name = 'vocabulary'

urlpatterns = [
    path('', views.word_list, name='word_list'),
    path('word/<int:word_id>/', views.word_detail, name='word_detail'),
    path('list/<int:list_id>/', views.word_list_detail, name='word_list_detail'),
    path('api/add-word/', views.add_word, name='add_word'),
    path('api/create-list/', views.create_word_list, name='create_word_list'),
    path('api/add-word-to-list/', views.add_word_to_list, name='add_word_to_list'),
    path('api/import-words/', views.import_words, name='import_words'),
    path('api/word/<int:word_id>/', views.get_word, name='get_word'),
    path('api/word/<int:word_id>/update/', views.update_word, name='update_word'),
    path('api/word-list/<int:list_id>/remove-word/<int:word_id>/', views.remove_word_from_list, name='remove_word_from_list'),
    path('api/word-list/<int:list_id>/update/', views.update_word_list, name='update_word_list'),
    path('api/word-list/<int:list_id>/delete/', views.delete_word_list, name='delete_word_list'),
    path('api/word-list/batch-remove-words/', views.batch_remove_words, name='batch_remove_words'),
    
    # 复习计划相关URL
    path('review/', views.review_dashboard, name='review_dashboard'),
    path('review/create/', views.create_review_plan, name='create_review_plan'),
    path('review/word/<int:record_id>/', views.review_word, name='review_word'),
] 