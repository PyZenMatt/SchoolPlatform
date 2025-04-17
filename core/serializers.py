from rest_framework import serializers
from .models import User, Lesson, Exercise, TeoCoinTransaction, Course, Notification
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password2": "Le password non coincidono."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['teacher', 'students']

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'teo_coins']

class TeoCoinTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeoCoinTransaction
        fields = ['user', 'amount', 'created_at', 'transaction_type']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    teacher = UserSerializer(read_only=True)
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_total_duration(self, obj):
        return obj.total_duration()

class NotificationSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'read', 'created_at', 'related_object']
        ordering = ['-created_at']

    def get_related_object(self, obj):
        try:
            if obj.notification_type == 'exercise_graded':
                exercise = Exercise.objects.get(id=obj.related_object_id)
                return {
                    'id': exercise.id,
                    'score': exercise.score,
                    'lesson_title': exercise.lesson.title
                }
            elif obj.notification_type == 'lesson_purchased':
                lesson = Lesson.objects.get(id=obj.related_object_id)
                return {
                    'id': lesson.id,
                    'title': lesson.title,
                    'price': lesson.price
                }
        except Exception as e:
            return None
        
class TeacherLessonSerializer(serializers.ModelSerializer):
    total_students = serializers.SerializerMethodField()
    total_earnings = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'price', 'total_students', 'total_earnings']

    def get_total_students(self, obj):
        return obj.students.count()

    def get_total_earnings(self, obj):
        return obj.price * obj.students.count() * 0.9  # 10% fee to platform    

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'price', 'total_students', 'total_earnings']

class TeacherCourseSerializer(serializers.ModelSerializer):
    lessons = TeacherLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'price', 'lessons', 'created_at']

        