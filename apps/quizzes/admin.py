from django.contrib import admin
from .models import Quiz, Question, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4
    min_num = 4
    max_num = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'topic', 'is_public', 'created_by_ai', 'created_at')
    list_filter = ('is_public', 'created_by_ai', 'topic', 'created_at')
    search_fields = ('title', 'topic', 'owner__username')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order', 'time_limit', 'points')
    list_filter = ('quiz', 'time_limit')
    search_fields = ('text', 'quiz__title')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
