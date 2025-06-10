from django.urls import path

# === COURSES ===
from courses.views.courses import CourseListCreateView, CourseDetailView, CreateCourseAPI

from courses.views.enrollments import (
    PurchaseCourseView,
    StudentEnrolledCoursesView,
    TeacherCourseStudentsView
)

# === LESSONS ===
from courses.views.lessons import (
    CourseLessonsView,
    AllLessonsWithCourseView,
    LessonCreateAssignView,
    AssignLessonToCourseAPI,
    LessonDetailView,
    LessonExercisesView,
    LessonViewSet,
    MarkLessonCompleteView
)

# === EXERCISES ===
from courses.views.exercises import (
    CreateExerciseView,
    SubmitExerciseView,
    ReviewExerciseView,
    MySubmissionView,           
    AssignedReviewsView,        
    SubmissionDetailView,   
    SubmissionHistoryView, 
    ReviewHistoryView,        
    ExerciseSubmissionsView,
    ExerciseDebugReviewersView,
    ExerciseDetailView
)

# === PENDING COURSES ===
from courses.views.pending import PendingCoursesView, ApproveCourseView, RejectCourseView


urlpatterns = [
    # === COURSES ===
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:course_id>/purchase/', PurchaseCourseView.as_view(), name='course-purchase'),

    # === ENROLLMENTS ===
    path('student/enrolled_courses/', StudentEnrolledCoursesView.as_view(), name='student-enrolled-courses'),
    path('teacher/courses/students/', TeacherCourseStudentsView.as_view(), name='teacher-course-students'),

    # === LESSONS ===
    path('courses/<int:course_id>/lessons/', CourseLessonsView.as_view(), name='course-lessons'),
    path('lessons/all/', AllLessonsWithCourseView.as_view(), name='all-lessons-with-course'),
    path('lessons/create/', LessonCreateAssignView.as_view(), name='create-assign-lesson'),
    path('lessons/<int:lesson_id>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/exercises/', LessonExercisesView.as_view(), name='lesson-exercises'),
    path('lessons/<int:lesson_id>/mark_complete/', MarkLessonCompleteView.as_view(), name='lesson-mark-complete'),

    # === EXERCISES ===
    path('exercises/create/', CreateExerciseView.as_view(), name='create-exercise'),
    path('exercises/<int:exercise_id>/submit/', SubmitExerciseView.as_view(), name='submit-exercise'),
    path('exercises/<int:submission_id>/review/', ReviewExerciseView.as_view(), name='review-exercise'),
    # --- Nuovi endpoint peer review ---
    path('exercises/<int:exercise_id>/my_submission/', MySubmissionView.as_view(), name='my-exercise-submission'),
    path('reviews/assigned/', AssignedReviewsView.as_view(), name='assigned-reviews'),
    path('submissions/<int:submission_id>/', SubmissionDetailView.as_view(), name='submission-detail'),
    path('exercises/submissions/', SubmissionHistoryView.as_view(), name='submission-history'),
    path('reviews/history/', ReviewHistoryView.as_view(), name='review-history'),
    path('exercises/<int:exercise_id>/submissions/', ExerciseSubmissionsView.as_view(), name='exercise-submissions'), # opzionale
    path('exercises/<int:exercise_id>/debug_reviewers/', ExerciseDebugReviewersView.as_view(), name='exercise-debug-reviewers'),
    path('exercises/<int:id>/', ExerciseDetailView.as_view(), name='exercise-detail'),

    # === PENDING COURSES ===
    path('pending-courses/', PendingCoursesView.as_view(), name='pending-courses'),
    path('approve-course/<int:course_id>/', ApproveCourseView.as_view(), name='approve-course'),
    path('reject-course/<int:course_id>/', RejectCourseView.as_view(), name='reject-course'),
]
