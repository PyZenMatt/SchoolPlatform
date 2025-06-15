#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime
import statistics

class JekyllSpeedTester:
    def __init__(self, base_url="http://localhost:4000"):
        self.base_url = base_url
        self.pages = [
            {"name": "Homepage", "url": "/"},
            {"name": "Features EN", "url": "/eng/features/"},
            {"name": "Features IT", "url": "/ita/features/"},
            {"name": "Technology EN", "url": "/eng/technology/"},
            {"name": "Technology IT", "url": "/ita/technology/"},
            {"name": "Invest EN", "url": "/eng/invest/"},
            {"name": "Invest IT", "url": "/ita/invest/"},
            {"name": "Roadmap EN", "url": "/eng/roadmap/"},
            {"name": "Roadmap IT", "url": "/ita/roadmap/"},
            {"name": "Tokenomics EN", "url": "/eng/tokenomics/"},
            {"name": "Tokenomics IT", "url": "/ita/tokenomics/"}
        ]
        
    def test_page_speed(self, url, runs=3):
        """Testa la velocità di una pagina con multiple runs"""
        times = []
        sizes = []
        
        for i in range(runs):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = (end_time - start_time) * 1000  # in milliseconds
                    page_size = len(response.content)
                    
                    times.append(load_time)
                    sizes.append(page_size)
                else:
                    print(f"❌ Error {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                print(f"❌ Request failed for {url}: {e}")
                
        return {
            "avg_time": statistics.mean(times) if times else 0,
            "min_time": min(times) if times else 0,
            "max_time": max(times) if times else 0,
            "avg_size": statistics.mean(sizes) if sizes else 0,
            "status": "success" if times else "failed"
        }
    
    def format_size(self, size_bytes):
        """Formatta la dimensione in KB/MB"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.1f}MB"
    
    def get_performance_grade(self, load_time):
        """Assegna un grade basato sul tempo di caricamento"""
        if load_time < 200:
            return "🟢 A+"
        elif load_time < 500:
            return "🟢 A"
        elif load_time < 1000:
            return "🟡 B"
        elif load_time < 2000:
            return "🟡 C"
        elif load_time < 3000:
            return "🔴 D"
        else:
            return "🔴 F"
    
    def run_speed_test(self):
        """Esegue il test completo"""
        print("🚀 Jekyll Site Speed Test")
        print(f"📍 Testing server: {self.base_url}")
        print("=" * 80)
        
        # Verifica che il server sia raggiungibile
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code != 200:
                print("❌ Jekyll server not accessible")
                return
        except requests.RequestException:
            print("❌ Jekyll server not running on http://localhost:4000")
            print("💡 Start it with: bundle exec jekyll serve")
            return
        
        results = []
        
        print(f"{'Page':<15} {'Grade':<8} {'Avg Time':<10} {'Min Time':<10} {'Max Time':<10} {'Size':<10}")
        print("-" * 80)
        
        for page in self.pages:
            url = f"{self.base_url}{page['url']}"
            print(f"🧪 Testing {page['name']}...", end=" ")
            
            result = self.test_page_speed(url)
            result['page'] = page['name']
            result['url'] = page['url']
            results.append(result)
            
            if result['status'] == 'success':
                grade = self.get_performance_grade(result['avg_time'])
                avg_time = f"{result['avg_time']:.0f}ms"
                min_time = f"{result['min_time']:.0f}ms"
                max_time = f"{result['max_time']:.0f}ms"
                size = self.format_size(result['avg_size'])
                
                print(f"\r{page['name']:<15} {grade:<8} {avg_time:<10} {min_time:<10} {max_time:<10} {size:<10}")
            else:
                print(f"\r{page['name']:<15} {'❌ FAIL':<8} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10}")
        
        print("-" * 80)
        
        # Statistiche generali
        successful_results = [r for r in results if r['status'] == 'success']
        
        if successful_results:
            avg_load_time = statistics.mean([r['avg_time'] for r in successful_results])
            total_size = sum([r['avg_size'] for r in successful_results])
            
            print(f"\n📊 SUMMARY:")
            print(f"   ✅ Successful tests: {len(successful_results)}/{len(results)}")
            print(f"   ⚡ Average load time: {avg_load_time:.0f}ms")
            print(f"   📦 Total site size: {self.format_size(total_size)}")
            print(f"   🎯 Performance grade: {self.get_performance_grade(avg_load_time)}")
            
            # Raccomandazioni
            print(f"\n💡 RECOMMENDATIONS:")
            if avg_load_time > 1000:
                print("   🔴 Average load time > 1s - consider optimization")
            if total_size > 5 * 1024 * 1024:  # 5MB
                print("   🔴 Total size > 5MB - optimize assets")
            
            print(f"\n🎯 TARGETS:")
            print(f"   Load time: <500ms (good), <200ms (excellent)")
            print(f"   Page size: <1MB per page")
        
        # Salva risultati
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = f"../reports/speed-test-{timestamp}.json"
        
        import os
        os.makedirs("../reports", exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {report_file}")

if __name__ == "__main__":
    tester = JekyllSpeedTester()
    tester.run_speed_test()
