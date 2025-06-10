from rest_framework import serializers
from rewards.models import BlockchainTransaction
from courses.models import Course
from users.serializers import UserSerializer


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for blockchain transactions - replaces the old TeoCoinTransaction serializer.
    """
    buyer = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = BlockchainTransaction
        fields = ['id', 'created_at', 'amount', 'transaction_type', 'buyer', 'description', 'tx_hash', 'status']

    def get_buyer(self, obj):
        # For course earnings, show who bought the course
        if obj.transaction_type == 'course_earned' and obj.related_object_id:
            purchase = BlockchainTransaction.objects.filter(
                transaction_type='course_purchase',
                related_object_id=obj.related_object_id
            ).order_by('-created_at').first()
            if purchase and purchase.user:
                return purchase.user.username
        # For course purchases, the buyer is the user
        if obj.transaction_type == 'course_purchase' and obj.user:
            return obj.user.username
        return None

    def get_description(self, obj):
        try:
            if obj.transaction_type == 'course_purchase':
                if obj.related_object_id:
                    try:
                        course = Course.objects.get(id=obj.related_object_id)
                        return f"Acquisto corso: {course.title}"
                    except Course.DoesNotExist:
                        return "Acquisto corso: (corso non trovato)"
                return "Acquisto corso"

            if obj.transaction_type == 'course_earned':
                if obj.related_object_id:
                    try:
                        course = Course.objects.get(id=obj.related_object_id)
                        return f"Vendita corso: {course.title}"
                    except Course.DoesNotExist:
                        return "Vendita corso: (corso non trovato)"
                return "Vendita corso"

            if obj.transaction_type == 'exercise_reward':
                return f"Premio esercizio (ID: {obj.related_object_id})"

            if obj.transaction_type == 'review_reward':
                return f"Premio valutazione (ID: {obj.related_object_id})"

            return obj.transaction_type.replace('_', ' ').title()

        except Exception as e:
            return f"Transazione blockchain: {obj.transaction_type}"


class TeacherCourseSerializer(serializers.ModelSerializer):
    students_count = serializers.SerializerMethodField()
    teacher = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'teacher',
            'students_count', 'created_at', 'updated_at'
        ]

    def get_students_count(self, obj):
        return obj.students.count()


