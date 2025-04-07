# quizapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'results', views.ResultViewSet, basename='result')

urlpatterns = [
    # Web Views
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('result/<int:result_id>/', views.result_view, name='result'),
    path('scores/', views.view_scores_view, name='view_scores'),
    path('add_question/', views.add_question_view, name='add_question'),
    
    # API Endpoints (simple URLs)
    path('api/register/', views.UserViewSet.as_view({'post': 'register'}), name='api_register'),
    path('api/login/', views.UserViewSet.as_view({'post': 'login'}), name='api_login'),
    path('api/questions/', views.QuestionViewSet.as_view({'get': 'list'}), name='api_questions'),
    path('api/submit-quiz/', views.ResultViewSet.as_view({'post': 'submit_quiz'}), name='api_submit_quiz'),
    path('api/results/', views.ResultViewSet.as_view({'get': 'list'}), name='api_results'),
]