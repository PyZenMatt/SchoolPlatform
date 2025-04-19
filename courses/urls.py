from django.urls import path
from .views import LessonListCreateView, ExerciseListCreateView, PurchaseLessonView, CourseListCreateView, CourseDetailView, CreateLessonAPI, CreateCourseAPI, CourseEnrollmentAPI, PurchaseCourseView

urlpatterns = [
    path('lessons/<int:lesson_id>/purchase/', PurchaseLessonView.as_view(), name='purchase-lesson'),
    path('courses/', CourseListCreateView.as_view()),
    path('courses/<int:course_id>/enroll/', CourseEnrollmentAPI.as_view(), name='course_enroll'),
    path('courses/<int:course_id>/purchase/', PurchaseCourseView.as_view(), name='course_purchase'),
    path('courses/<int:pk>/', CourseDetailView.as_view()),
    path('lessons/', LessonListCreateView.as_view(), name='lesson_list_create'),
    path('exercises/', ExerciseListCreateView.as_view(), name='exercise_list_create'),
    path('teacher/lessons/', CreateLessonAPI.as_view(), name='create_lesson'),
    path('teacher/courses/', CreateCourseAPI.as_view(), name='create_courses'),
]
