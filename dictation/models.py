from django.db import models
from django.utils import timezone
from vocabulary.models import Word, WordList, WordLearningRecord
from django.contrib.auth.models import User

class DictationSession(models.Model):
    """听写会话模型"""
    word_list = models.ForeignKey(WordList, on_delete=models.CASCADE, verbose_name='单词列表')
    session_name = models.CharField('会话名称', max_length=200)
    total_words = models.IntegerField('总单词数', default=0)
    completed_words = models.IntegerField('已完成单词数', default=0)
    correct_count = models.IntegerField('正确数量', default=0)
    wrong_count = models.IntegerField('错误数量', default=0)
    start_time = models.DateTimeField('开始时间', default=timezone.now)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    is_completed = models.BooleanField('是否完成', default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', null=True)
    skipped_words = models.TextField('跳过的单词ID列表', blank=True, default='')
    
    class Meta:
        verbose_name = '听写会话'
        verbose_name_plural = '听写会话'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.session_name} - {self.word_list.name}"
    
    @property
    def accuracy_rate(self):
        """准确率"""
        if self.total_words == 0:
            return 0
        return round((self.correct_count / self.total_words) * 100, 2)
    
    @property
    def duration(self):
        """持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time

class DictationRecord(models.Model):
    """听写记录模型"""
    session = models.ForeignKey(DictationSession, on_delete=models.CASCADE, verbose_name='听写会话')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, verbose_name='单词')
    user_answer = models.CharField('用户答案', max_length=100)
    is_correct = models.BooleanField('是否正确', default=False)
    time_taken = models.IntegerField('用时(秒)', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    learning_record = models.ForeignKey(WordLearningRecord, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='学习记录')
    
    class Meta:
        verbose_name = '听写记录'
        verbose_name_plural = '听写记录'
    
    def __str__(self):
        return f"{self.word.word} - {'正确' if self.is_correct else '错误'}"
    
    def save(self, *args, **kwargs):
        """保存时更新学习记录"""
        super().save(*args, **kwargs)
        
        # 如果没有关联的学习记录且会话有用户，则创建或更新学习记录
        if not self.learning_record and self.session.user:
            # 尝试查找现有学习记录
            learning_record, created = WordLearningRecord.objects.get_or_create(
                word=self.word,
                user=self.session.user,
                defaults={
                    'next_review_date': timezone.now()
                }
            )
            
            # 更新学习记录
            learning_record.update_mastery(self.is_correct)
            
            # 关联学习记录
            self.learning_record = learning_record
            super().save(update_fields=['learning_record'])

class UserProgress(models.Model):
    """用户进度模型"""
    word = models.ForeignKey(Word, on_delete=models.CASCADE, verbose_name='单词')
    total_attempts = models.IntegerField('总尝试次数', default=0)
    correct_attempts = models.IntegerField('正确次数', default=0)
    last_practiced = models.DateTimeField('最后练习时间', default=timezone.now)
    mastery_level = models.IntegerField('掌握程度', default=0)  # 0-4
    
    class Meta:
        verbose_name = '用户进度'
        verbose_name_plural = '用户进度'
    
    def __str__(self):
        return f"{self.word.word} - {self.mastery_level}"
    
    @property
    def accuracy_rate(self):
        """准确率"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_attempts / self.total_attempts) * 100, 2)
