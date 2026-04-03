from rest_framework import serializers
from .models import UserProfile, Quiz, Question, Option, QuizAttempt

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'avatar', 'total_points']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'options']

class QuizSerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'creator', 'join_code', 'created_at', 'questions']

class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to create a quiz.")
        quiz = Quiz.objects.create(creator=user, **validated_data)
        return quiz

class QuizAttemptSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    quiz = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'quiz', 'score', 'completed_at']
