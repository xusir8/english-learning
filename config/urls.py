"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

def home(request):
    return redirect('dictation:home')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('vocabulary/', include('vocabulary.urls')),
    path('dictation/', include('dictation.urls')),
    path('tts/', include('tts.urls')),
    path('test-echarts/', TemplateView.as_view(template_name='test_echarts.html'), name='test_echarts'),
    path('test-dictation/', TemplateView.as_view(template_name='test_dictation.html'), name='test_dictation'),
    path('test-voice/', TemplateView.as_view(template_name='test_voice.html'), name='test_voice'),
    path('test-dictation-hidden/', TemplateView.as_view(template_name='test_dictation_hidden.html'), name='test_dictation_hidden'),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # 添加media文件的URL模式
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
