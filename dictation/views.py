from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from vocabulary.models import Word, WordList, WordLearningRecord, ReviewPlan
from .models import DictationSession, DictationRecord, UserProgress
import json
import random

def dictation_home(request):
    """听写首页"""
    word_lists = WordList.objects.all()
    
    # 获取当前用户的最近会话
    if request.user.is_authenticated:
        recent_sessions = DictationSession.objects.filter(
            user=request.user, 
            is_completed=True
        ).order_by('-end_time')[:5]
    else:
        recent_sessions = DictationSession.objects.filter(
            is_completed=True
        ).order_by('-end_time')[:5]
    
    context = {
        'word_lists': word_lists,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'dictation/home.html', context)

def start_dictation(request, list_id):
    """开始听写"""
    word_list = get_object_or_404(WordList, id=list_id)
    words = word_list.words.filter(is_active=True).order_by('wordlistword__order')
    
    if not words.exists():
        messages.error(request, f'词书"{word_list.name}"为空，请先添加单词后再开始听写。')
        return redirect('dictation:home')
    
    # 创建听写会话
    session = DictationSession.objects.create(
        word_list=word_list,
        user=request.user if request.user.is_authenticated else None,
        session_name=f"{word_list.name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        total_words=words.count()
    )
    
    # 重定向到会话页面
    return redirect('dictation:dictation_session', session_id=session.id)

def dictation_session(request, session_id):
    """听写会话页面"""
    session = get_object_or_404(DictationSession, id=session_id)
    
    # 确保用户只能访问自己的会话
    if session.user and session.user != request.user and request.user.is_authenticated:
        messages.error(request, "您无权访问此听写会话")
        return redirect('dictation:home')
    
    words = session.word_list.words.filter(is_active=True).order_by('wordlistword__order')
    
    # 获取当前进度 - 只计算正确回答的单词
    completed_words = DictationRecord.objects.filter(session=session, is_correct=True).values_list('word_id', flat=True)
    
    # 检查是否有上一次答错的单词
    last_incorrect = DictationRecord.objects.filter(
        session=session, 
        is_correct=False
    ).order_by('-created_at').first()
    
    # 解析跳过的单词ID列表
    skipped_word_ids = []
    if session.skipped_words:
        skipped_word_ids = [int(id) for id in session.skipped_words.strip(',').split(',') if id]
    
    # 决定当前要学习的单词
    if last_incorrect and last_incorrect.word_id not in completed_words:
        # 如果有答错的单词且尚未正确回答，则继续练习该单词
        current_word = last_incorrect.word
    else:
        # 否则获取剩余单词中的第一个
        remaining_words = words.exclude(id__in=completed_words)
        
        if not remaining_words.exists():
            # 如果所有常规单词都已完成，检查是否有跳过的单词
            if skipped_word_ids:
                # 获取第一个跳过的单词
                skipped_word_id = skipped_word_ids[0]
                current_word = get_object_or_404(Word, id=skipped_word_id)
                
                # 从跳过列表中移除这个单词
                skipped_word_ids.pop(0)
                session.skipped_words = ','.join(map(str, skipped_word_ids)) + ',' if skipped_word_ids else ''
                session.save(update_fields=['skipped_words'])
            else:
                # 所有单词都已正确完成
                session.is_completed = True
                session.end_time = timezone.now()
                session.save()
                
                context = {
                    'session': session,
                    'completed': True,
                }
                return render(request, 'dictation/result.html', context)
        else:
            current_word = remaining_words.first()
    
    # 获取该单词的学习记录
    learning_record = None
    if request.user.is_authenticated:
        learning_record, created = WordLearningRecord.objects.get_or_create(
            word=current_word,
            user=request.user,
            defaults={'next_review_date': timezone.now()}
        )
    
    # 计算进度百分比 - 只计算正确完成的单词
    total_words = words.count()
    completed_count = len(completed_words)
    percentage = round((completed_count / total_words) * 100, 1) if total_words > 0 else 0
    
    context = {
        'session': session,
        'current_word': current_word,
        'learning_record': learning_record,
        'progress': {
            'completed': completed_count,
            'total': total_words,
            'percentage': percentage
        },
        'remaining_skipped': len(skipped_word_ids)
    }
    return render(request, 'dictation/dictation.html', context)

