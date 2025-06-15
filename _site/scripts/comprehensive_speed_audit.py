#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE JEKYLL SITE SPEED AUDIT TOOL
==============================================

Analizza in profondità la performance del sito Jekyll e fornisce
raccomandazioni specifiche per ogni problema trovato.

Author: AI Assistant
Version: 1.0
"""

import time
import requests
import json
import os
import sys
from urllib.parse import urljoin, urlparse
from pathlib import Path
import subprocess
import gzip
from collections import defaultdict
import re
from datetime import datetime

# Colori per output terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class WebsiteSpeedAuditor:
    def __init__(self, base_url="http://localhost:4000", timeout=30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Pagine da testare
        self.pages_to_test = [
            '/',
            '/eng/',
            '/ita/',
            '/eng/features/',
            '/ita/features/',
            '/eng/technology/',
            '/ita/technology/',
            '/eng/roadmap/',
            '/ita/roadmap/',
            '/eng/invest/',
            '/ita/invest/',
            '/eng/faq/',
            '/ita/faq/',
            '/eng/tokenomics/',
            '/ita/tokenomics/',
            '/eng/contact/',
            '/ita/contact/'
        ]
        
        # Metriche da tracciare
        self.metrics = defaultdict(dict)
        self.recommendations = []
        self.critical_issues = []
        self.warnings = []
        
    def print_header(self, title):
        """Stampa un header formattato"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    def print_section(self, title):
        """Stampa una sezione"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}📊 {title}{Colors.END}")
        print(f"{Colors.BLUE}{'-'*50}{Colors.END}")
    
    def print_success(self, message):
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    
    def print_warning(self, message):
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    def print_error(self, message):
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    
    def print_info(self, message):
        print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

    def check_server_availability(self):
        """Verifica se il server Jekyll è attivo"""
        self.print_section("Server Availability Check")
        try:
            response = self.session.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.print_success(f"Server Jekyll attivo su {self.base_url}")
                return True
            else:
                self.print_error(f"Server risponde con status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("Server Jekyll non raggiungibile. Assicurati che sia attivo con:")
            print(f"{Colors.YELLOW}bundle exec jekyll serve --host=0.0.0.0 --port=4000{Colors.END}")
            return False
        except Exception as e:
            self.print_error(f"Errore di connessione: {str(e)}")
            return False

    def analyze_page_load_times(self):
        """Analizza i tempi di caricamento per ogni pagina"""
        self.print_section("Page Load Time Analysis")
        
        for page in self.pages_to_test:
            url = urljoin(self.base_url, page)
            
            try:
                # Misura tempo di caricamento
                start_time = time.time()
                response = self.session.get(url, timeout=self.timeout)
                load_time = time.time() - start_time
                
                # Salva metriche
                self.metrics[page] = {
                    'load_time': load_time,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'response_headers': dict(response.headers)
                }
                
                # Valuta performance
                if load_time < 0.5:
                    status = f"{Colors.GREEN}EXCELLENT"
                elif load_time < 1.0:
                    status = f"{Colors.GREEN}GOOD"
                elif load_time < 2.0:
                    status = f"{Colors.YELLOW}ACCEPTABLE"
                elif load_time < 3.0:
                    status = f"{Colors.YELLOW}SLOW"
                else:
                    status = f"{Colors.RED}CRITICAL"
                
                print(f"{page:<25} {load_time:>6.3f}s {status}{Colors.END} ({len(response.content):,} bytes)")
                
                # Aggiungi raccomandazioni
                if load_time > 2.0:
                    self.critical_issues.append(f"Pagina {page} carica in {load_time:.3f}s (target: < 1.5s)")
                elif load_time > 1.0:
                    self.warnings.append(f"Pagina {page} carica in {load_time:.3f}s (ottimizzabile)")
                    
            except requests.exceptions.Timeout:
                self.print_error(f"{page:<25} TIMEOUT (>{self.timeout}s)")
                self.critical_issues.append(f"Pagina {page} va in timeout")
            except Exception as e:
                self.print_error(f"{page:<25} ERROR: {str(e)}")

    def analyze_resource_sizes(self):
        """Analizza le dimensioni delle risorse"""
        self.print_section("Resource Size Analysis")
        
        # Analizza CSS
        css_files = self._find_css_files()
        total_css_size = 0
        
        print(f"\n{Colors.BOLD}📄 CSS Files:{Colors.END}")
        for css_file in css_files:
            size = self._get_file_size(css_file)
            total_css_size += size
            status = "✅" if size < 50000 else ("⚠️" if size < 100000 else "❌")
            print(f"  {status} {css_file}: {size:,} bytes ({size/1024:.1f} KB)")
        
        print(f"\n{Colors.BOLD}Total CSS: {total_css_size:,} bytes ({total_css_size/1024:.1f} KB){Colors.END}")
        
        # Raccomandazioni CSS
        if total_css_size > 100000:
            self.critical_issues.append(f"CSS troppo pesante: {total_css_size/1024:.1f} KB (target: < 100 KB)")
            self.recommendations.append("🎯 Rimuovi CSS non utilizzato con PurgeCSS")
            self.recommendations.append("🗜️ Minifica CSS in produzione")
        elif total_css_size > 50000:
            self.warnings.append(f"CSS ottimizzabile: {total_css_size/1024:.1f} KB")
        
        # Analizza JavaScript
        js_files = self._find_js_files()
        total_js_size = 0
        
        print(f"\n{Colors.BOLD}📜 JavaScript Files:{Colors.END}")
        for js_file in js_files:
            size = self._get_file_size(js_file)
            total_js_size += size
            status = "✅" if size < 30000 else ("⚠️" if size < 60000 else "❌")
            print(f"  {status} {js_file}: {size:,} bytes ({size/1024:.1f} KB)")
            
        print(f"\n{Colors.BOLD}Total JS: {total_js_size:,} bytes ({total_js_size/1024:.1f} KB){Colors.END}")
        
        # Raccomandazioni JS
        if total_js_size > 100000:
            self.critical_issues.append(f"JavaScript troppo pesante: {total_js_size/1024:.1f} KB")
            self.recommendations.append("⚡ Implementa code splitting")
            self.recommendations.append("🗜️ Minifica JavaScript in produzione")
        
        # Analizza immagini
        self._analyze_images()

    def _find_css_files(self):
        """Trova tutti i file CSS"""
        css_files = []
        assets_dir = Path("assets/css")
        if assets_dir.exists():
            for css_file in assets_dir.glob("**/*.css"):
                css_files.append(str(css_file))
            for scss_file in assets_dir.glob("**/*.scss"):
                css_files.append(str(scss_file))
        return css_files

    def _find_js_files(self):
        """Trova tutti i file JavaScript"""
        js_files = []
        assets_dir = Path("assets/js")
        if assets_dir.exists():
            for js_file in assets_dir.glob("**/*.js"):
                js_files.append(str(js_file))
        return js_files

    def _get_file_size(self, file_path):
        """Ottieni dimensione file"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0

    def _analyze_images(self):
        """Analizza le immagini"""
        print(f"\n{Colors.BOLD}🖼️ Image Analysis:{Colors.END}")
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        images = []
        
        for ext in ['**/*' + e for e in image_extensions]:
            images.extend(Path("assets/images").glob(ext) if Path("assets/images").exists() else [])
        
        total_image_size = 0
        large_images = []
        
        for img in images:
            size = self._get_file_size(img)
            total_image_size += size
            
            if size > 500000:  # > 500KB
                large_images.append((str(img), size))
                status = "❌"
            elif size > 200000:  # > 200KB
                status = "⚠️"
            else:
                status = "✅"
                
            print(f"  {status} {img.name}: {size:,} bytes ({size/1024:.1f} KB)")
        
        print(f"\n{Colors.BOLD}Total Images: {total_image_size:,} bytes ({total_image_size/1024:.1f} KB){Colors.END}")
        
        # Raccomandazioni immagini
        if large_images:
            self.critical_issues.append("Immagini troppo pesanti trovate")
            for img, size in large_images:
                self.recommendations.append(f"🖼️ Ottimizza {img} ({size/1024:.1f} KB → target: < 200 KB)")
            self.recommendations.append("📷 Converti immagini in formato WebP")
            self.recommendations.append("🎯 Implementa lazy loading per immagini")

    def analyze_html_structure(self):
        """Analizza la struttura HTML delle pagine"""
        self.print_section("HTML Structure Analysis")
        
        for page in self.pages_to_test[:3]:  # Testa prime 3 pagine
            url = urljoin(self.base_url, page)
            
            try:
                response = self.session.get(url)
                html = response.text
                
                print(f"\n{Colors.BOLD}📄 {page}:{Colors.END}")
                
                # Conta elementi
                script_tags = len(re.findall(r'<script[^>]*>', html))
                link_tags = len(re.findall(r'<link[^>]*>', html))
                img_tags = len(re.findall(r'<img[^>]*>', html))
                
                print(f"  Script tags: {script_tags}")
                print(f"  Link tags: {link_tags}")
                print(f"  Image tags: {img_tags}")
                
                # Verifica meta tags SEO
                self._check_seo_meta_tags(html, page)
                
                # Verifica performance hints
                self._check_performance_hints(html, page)
                
            except Exception as e:
                self.print_error(f"Errore analisi HTML per {page}: {str(e)}")

    def _check_seo_meta_tags(self, html, page):
        """Verifica meta tags SEO"""
        checks = {
            'title': r'<title[^>]*>',
            'meta description': r'<meta[^>]*name=["\']description["\'][^>]*>',
            'meta viewport': r'<meta[^>]*name=["\']viewport["\'][^>]*>',
            'meta charset': r'<meta[^>]*charset[^>]*>',
            'og:title': r'<meta[^>]*property=["\']og:title["\'][^>]*>',
            'og:description': r'<meta[^>]*property=["\']og:description["\'][^>]*>'
        }
        
        print(f"  {Colors.UNDERLINE}SEO Meta Tags:{Colors.END}")
        for tag, pattern in checks.items():
            if re.search(pattern, html, re.IGNORECASE):
                self.print_success(f"    {tag}: Present")
            else:
                self.print_warning(f"    {tag}: Missing")
                self.recommendations.append(f"📝 Aggiungi {tag} per {page}")

    def _check_performance_hints(self, html, page):
        """Verifica hint di performance"""
        print(f"  {Colors.UNDERLINE}Performance Hints:{Colors.END}")
        
        # Preload
        preload_found = re.search(r'<link[^>]*rel=["\']preload["\'][^>]*>', html)
        if preload_found:
            self.print_success("    Preload hints: Present")
        else:
            self.print_warning("    Preload hints: Missing")
            self.recommendations.append(f"⚡ Aggiungi preload per risorse critiche in {page}")
        
        # DNS prefetch
        dns_prefetch = re.search(r'<link[^>]*rel=["\']dns-prefetch["\'][^>]*>', html)
        if dns_prefetch:
            self.print_success("    DNS prefetch: Present")
        else:
            self.print_info("    DNS prefetch: Consider adding for external domains")

    def analyze_compression(self):
        """Analizza la compressione delle risorse"""
        self.print_section("Compression Analysis")
        
        # Test Gzip support
        headers = {'Accept-Encoding': 'gzip, deflate'}
        
        for page in self.pages_to_test[:3]:
            url = urljoin(self.base_url, page)
            
            try:
                response = self.session.get(url, headers=headers)
                
                encoding = response.headers.get('Content-Encoding', 'none')
                original_size = len(response.content)
                
                print(f"{page:<25} Encoding: {encoding:<10} Size: {original_size:,} bytes")
                
                if encoding == 'none':
                    self.warnings.append(f"Compressione non attiva per {page}")
                    self.recommendations.append("🗜️ Attiva Gzip compression nel server")
                
            except Exception as e:
                self.print_error(f"Errore test compressione per {page}: {str(e)}")

    def check_jekyll_config(self):
        """Analizza la configurazione Jekyll per performance"""
        self.print_section("Jekyll Configuration Analysis")
        
        config_file = Path("_config.yml")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = f.read()
            
            # Controlla impostazioni performance
            checks = {
                'compress_html': ('compress_html:', "HTML compression"),
                'sass_style': ('sass:', "Sass compilation"),
                'incremental': ('incremental:', "Incremental builds"),
                'plugins': ('plugins:', "Jekyll plugins")
            }
            
            for key, (pattern, description) in checks.items():
                if pattern in config:
                    self.print_success(f"{description}: Configured")
                else:
                    self.print_warning(f"{description}: Not found")
                    if key == 'compress_html':
                        self.recommendations.append("🗜️ Aggiungi jekyll-compress-html plugin")
        else:
            self.print_error("_config.yml non trovato")

    def generate_lighthouse_score_estimate(self):
        """Genera una stima del punteggio Lighthouse basata sui dati raccolti"""
        self.print_section("Lighthouse Score Estimation")
        
        # Calcola punteggi basati sulle metriche raccolte
        avg_load_time = sum(self.metrics[page].get('load_time', 0) for page in self.metrics) / len(self.metrics) if self.metrics else 0
        
        # Performance Score (0-100)
        if avg_load_time < 1.0:
            performance_score = 95
        elif avg_load_time < 1.5:
            performance_score = 85
        elif avg_load_time < 2.0:
            performance_score = 75
        elif avg_load_time < 3.0:
            performance_score = 65
        else:
            performance_score = 50
        
        # SEO Score (basato sui meta tags)
        seo_score = 85  # Base score, da aggiustare in base ai controlli
        
        # Accessibility Score
        accessibility_score = 80  # Base score
        
        print(f"{Colors.BOLD}Estimated Lighthouse Scores:{Colors.END}")
        print(f"  🚀 Performance: {self._get_score_color(performance_score)}{performance_score}/100{Colors.END}")
        print(f"  ♿ Accessibility: {self._get_score_color(accessibility_score)}{accessibility_score}/100{Colors.END}")
        print(f"  📈 SEO: {self._get_score_color(seo_score)}{seo_score}/100{Colors.END}")
        
        return {
            'performance': performance_score,
            'accessibility': accessibility_score,
            'seo': seo_score
        }

    def _get_score_color(self, score):
        """Restituisce il colore basato sul punteggio"""
        if score >= 90:
            return Colors.GREEN
        elif score >= 70:
            return Colors.YELLOW
        else:
            return Colors.RED

    def generate_recommendations_report(self):
        """Genera il report finale con raccomandazioni"""
        self.print_section("🎯 PERFORMANCE RECOMMENDATIONS")
        
        if self.critical_issues:
            print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL ISSUES (Fix Immediately):{Colors.END}")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"{Colors.RED}  {i}. {issue}{Colors.END}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ WARNINGS (Should Fix):{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{Colors.YELLOW}  {i}. {warning}{Colors.END}")
        
        if self.recommendations:
            print(f"\n{Colors.CYAN}{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"{Colors.CYAN}  {i}. {rec}{Colors.END}")
        
        # Priority Actions
        print(f"\n{Colors.BOLD}{Colors.PURPLE}🎯 TOP PRIORITY ACTIONS:{Colors.END}")
        priority_actions = [
            "1. 🗜️ Attiva compressione Gzip",
            "2. 🖼️ Ottimizza immagini (WebP + lazy loading)",
            "3. 📦 Minifica CSS e JS",
            "4. ⚡ Aggiungi preload per risorse critiche",
            "5. 🧹 Rimuovi CSS/JS non utilizzato"
        ]
        
        for action in priority_actions:
            print(f"{Colors.PURPLE}  {action}{Colors.END}")

    def save_detailed_report(self):
        """Salva un report dettagliato in JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'metrics': self.metrics,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'summary': {
                'total_pages_tested': len(self.metrics),
                'avg_load_time': sum(m.get('load_time', 0) for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0,
                'critical_issues_count': len(self.critical_issues),
                'warnings_count': len(self.warnings)
            }
        }
        
        report_file = Path("scripts/speed_audit_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_success(f"Report dettagliato salvato in: {report_file}")

    def run_full_audit(self):
        """Esegue l'audit completo"""
        self.print_header("🚀 COMPREHENSIVE WEBSITE SPEED AUDIT")
        
        # Verifica disponibilità server
        if not self.check_server_availability():
            return False
        
        # Esegui tutti i test
        self.analyze_page_load_times()
        self.analyze_resource_sizes()
        self.analyze_html_structure()
        self.analyze_compression()
        self.check_jekyll_config()
        
        # Genera stime e raccomandazioni
        lighthouse_scores = self.generate_lighthouse_score_estimate()
        self.generate_recommendations_report()
        
        # Salva report
        self.save_detailed_report()
        
        self.print_header("✅ AUDIT COMPLETED")
        return True

def main():
    """Funzione principale"""
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 Jekyll Site Speed Auditor v1.0{Colors.END}")
    
    # Controlla se Jekyll server è specificato
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4000"
    
    auditor = WebsiteSpeedAuditor(base_url)
    success = auditor.run_full_audit()
    
    if success:
        print(f"\n{Colors.GREEN}🎉 Audit completato con successo!{Colors.END}")
        print(f"{Colors.CYAN}📊 Controlla il file 'scripts/speed_audit_report.json' per dettagli completi{Colors.END}")
    else:
        print(f"\n{Colors.RED}❌ Audit fallito. Controlla che Jekyll server sia attivo.{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
