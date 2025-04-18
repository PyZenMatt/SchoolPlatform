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
        fields = ['id', 'title', 'content', 'course', 'teacher', 'created_at']
        read_only_fields = ['teacher']
    
    def validate_course(self, value):
        if value and value.teacher != self.context['request'].user:
            raise serializers.ValidationError("Non sei il teacher di questo corso")
        return value

class ExerciseSerializer(serializers.ModelSerializer):
    student = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.filter(role='student')
    )
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())

    class Meta:
        model = Exercise
        fields = ['id', 'student', 'lesson', 'submission', 'score', 'feedback']
        read_only_fields = ['student', 'score', 'feedback']

    def validate_lesson(self, value):
        # Verifica che lo studente sia iscritto alla lezione
        if not self.context['request'].user.purchased_lessons.filter(id=value.id).exists():
            raise serializers.ValidationError("Non sei iscritto a questa lezione")
        return value

class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'teo_coins', 'email']

class TeoCoinTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeoCoinTransaction
        fields = ['user', 'amount', 'created_at', 'transaction_type']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    teacher = UserSerializer(read_only=True)
    total_duration = serializers.SerializerMethodField()
    students = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'teacher', 'lessons','total_duration', 'students', 'created_at']
        read_only_fields = ['teacher']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Il prezzo deve essere maggiore di zero")
        return value

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'teacher', 'lessons', 'students', 'created_at']
        read_only_fields = ['teacher', 'students']
        extra_kwargs = {
            'lessons': {'read_only': True}
        }

    def total_duration(self):
        return sum(lesson.duration for lesson in self.lessons.all())

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
    total_earnings = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'price', 'total_earnings', 'total_students']

    def get_total_earnings(self, obj):
        return obj.price * obj.students.count() * 0.9

    def get_total_students(self, obj):
        return obj.students.count()


        