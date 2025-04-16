from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images.blocks import ImageChooserBlock
from django.db import models
from wagtail.snippets.models import register_snippet
from core.models import Lesson, Course
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .blocks import LessonContentBlock
from django.contrib.auth.models import User
from django.conf import settings
from django import forms

class HomePage(Page):
    hero_title = models.CharField(max_length=255, blank=True)

    featured_lessons = models.ManyToManyField(
        'core.Lesson',
        blank=True,
        help_text="Seleziona lezioni da mettere in evidenza"
    )

    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('featured_lessons', widget=forms.CheckboxSelectMultiple),
    ]
    
    class Meta:
        verbose_name = "Homepage TeoArt"

class LessonIndexPage(Page):
    intro = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['courses'] = Course.objects.all().prefetch_related('lessons')
        return context

    def get_template(self, request, *args, **kwargs):
        return "cms/lesson_index_page.html"

class LessonPage(Page):
    teacher = models.ForeignKey(
           settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'teacher'}
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Principiante'),
            ('intermediate', 'Intermedio'),
            ('advanced', 'Avanzato')
        ]
    )
    body = StreamField(
        LessonContentBlock(),
        use_json_field=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('teacher'),
        FieldPanel('difficulty'),
        FieldPanel('body'),
    ]

    parent_page_types = ['LessonIndexPage']
    subpage_types = []

@register_snippet
class LessonSnippet(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    
    panels = [
        FieldPanel('lesson')
    ]
    
    def __str__(self):
        return self.lesson.title

@register_snippet
class CourseSnippet(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    
    panels = [
        FieldPanel('course')
    ]
    
    def __str__(self):
        return self.course.title

class HomePage(Page):
    hero_title = models.CharField(max_length=255, blank=True)
    featured_content = StreamField([
        ('featured_lessons', blocks.ListBlock(
            blocks.PageChooserBlock(
                target_model='cms.LessonSnippet',
                icon='fa-book'
            ),
            label="Lezioni in evidenza",
            help_text="Seleziona lezioni da mettere in evidenza"
        )),
        ('featured_courses', blocks.ListBlock(
            blocks.PageChooserBlock(
                target_model='cms.CourseSnippet',
                icon='fa-graduation-cap'
            ),
            label="Corsi in evidenza"
        )),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('featured_content'),
    ]

class LessonAdmin(SnippetViewSet):
    model = Lesson
    menu_label = "Lezioni"
    icon = "fa-book-open"
    list_display = ('title', 'teacher', 'price')
    list_filter = ('teacher',)
    search_fields = ('title', 'content')
    add_to_settings_menu = False
    panels = [
        FieldPanel('title'),
        FieldPanel('teacher'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('price'),
            FieldPanel('duration'),
        ], heading="Prezzo & Durata"),
    ]

class CourseAdmin(SnippetViewSet):
    model = Course
    menu_label = "Corsi"
    icon = "fa-graduation-cap"
    list_display = ('title', 'teacher', 'price')
    add_to_settings_menu = False
    panels = [
        FieldPanel('title'),
        FieldPanel('teacher'),
        FieldPanel('description'),
        FieldPanel('price'),
        FieldPanel('lessons'),
    ]

class ContentManagerGroup(SnippetViewSetGroup):
    menu_label = "Gestione Contenuti"
    menu_icon = "folder-open-inverse"
    items = (LessonAdmin, CourseAdmin)

class CoursePage(Page):
    course = models.OneToOneField(
        Course,
        on_delete=models.PROTECT,
        related_name='wagtail_page'
    )
    
    body = StreamField([
        ('description', blocks.RichTextBlock(
            features=['h2', 'h3', 'bold', 'italic', 'link', 'image'],
            icon='pilcrow'
        )),
        ('lesson_list', blocks.PageChooserBlock(
            target_model='cms.LessonPage',
            icon='fa-list-ol'
        )),
        ('requirements', blocks.ListBlock(
            blocks.CharBlock(),
            icon='fa-check-circle'
        )),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('course'),
        FieldPanel('body'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['enrolled_students'] = self.course.students.count()
        context['total_duration'] = self.course.total_duration()
        return context