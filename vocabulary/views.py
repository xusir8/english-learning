from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Word, WordList, WordListWord
import json
from django.db import models
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import WordList, WordLearningRecord, ReviewPlan

# Create your views here.

def word_list(request):
    """单词列表页面"""
    words = Word.objects.filter(is_active=True).order_by('word')
    word_lists = WordList.objects.all()
    
    context = {
        'words': words,
        'word_lists': word_lists,
    }
    return render(request, 'vocabulary/word_list.html', context)

def word_detail(request, word_id):
    """单词详情页面"""
    word = get_object_or_404(Word, id=word_id)
    context = {
        'word': word,
    }
    return render(request, 'vocabulary/word_detail.html', context)

def word_list_detail(request, list_id):
    """单词列表详情页面"""
    word_list_obj = get_object_or_404(WordList, id=list_id)
    words = word_list_obj.words.all().order_by('wordlistword__order')
    
    context = {
        'word_list': word_list_obj,
        'words': words,
    }
    return render(request, 'vocabulary/word_list_detail.html', context)

@csrf_exempt
def add_word(request):
    """添加单词API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word = Word.objects.create(
                word=data['word'],
                phonetic=data.get('phonetic', ''),
                translation=data['translation'],
                example_sentence=data.get('example_sentence', ''),
                difficulty_level=data.get('difficulty_level', 1)
            )
            return JsonResponse({
                'success': True,
                'message': '单词添加成功',
                'word_id': word.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

@csrf_exempt
def create_word_list(request):
    """创建单词列表API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_list = WordList.objects.create(
                name=data['name'],
                description=data.get('description', '')
            )
            return JsonResponse({
                'success': True,
                'message': '单词列表创建成功',
                'list_id': word_list.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'创建失败: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

@csrf_exempt
def add_word_to_list(request):
    """添加单词到列表API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_list = get_object_or_404(WordList, id=data['list_id'])
            word = get_object_or_404(Word, id=data['word_id'])
            
            # 检查是否已存在
            if WordListWord.objects.filter(word_list=word_list, word=word).exists():
                return JsonResponse({
                    'success': False,
                    'message': '单词已在此列表中'
                })
            
            # 检查是否有同名单词已在此列表中
            if WordListWord.objects.filter(word_list=word_list, word__word=word.word).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'单词"{word.word}"已在此列表中'
                })
            
            # 获取当前最大排序号
            max_order = WordListWord.objects.filter(word_list=word_list).aggregate(
                models.Max('order'))['order__max'] or 0
            
            WordListWord.objects.create(
                word_list=word_list,
                word=word,
                order=max_order + 1
            )
            
            return JsonResponse({
                'success': True,
                'message': '单词已添加到列表'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

@login_required
def review_dashboard(request):
    """复习计划仪表板"""
    active_plans = ReviewPlan.objects.filter(
        user=request.user,
        is_active=True
    )
    
    # 获取今天需要复习的单词
    today_words = []
    for plan in active_plans:
        today_words.extend(plan.get_today_words())
    
    # 获取学习进度统计
    learning_stats = WordLearningRecord.objects.filter(user=request.user).aggregate(
        total_words=models.Count('id'),
        mastered_words=models.Count('id', filter=models.Q(mastery_level__gte=80)),
        in_progress=models.Count('id', filter=models.Q(mastery_level__lt=80))
    )
    
    return render(request, 'vocabulary/review_dashboard.html', {
        'active_plans': active_plans,
        'today_words': today_words,
        'learning_stats': learning_stats,
    })

@login_required
def create_review_plan(request):
    """创建复习计划"""
    if request.method == 'POST':
        word_list_id = request.POST.get('word_list')
        plan_type = request.POST.get('plan_type')
        start_date = request.POST.get('start_date')
        
        word_list = get_object_or_404(WordList, id=word_list_id)
        
        # 创建复习计划
        plan = ReviewPlan.objects.create(
            user=request.user,
            word_list=word_list,
            plan_type=plan_type,
            start_date=timezone.now() if not start_date else start_date,
        )
        
        # 如果是新学习计划，为所有单词创建学习记录
        if plan_type == 'NEW':
            words = word_list.words.all()
            for word in words:
                WordLearningRecord.objects.create(
                    word=word,
                    user=request.user,
                    next_review_date=timezone.now()
                )
        
        messages.success(request, '复习计划创建成功！')
        return redirect('review_dashboard')
    
    word_lists = WordList.objects.all()
    return render(request, 'vocabulary/create_review_plan.html', {
        'word_lists': word_lists
    })

@login_required
def review_word(request, record_id):
    """复习单个单词"""
    record = get_object_or_404(WordLearningRecord, id=record_id, user=request.user)
    
    if request.method == 'POST':
        result = request.POST.get('result') == 'correct'
        record.update_mastery(result)
        messages.success(request, '复习记录已更新！')
        return redirect('review_dashboard')
    
    return render(request, 'vocabulary/review_word.html', {
        'record': record
    })

@csrf_exempt
def import_words(request):
    """批量导入单词API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_list = get_object_or_404(WordList, id=data['list_id'])
            word_data = data['word_data'].strip().split('\n')
            
            imported_count = 0
            failed_words = []
            line_number = 0
            
            # 获取当前词书中已有的单词文本列表，用于检查重复
            existing_words_in_list = set(word_list.words.values_list('word', flat=True))
            
            for line in word_data:
                line_number += 1
                if not line.strip():
                    continue
                    
                parts = line.split(',')
                
                # 只要有单词就继续处理，格式可以很灵活
                word_text = parts[0].strip()
                
                # 验证单词不能为空
                if not word_text:
                    failed_words.append({
                        'line': line_number,
                        'content': line.strip(),
                        'reason': '单词不能为空'
                    })
                    continue
                
                # 检查单词是否已在当前词书中
                if word_text in existing_words_in_list:
                    failed_words.append({
                        'line': line_number,
                        'content': line.strip(),
                        'reason': f'单词"{word_text}"已在当前词书中'
                    })
                    continue
                
                # 解析其他字段，允许灵活的格式
                phonetic = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ''
                translation = parts[2].strip() if len(parts) > 2 and parts[2].strip() else ''
                example = parts[3].strip() if len(parts) > 3 and parts[3].strip() else ''
                
                # 如果没有第三个字段，第二个字段作为释义
                if not translation and phonetic:
                    translation = phonetic
                    phonetic = ''
                
                # 如果仍然没有释义，使用单词本身作为释义
                if not translation:
                    translation = word_text
                
                difficulty = 2  # 默认中等难度
                if len(parts) > 4 and parts[4].strip():
                    try:
                        difficulty_text = parts[4].strip().lower()
                        if difficulty_text in ['1', 'easy', '简单']:
                            difficulty = 1
                        elif difficulty_text in ['3', 'hard', '困难']:
                            difficulty = 3
                    except:
                        pass
                
                try:
                    # 创建新单词
                    word = Word.objects.create(
                        word=word_text,
                        phonetic=phonetic,
                        translation=translation,
                        example_sentence=example,
                        difficulty_level=difficulty
                    )
                    
                    # 获取当前最大排序号
                    max_order = WordListWord.objects.filter(word_list=word_list).aggregate(
                        models.Max('order'))['order__max'] or 0
                    
                    # 添加到词书
                    WordListWord.objects.create(
                        word_list=word_list,
                        word=word,
                        order=max_order + 1
                    )
                    
                    # 更新已存在单词集合，用于后续检查
                    existing_words_in_list.add(word_text)
                    
                    imported_count += 1
                    
                except Exception as e:
                    failed_words.append({
                        'line': line_number,
                        'content': line.strip(),
                        'reason': str(e)
                    })
            
            return JsonResponse({
                'success': True,
                'message': f'成功导入{imported_count}个单词，失败{len(failed_words)}个',
                'imported_count': imported_count,
                'failed_words': failed_words
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'导入失败: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})

@csrf_exempt
def get_word(request, word_id):
    """获取单词API"""
    try:
        word = get_object_or_404(Word, id=word_id)
        return JsonResponse({
            'success': True,
            'word': {
                'id': word.id,
                'word': word.word,
                'phonetic': word.phonetic,
                'translation': word.translation,
                'example_sentence': word.example_sentence,
                'difficulty_level': word.difficulty_level
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@csrf_exempt
def update_word(request, word_id):
    """更新单词API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word = get_object_or_404(Word, id=word_id)
            
            # 获取新的单词文本
            new_word_text = data.get('word', word.word)
            
            # 如果单词文本发生变化，检查是否会与同一单词书中的其他单词冲突
            if new_word_text != word.word:
                # 获取当前单词所在的所有单词书
                word_lists = WordList.objects.filter(wordlistword__word=word)
                
                for wl in word_lists:
                    # 检查每个单词书中是否有同名单词(排除当前单词)
                    if WordListWord.objects.filter(
                        word_list=wl, 
                        word__word=new_word_text
                    ).exclude(word=word).exists():
                        return JsonResponse({
                            'success': False,
                            'message': f'更新失败：单词"{new_word_text}"已存在于词书"{wl.name}"中，请使用其他单词'
                        })
            
            # 更新单词信息
            word.word = new_word_text
            word.phonetic = data.get('phonetic', word.phonetic)
            word.translation = data.get('translation', word.translation)
            word.example_sentence = data.get('example_sentence', word.example_sentence)
            word.difficulty_level = data.get('difficulty_level', word.difficulty_level)
            word.save()
            
            return JsonResponse({
                'success': True,
                'message': '单词更新成功'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'更新失败：{str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': '只支持POST请求'
    })

@csrf_exempt
def remove_word_from_list(request, list_id, word_id):
    """从词书中移除单词API"""
    if request.method == 'POST':
        try:
            word_list = get_object_or_404(WordList, id=list_id)
            word = get_object_or_404(Word, id=word_id)
            
            # 删除关联
            WordListWord.objects.filter(word_list=word_list, word=word).delete()
            
            return JsonResponse({
                'success': True,
                'message': '单词已从词书中移除'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': '只支持POST请求'
    })

@csrf_exempt
def update_word_list(request, list_id):
    """更新词书API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_list = get_object_or_404(WordList, id=list_id)
            
            word_list.name = data.get('name', word_list.name)
            word_list.description = data.get('description', word_list.description)
            word_list.save()
            
            return JsonResponse({
                'success': True,
                'message': '词书更新成功'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': '只支持POST请求'
    })

@csrf_exempt
def delete_word_list(request, list_id):
    """删除词书API"""
    if request.method == 'POST':
        try:
            word_list = get_object_or_404(WordList, id=list_id)
            word_list.delete()
            
            return JsonResponse({
                'success': True,
                'message': '词书已删除'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': '只支持POST请求'
    })

@csrf_exempt
def batch_remove_words(request):
    """批量从词书中移除单词API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_list = get_object_or_404(WordList, id=data['list_id'])
            word_ids = data['word_ids']
            
            if not word_ids:
                return JsonResponse({
                    'success': False,
                    'message': '请选择要删除的单词'
                })
            
            # 批量删除词书中的单词关联
            removed_count = WordListWord.objects.filter(
                word_list=word_list,
                word_id__in=word_ids
            ).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'成功从词书中移除 {removed_count} 个单词',
                'removed_count': removed_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'删除失败: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'})
