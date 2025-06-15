#!/usr/bin/env python3
"""
⚡ QUICK SPEED TEST
==================

Test rapido della velocità delle pagine principali
"""

import time
import requests
import statistics
from urllib.parse import urljoin

class QuickSpeedTest:
    def __init__(self, base_url="http://localhost:4000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_page_speed(self, page, runs=3):
        """Testa velocità di una pagina con multiple run"""
        url = urljoin(self.base_url, page)
        times = []
        
        for i in range(runs):
            try:
                start = time.time()
                response = self.session.get(url, timeout=10)
                load_time = time.time() - start
                times.append(load_time)
            except Exception as e:
                print(f"❌ Errore su {page}: {e}")
                return None
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        # Status based on time
        if avg_time < 0.5:
            status = "🟢 EXCELLENT"
        elif avg_time < 1.0:
            status = "🟡 GOOD"
        elif avg_time < 2.0:
            status = "🟠 SLOW"
        else:
            status = "🔴 CRITICAL"
            
        print(f"{page:<20} {avg_time:.3f}s (min: {min_time:.3f}s, max: {max_time:.3f}s) {status}")
        return avg_time
    
    def run_quick_test(self):
        """Esegue test rapido"""
        print("⚡ QUICK SPEED TEST")
        print("=" * 50)
        
        pages = ['/', '/eng/features/', '/eng/invest/', '/eng/technology/']
        times = []
        
        for page in pages:
            avg_time = self.test_page_speed(page)
            if avg_time:
                times.append(avg_time)
        
        if times:
            overall_avg = statistics.mean(times)
            print(f"\n📊 Overall Average: {overall_avg:.3f}s")
            
            if overall_avg < 1.0:
                print("🎉 PERFORMANCE: EXCELLENT!")
            elif overall_avg < 2.0:
                print("👍 PERFORMANCE: GOOD")
            else:
                print("⚠️ PERFORMANCE: NEEDS OPTIMIZATION")

if __name__ == "__main__":
    tester = QuickSpeedTest()
    tester.run_quick_test()
