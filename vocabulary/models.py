from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Word(models.Model):
    """单词模型"""
    word = models.CharField('单词', max_length=100)
    phonetic = models.CharField('音标', max_length=100, blank=True)
    translation = models.TextField('中文释义')
    example_sentence = models.TextField('例句', blank=True)
    difficulty_level = models.IntegerField('难度等级', choices=[
        (1, '简单'),
        (2, '中等'),
        (3, '困难'),
    ], default=1)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '单词'
        verbose_name_plural = '单词'
        ordering = ['word']
    
    def __str__(self):
        return self.word

class WordList(models.Model):
    """单词列表模型"""
    name = models.CharField('列表名称', max_length=200)
    description = models.TextField('描述', blank=True)
    words = models.ManyToManyField(Word, verbose_name='单词', through='WordListWord')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '单词列表'
        verbose_name_plural = '单词列表'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class WordListWord(models.Model):
    """单词列表关联模型"""
    word_list = models.ForeignKey(WordList, on_delete=models.CASCADE, verbose_name='单词列表')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, verbose_name='单词')
    order = models.IntegerField('排序', default=0)
    added_at = models.DateTimeField('添加时间', default=timezone.now)
    
    class Meta:
        verbose_name = '单词列表项'
        verbose_name_plural = '单词列表项'
        ordering = ['order']
        unique_together = ['word_list', 'word']
    
    def __str__(self):
        return f"{self.word_list.name} - {self.word.word}"

class WordLearningRecord(models.Model):
    """单词学习记录"""
    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_learn_date = models.DateTimeField(auto_now_add=True)
    last_review_date = models.DateTimeField(auto_now=True)
    review_count = models.IntegerField(default=0)
    mastery_level = models.IntegerField(default=0)  # 0-100表示掌握程度
    next_review_date = models.DateTimeField()
    
    class Meta:
        unique_together = ['word', 'user']
        
    def calculate_next_review(self):
        """基于艾宾浩斯遗忘曲线计算下次复习时间"""
        intervals = [1, 2, 4, 7, 15, 30, 60, 90]  # 复习间隔(天)
        if self.review_count >= len(intervals):
            days = intervals[-1]
        else:
            days = intervals[self.review_count]
        self.next_review_date = timezone.now() + timezone.timedelta(days=days)
        
    def update_mastery(self, review_result):
        """更新掌握程度"""
        if review_result:  # 复习正确
            self.mastery_level = min(100, self.mastery_level + 10)
        else:  # 复习错误
            self.mastery_level = max(0, self.mastery_level - 20)
        self.review_count += 1
        self.calculate_next_review()
        self.save()

class ReviewPlan(models.Model):
    """复习计划"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word_list = models.ForeignKey('WordList', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    PLAN_TYPES = (
        ('NEW', '新学习'),
        ('REVIEW', '复习计划'),
    )
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPES)
    
    def generate_review_schedule(self):
        """生成复习计划"""
        records = WordLearningRecord.objects.filter(
            user=self.user,
            word__wordlistword__word_list=self.word_list
        )
        
        # 按照下次复习时间排序
        return records.order_by('next_review_date')
    
    def get_today_words(self):
        """获取今天需要复习的单词"""
        today = timezone.now().date()
        records = self.generate_review_schedule()
        return records.filter(next_review_date__date=today)