@csrf_exempt
def submit_answer(request, session_id):
    """提交听写答案"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session = get_object_or_404(DictationSession, id=session_id)
            
            # 确保用户只能提交自己的会话答案
            if session.user and session.user != request.user and request.user.is_authenticated:
                return JsonResponse({'success': False, 'message': '您无权提交此听写会话的答案'})
            
            word = get_object_or_404(Word, id=data['word_id'])
            user_answer = data['answer'].strip().lower()
            time_taken = data.get('time_taken', 0)
            
            # 检查答案是否正确（忽略大小写和空格）
            is_correct = user_answer == word.word.lower()
            
            # 创建听写记录
            record = DictationRecord.objects.create(
                session=session,
                word=word,
                user_answer=user_answer,
                is_correct=is_correct,
                time_taken=time_taken
            )
            
            # 更新会话统计 - 只有正确时才增加完成单词计数
            if is_correct:
                session.completed_words += 1
                session.correct_count += 1
            else:
                session.wrong_count += 1
            session.save()
            
            # 更新用户进度
            progress, created = UserProgress.objects.get_or_create(word=word)
            progress.total_attempts += 1
            if is_correct:
                progress.correct_attempts += 1
            progress.last_practiced = timezone.now()
            
            # 根据准确率更新掌握程度
            accuracy = progress.accuracy_rate
            if accuracy >= 90:
                progress.mastery_level = 4
            elif accuracy >= 80:
                progress.mastery_level = 3
            elif accuracy >= 60:
                progress.mastery_level = 2
            elif accuracy >= 30:
                progress.mastery_level = 1
            else:
                progress.mastery_level = 0
            progress.save()
            
            # 获取或创建学习记录
            if request.user.is_authenticated:
                learning_record, created = WordLearningRecord.objects.get_or_create(
                    word=word,
                    user=request.user,
                    defaults={'next_review_date': timezone.now()}
                )
                
                # 更新学习记录
                learning_record.update_mastery(is_correct)
                
                # 关联学习记录到听写记录
                record.learning_record = learning_record
                record.save(update_fields=['learning_record'])
            
            return JsonResponse({
                'success': True,
                'is_correct': is_correct,
                'correct_word': word.word,
                'next_url': f'/dictation/session/{session_id}/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

@csrf_exempt
def skip_word(request, session_id):
    """跳过当前单词，将其放到学习列表的最后"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session = get_object_or_404(DictationSession, id=session_id)
            
            # 确保用户只能操作自己的会话
            if session.user and session.user != request.user and request.user.is_authenticated:
                return JsonResponse({'success': False, 'message': '您无权操作此听写会话'})
            
            word = get_object_or_404(Word, id=data['word_id'])
            
            # 创建一个错误记录，以便在后续查询中能够找到这个单词
            record = DictationRecord.objects.create(
                session=session,
                word=word,
                user_answer='[已跳过]',
                is_correct=False,
                time_taken=0
            )
            
            # 更新会话统计
            session.wrong_count += 1
            session.save()
            
            # 获取或创建学习记录
            if request.user.is_authenticated:
                learning_record, created = WordLearningRecord.objects.get_or_create(
                    word=word,
                    user=request.user,
                    defaults={'next_review_date': timezone.now()}
                )
                
                # 更新学习记录 - 跳过不影响掌握程度
                record.learning_record = learning_record
                record.save(update_fields=['learning_record'])
            
            # 创建一个特殊标记，表示这个单词被跳过，需要放到列表末尾
            session.skipped_words = session.skipped_words + str(word.id) + ',' if hasattr(session, 'skipped_words') else str(word.id) + ','
            session.save(update_fields=['skipped_words'])
            
            return JsonResponse({
                'success': True,
                'message': '单词已跳过，将在学完其他单词后再次出现'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

def dictation_result(request, session_id):
    """听写结果页面"""
    session = get_object_or_404(DictationSession, id=session_id)
    
    # 确保用户只能查看自己的会话结果
    if session.user and session.user != request.user and request.user.is_authenticated:
        messages.error(request, "您无权查看此听写会话的结果")
        return redirect('dictation:home')
    
    # 获取所有记录，包括错误和正确的
    records = DictationRecord.objects.filter(session=session).order_by('created_at')
    
    # 获取正确回答的单词ID列表
    correct_word_ids = records.filter(is_correct=True).values_list('word_id', flat=True).distinct()
    
    # 计算总体准确率 - 基于唯一单词的正确率
    total_unique_words = session.word_list.words.count()
    correct_unique_words = len(correct_word_ids)
    
    accuracy_rate = 0
    if total_unique_words > 0:
        accuracy_rate = round((correct_unique_words / total_unique_words) * 100, 1)
    
    # 按难度统计
    difficulty_stats = {}
    
    # 获取每个单词的最后一次正确记录
    word_ids_dict = {}
    for record in records.filter(is_correct=True):
        word_ids_dict[record.word_id] = record
    
    # 使用最后一次正确记录进行统计
    for record in word_ids_dict.values():
        level = record.word.difficulty_level
        if level not in difficulty_stats:
            difficulty_stats[level] = {'total': 0, 'correct': 0}
        difficulty_stats[level]['total'] += 1
        difficulty_stats[level]['correct'] += 1
    
    # 计算每个难度的正确率
    for level in difficulty_stats:
        stats = difficulty_stats[level]
        if stats['total'] > 0:
            stats['accuracy_rate'] = round((stats['correct'] / stats['total']) * 100, 1)
        else:
            stats['accuracy_rate'] = 0.0
    
    context = {
        'session': session,
        'records': records,
        'accuracy_rate': accuracy_rate,
        'difficulty_stats': difficulty_stats,
        'total_attempts': records.count(),
        'correct_unique_words': correct_unique_words,
        'total_unique_words': total_unique_words
    }
    return render(request, 'dictation/result.html', context)

@login_required
def progress_report(request):
    """进度报告"""
    # 获取用户的学习记录
    learning_records = WordLearningRecord.objects.filter(user=request.user)
    
    # 按掌握程度分组
    mastery_groups = {
        '已掌握': learning_records.filter(mastery_level__gte=80).count(),
        '学习中': learning_records.filter(mastery_level__lt=80, mastery_level__gte=40).count(),
        '需加强': learning_records.filter(mastery_level__lt=40).count()
    }
    
    # 预处理图表数据
    mastery_chart_data = json.dumps([
        {"value": mastery_groups['已掌握'], "name": "已掌握", "color": "#10B981"},
        {"value": mastery_groups['学习中'], "name": "学习中", "color": "#3B82F6"},
        {"value": mastery_groups['需加强'], "name": "需加强", "color": "#EF4444"}
    ])
    
    # 获取今日需要复习的单词
    today = timezone.now().date()
    today_reviews = learning_records.filter(next_review_date__date=today)
    
    # 获取活跃的复习计划
    active_plans = ReviewPlan.objects.filter(user=request.user, is_active=True)
    
    # 听写记录统计
    dictation_records = DictationRecord.objects.filter(
        session__user=request.user,
        learning_record__isnull=False
    )
    
    # 按日期统计听写数据
    date_stats = {}
    for record in dictation_records:
        date_key = record.created_at.date()
        if date_key not in date_stats:
            date_stats[date_key] = {'total': 0, 'correct': 0}
        date_stats[date_key]['total'] += 1
        if record.is_correct:
            date_stats[date_key]['correct'] += 1
    
    # 转换为图表数据格式
    chart_data = {
        'dates': [],
        'accuracy': [],
        'count': []
    }
    
    for date in sorted(date_stats.keys()):
        stats = date_stats[date]
        chart_data['dates'].append(date.strftime('%m-%d'))
        chart_data['count'].append(stats['total'])
        if stats['total'] > 0:
            chart_data['accuracy'].append(round((stats['correct'] / stats['total']) * 100, 1))
        else:
            chart_data['accuracy'].append(0)
    
    context = {
        'learning_records': learning_records,
        'mastery_groups': mastery_groups,
        'today_reviews': today_reviews,
        'active_plans': active_plans,
        'chart_data': json.dumps(chart_data),
        'mastery_chart_data': mastery_chart_data
    }
    return render(request, 'dictation/progress.html', context)
