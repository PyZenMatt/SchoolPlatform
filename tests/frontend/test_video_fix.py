#!/usr/bin/env python
import os
import django
import sys
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course
import json

def test_video_upload_api():
    print("🧪 Testing video upload API fix...")
    
    # Create test client
    client = Client()
    User = get_user_model()
    
    # Get or create teacher user
    teacher = User.objects.filter(role='teacher').first()
    if not teacher:
        print("❌ No teacher found")
        return
    
    # Create a test course
    course = Course.objects.create(
        title="Test Course for Video Upload",
        description="Test course",
        teacher=teacher,
        category="disegno",
        is_approved=True
    )
    
    # Create a test video file (small content for testing)
    video_content = b"fake video content for testing"
    video_file = SimpleUploadedFile(
        "test_video.mp4",
        video_content,
        content_type="video/mp4"
    )
    
    # Login the teacher
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(teacher)
    access_token = str(refresh.access_token)
    
    # Test the API
    response = client.post('/api/v1/lessons/create/', {
        'title': 'Test Video Lesson API Fix',
        'content': 'Test content for video lesson',
        'duration': '45',
        'lesson_type': 'video',
        'course_id': str(course.id),
        'video_file': video_file,
    }, HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    print(f"📡 Response status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Lesson created successfully: {data.get('title')}")
        if data.get('video_file_url'):
            print(f"✅ Video URL: {data.get('video_file_url')}")
        else:
            print("⚠️ No video URL in response")
    else:
        print(f"❌ Error: {response.content.decode()}")
    
    # Cleanup
    course.delete()

if __name__ == "__main__":
    test_video_upload_api()
