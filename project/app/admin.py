from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Quiz, Question, Option, QuizAttempt

class CustomUserAdmin(UserAdmin):
    model = UserProfile
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('avatar', 'total_points')}),
    )

class OptionInline(admin.TabularInline):
    model = Option
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'creator', 'join_code', 'created_at')

admin.site.register(UserProfile, CustomUserAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)
admin.site.register(QuizAttempt)
