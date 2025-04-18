from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import User, Lesson, Exercise, Course
from django import forms

# Aggiungi questo form personalizzato
class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra solo studenti per il campo students
        if 'students' in self.fields:
            self.fields['students'].queryset = User.objects.filter(role='student')
        # Filtra solo docenti per il campo teacher
        if 'teacher' in self.fields:
            self.fields['teacher'].queryset = User.objects.filter(role='teacher')

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informazioni Personali', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permessi', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ("Ruolo & TeoCoin", {"fields": ("role", "teo_coins")}),
        ('Date importanti', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'role', 'teo_coins', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    # Aggiungi questo metodo per filtrare l'autocomplete
    def get_search_results(self, request, queryset, search_term):
        if 'autocomplete' in request.path:
            model_name = request.GET.get('model_name', '')
            field_name = request.GET.get('field_name', '')
            if model_name == 'course' and field_name == 'students':
                queryset = queryset.filter(role='student')
            elif model_name == 'course' and field_name == 'teacher':
                queryset = queryset.filter(role='teacher')
        return super().get_search_results(request, queryset, search_term)

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    readonly_fields = ['teacher']
    fk_name = 'course'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'course':
            kwargs['queryset'] = Course.objects.filter(teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'teacher', 'duration']
    list_editable = ['course']
    list_filter = ['course__teacher']
    search_fields = ['title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(teacher=request.user)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)

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

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm  # Aggiungi il form personalizzato
    inlines = [LessonInline]
    list_display = ['title', 'price', 'teacher', 'total_students']
    list_filter = ['teacher']
    search_fields = ['title']
    filter_horizontal = ('students',)
    autocomplete_fields = ['students', 'teacher']

    # Nuovo metodo per contare gli studenti
    def total_students(self, obj):
        return obj.students.count()
    total_students.short_description = "Studenti Iscritti"

    def get_search_results(self, request, queryset, search_term):
        if 'autocomplete' in request.path:
            field_name = request.GET.get('field_name', '')
            if field_name == 'students':
                return User.objects.filter(
                    role='student',
                    username__icontains=search_term
                ), False
            elif field_name == 'teacher':
                return User.objects.filter(
                    role='teacher',
                    username__icontains=search_term
                ), False
        return super().get_search_results(request, queryset, search_term)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and request.user.role == 'teacher':
            form.base_fields['teacher'].initial = request.user
            form.base_fields['teacher'].disabled = True
            form.base_fields['teacher'].widget.can_add_related = False
            form.base_fields['teacher'].widget.can_change_related = False
        return form

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
admin.site.register(Exercise, ExerciseAdmin)