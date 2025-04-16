from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import User, Lesson, Exercise

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Ruolo & TeoCoin", {"fields": ("role", "teo_coins")}),
    )
    list_display = ('username', 'email', 'role', 'teo_coins')
    list_filter = ('role',)
    search_fields = ('username', 'email')

class LessonAdmin(PermissionRequiredMixin, admin.ModelAdmin):
    list_display = ('title', 'teacher', 'price', 'duration', 'created_at')
    list_filter = ('teacher',)
    search_fields = ('title', 'content')
    raw_id_fields = ('students',)
    date_hierarchy = 'created_at'
    permission_required = ('core.view_lesson', 'core.change_lesson')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['teacher'].queryset = User.objects.filter(role='teacher')
        return form

class ExerciseAdmin(PermissionRequiredMixin, admin.ModelAdmin):
    list_display = ('student', 'lesson', 'status', 'score', 'submission_short')
    list_filter = (
        ('student', admin.RelatedOnlyFieldListFilter),
        ('lesson', admin.RelatedOnlyFieldListFilter),
        'status'
    )
    search_fields = ('lesson__title', 'student__username')
    raw_id_fields = ('lesson',)
    date_hierarchy = 'created_at'
    permission_required = ('core.view_exercise', 'core.change_exercise')

    def submission_short(self, obj):
        return obj.submission[:50] + '...' if len(obj.submission) > 50 else obj.submission
    submission_short.short_description = 'Submission'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['student'].queryset = User.objects.filter(role='student')
        return form

admin.site.register(User, UserAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Exercise, ExerciseAdmin)