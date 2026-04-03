from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserProfileViewSet, QuizViewSet, QuestionViewSet,
    OptionViewSet, QuizAttemptViewSet
)

router = DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'options', OptionViewSet)
router.register(r'attempts', QuizAttemptViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
