from django.contrib import admin
from .models import Word, WordList, WordListWord

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['word', 'phonetic', 'translation', 'difficulty_level', 'is_active', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['word', 'translation']
    list_editable = ['is_active', 'difficulty_level']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('word', 'phonetic', 'translation', 'example_sentence')
        }),
        ('分类信息', {
            'fields': ('difficulty_level', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WordList)
class WordListAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'word_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def word_count(self, obj):
        return obj.words.count()
    word_count.short_description = '单词数量'

@admin.register(WordListWord)
class WordListWordAdmin(admin.ModelAdmin):
    list_display = ['word_list', 'word', 'order', 'added_at']
    list_filter = ['word_list', 'added_at']
    search_fields = ['word_list__name', 'word__word']
    list_editable = ['order']
