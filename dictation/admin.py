from django.contrib import admin
from .models import DictationSession, DictationRecord, UserProgress

@admin.register(DictationSession)
class DictationSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'word_list', 'total_words', 'completed_words', 
                   'correct_count', 'accuracy_rate', 'is_completed', 'start_time', 'user']
    list_filter = ['is_completed', 'start_time', 'word_list', 'user']
    search_fields = ['session_name', 'word_list__name']
    readonly_fields = ['start_time', 'end_time', 'accuracy_rate', 'duration']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('session_name', 'word_list', 'is_completed', 'user')
        }),
        ('进度信息', {
            'fields': ('total_words', 'completed_words', 'correct_count', 'wrong_count')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time', 'duration'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DictationRecord)
class DictationRecordAdmin(admin.ModelAdmin):
    list_display = ['session', 'word', 'user_answer', 'is_correct', 'time_taken', 'created_at', 'learning_record']
    list_filter = ['is_correct', 'created_at', 'session']
    search_fields = ['session__session_name', 'word__word', 'user_answer']
    readonly_fields = ['created_at']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['word', 'total_attempts', 'correct_attempts', 'accuracy_rate', 
                   'mastery_level', 'last_practiced']
    list_filter = ['mastery_level', 'last_practiced']
    search_fields = ['word__word']
    readonly_fields = ['accuracy_rate']
    
    fieldsets = (
        ('单词信息', {
            'fields': ('word',)
        }),
        ('练习统计', {
            'fields': ('total_attempts', 'correct_attempts', 'accuracy_rate')
        }),
        ('掌握程度', {
            'fields': ('mastery_level', 'last_practiced')
        }),
    )
