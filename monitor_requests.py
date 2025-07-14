#!/usr/bin/env python
"""
Real-time Request Monitor
Monitor all incoming requests to see if frontend calls are reaching the backend
"""

import os
import sys
import django
from django.http import HttpResponse
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

print("🔍 REAL-TIME REQUEST MONITOR")
print("=" * 50)
print("This tool monitors all incoming HTTP requests.")
print("Now perform the frontend action (click the accept button) and watch for requests below.")
print("=" * 50)

# Monitor the API performance log in real-time
try:
    import subprocess
    
    # Start monitoring the log file
    log_file = "logs/api_performance.log"
    
    if os.path.exists(log_file):
        print(f"📊 Monitoring {log_file} for new requests...")
        print("🎯 Look for POST requests to /api/v1/teocoin/teacher/absorptions/choose/")
        print("📱 Now go to your frontend and click the 'Accept TEO' button")
        print("-" * 50)
        
        # Use tail -f to follow the log file
        process = subprocess.Popen(['tail', '-f', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
                    
                    # Highlight teacher absorption requests
                    if 'teacher/absorptions' in line:
                        print("🎯 TEACHER ABSORPTION REQUEST DETECTED! ^^^")
                    elif 'POST' in line:
                        print("📤 POST request detected ^^^")
                        
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
        finally:
            process.terminate()
    else:
        print(f"❌ Log file not found: {log_file}")
        print("Creating a simple HTTP server monitor instead...")
        
        # Alternative: Monitor Django's console output
        print("👀 Start clicking the frontend button now. We'll monitor for any activity...")
        
        # Simple loop to wait for user input
        input("Press Enter after you've clicked the frontend button...")
        print("📊 Checking recent logs...")
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:]  # Last 10 lines
                print("Recent log entries:")
                for line in recent_lines:
                    print(f"  {line.strip()}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
