from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserProfile, Quiz, Question, Option, QuizAttempt
from .serializers import (
    UserProfileSerializer, QuizSerializer, QuizCreateSerializer,
    QuestionSerializer, OptionSerializer, QuizAttemptSerializer
)

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creator__username']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateSerializer
        return QuizSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz__id']
    ordering_fields = ['order']

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question__id']

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user__username', 'quiz__id']
    ordering_fields = ['score', 'completed_at']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
