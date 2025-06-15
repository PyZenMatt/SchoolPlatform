#!/usr/bin/env python3
"""
Advanced Jekyll Site Performance Analyzer
Analyzes performance, SEO, accessibility, and optimization opportunities
"""

import requests
import time
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import os

class SiteAnalyzer:
    def __init__(self, base_url="http://localhost:4000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "pages": {},
            "global_issues": [],
            "recommendations": []
        }
        
    def analyze_page(self, path, page_name):
        """Analyze a single page comprehensively"""
        url = urljoin(self.base_url, path)
        
        try:
            # Timing
            start_time = time.time()
            response = requests.get(url, timeout=10)
            load_time = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Basic metrics
            content_size = len(response.content)
            html_size = len(response.text)
            
            analysis = {
                "load_time_ms": round(load_time, 2),
                "status_code": response.status_code,
                "content_size": content_size,
                "html_size": html_size,
                "compression_ratio": round((1 - html_size/content_size) * 100, 2) if content_size > 0 else 0
            }
            
            # HTML Analysis
            analysis.update(self._analyze_html_structure(soup))
            
            # Performance Analysis
            analysis.update(self._analyze_performance(soup, response))
            
            # SEO Analysis
            analysis.update(self._analyze_seo(soup))
            
            # Accessibility Analysis
            analysis.update(self._analyze_accessibility(soup))
            
            # Content Analysis
            analysis.update(self._analyze_content(soup))
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_html_structure(self, soup):
        """Analyze HTML structure and best practices"""
        analysis = {}
        
        # Document structure
        analysis["has_doctype"] = str(soup).startswith("<!DOCTYPE")
        analysis["html_lang"] = soup.html.get('lang') if soup.html else None
        analysis["has_viewport"] = bool(soup.find('meta', attrs={'name': 'viewport'}))
        
        # Head analysis
        head = soup.head if soup.head else soup
        analysis["title_length"] = len(head.title.string) if head.title else 0
        analysis["meta_description"] = bool(head.find('meta', attrs={'name': 'description'}))
        
        # Links and resources
        analysis["external_links"] = len([a for a in soup.find_all('a', href=True) 
                                        if a['href'].startswith(('http', '//'))])
        analysis["internal_links"] = len([a for a in soup.find_all('a', href=True) 
                                        if not a['href'].startswith(('http', '//', '#', 'mailto:', 'tel:'))])
        
        return {"html_structure": analysis}
    
    def _analyze_performance(self, soup, response):
        """Analyze performance-related aspects"""
        analysis = {}
        
        # CSS Analysis
        css_links = soup.find_all('link', rel='stylesheet')
        analysis["css_files"] = len(css_links)
        analysis["inline_css"] = len(soup.find_all('style'))
        
        # JavaScript Analysis
        js_scripts = soup.find_all('script', src=True)
        analysis["js_files"] = len(js_scripts)
        analysis["inline_js"] = len(soup.find_all('script', src=False))
        
        # Image Analysis
        images = soup.find_all('img')
        analysis["total_images"] = len(images)
        analysis["images_with_alt"] = len([img for img in images if img.get('alt')])
        analysis["images_with_lazy"] = len([img for img in images if 'lazy' in str(img.get('loading', ''))])
        analysis["images_without_dimensions"] = len([img for img in images 
                                                   if not (img.get('width') and img.get('height'))])
        
        # Resource hints
        analysis["preload_links"] = len(soup.find_all('link', rel='preload'))
        analysis["prefetch_links"] = len(soup.find_all('link', rel='prefetch'))
        analysis["dns_prefetch"] = len(soup.find_all('link', rel='dns-prefetch'))
        
        # Headers analysis
        headers = dict(response.headers)
        analysis["gzip_enabled"] = 'gzip' in headers.get('content-encoding', '')
        analysis["cache_control"] = headers.get('cache-control', 'none')
        analysis["has_etag"] = 'etag' in headers
        
        return {"performance": analysis}
    
    def _analyze_seo(self, soup):
        """Analyze SEO factors"""
        analysis = {}
        
        # Title and meta
        title = soup.title
        analysis["title"] = title.string.strip() if title else None
        analysis["title_length"] = len(analysis["title"]) if analysis["title"] else 0
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        analysis["meta_description"] = meta_desc.get('content') if meta_desc else None
        analysis["meta_desc_length"] = len(analysis["meta_description"]) if analysis["meta_description"] else 0
        
        # Headings structure
        headings = {}
        for i in range(1, 7):
            headings[f"h{i}"] = len(soup.find_all(f'h{i}'))
        analysis["headings"] = headings
        
        # Structured data
        analysis["json_ld"] = len(soup.find_all('script', type='application/ld+json'))
        analysis["microdata"] = len(soup.find_all(attrs={'itemtype': True}))
        
        # Open Graph
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        analysis["open_graph_tags"] = len(og_tags)
        
        # Twitter Cards
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
        analysis["twitter_cards"] = len(twitter_tags)
        
        return {"seo": analysis}
    
    def _analyze_accessibility(self, soup):
        """Analyze accessibility factors"""
        analysis = {}
        
        # Images
        images = soup.find_all('img')
        analysis["images_total"] = len(images)
        analysis["images_with_alt"] = len([img for img in images if img.get('alt')])
        analysis["images_missing_alt"] = analysis["images_total"] - analysis["images_with_alt"]
        
        # Forms
        inputs = soup.find_all('input')
        analysis["form_inputs"] = len(inputs)
        analysis["inputs_with_labels"] = len([inp for inp in inputs 
                                            if inp.get('id') and soup.find('label', attrs={'for': inp.get('id')})])
        
        # Links
        links = soup.find_all('a')
        analysis["total_links"] = len(links)
        analysis["links_without_text"] = len([a for a in links if not a.get_text().strip()])
        
        # ARIA
        analysis["aria_labels"] = len(soup.find_all(attrs={'aria-label': True}))
        analysis["aria_describedby"] = len(soup.find_all(attrs={'aria-describedby': True}))
        
        # Semantic HTML
        semantic_tags = ['main', 'header', 'footer', 'nav', 'section', 'article', 'aside']
        analysis["semantic_elements"] = {tag: len(soup.find_all(tag)) for tag in semantic_tags}
        
        return {"accessibility": analysis}
    
    def _analyze_content(self, soup):
        """Analyze content quality and structure"""
        analysis = {}
        
        # Text content
        text_content = soup.get_text()
        words = text_content.split()
        analysis["word_count"] = len(words)
        analysis["character_count"] = len(text_content)
        
        # Reading level (simple approximation)
        sentences = text_content.count('.') + text_content.count('!') + text_content.count('?')
        analysis["estimated_sentences"] = sentences
        analysis["avg_words_per_sentence"] = round(len(words) / max(sentences, 1), 2)
        
        # Content structure
        paragraphs = soup.find_all('p')
        analysis["paragraphs"] = len(paragraphs)
        analysis["avg_words_per_paragraph"] = round(len(words) / max(len(paragraphs), 1), 2)
        
        # Lists
        analysis["ordered_lists"] = len(soup.find_all('ol'))
        analysis["unordered_lists"] = len(soup.find_all('ul'))
        analysis["list_items"] = len(soup.find_all('li'))
        
        return {"content": analysis}
    
    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        for page_name, data in self.results["pages"].items():
            if "error" in data:
                continue
                
            page_recs = []
            
            # Performance recommendations
            perf = data.get("performance", {})
            if perf.get("css_files", 0) > 5:
                page_recs.append("🎨 Consider combining CSS files to reduce HTTP requests")
            if perf.get("js_files", 0) > 5:
                page_recs.append("📜 Consider combining JavaScript files")
            if perf.get("images_without_dimensions", 0) > 0:
                page_recs.append("📐 Add width/height to images to prevent layout shift")
            if perf.get("images_with_lazy", 0) == 0 and perf.get("total_images", 0) > 3:
                page_recs.append("⚡ Implement lazy loading for images")
            
            # SEO recommendations  
            seo = data.get("seo", {})
            if seo.get("title_length", 0) > 60:
                page_recs.append("📝 Title tag too long (>60 chars) - may be truncated in search results")
            if seo.get("meta_desc_length", 0) > 160:
                page_recs.append("📝 Meta description too long (>160 chars)")
            if seo.get("meta_desc_length", 0) == 0:
                page_recs.append("❌ Missing meta description")
            if seo.get("open_graph_tags", 0) == 0:
                page_recs.append("📱 Add Open Graph tags for better social sharing")
            
            # Accessibility recommendations
            acc = data.get("accessibility", {})
            if acc.get("images_missing_alt", 0) > 0:
                page_recs.append(f"♿ {acc['images_missing_alt']} images missing alt text")
            if acc.get("links_without_text", 0) > 0:
                page_recs.append(f"🔗 {acc['links_without_text']} links without descriptive text")
            
            # Content recommendations
            content = data.get("content", {})
            if content.get("word_count", 0) < 300:
                page_recs.append("📝 Consider adding more content (current: <300 words)")
            if content.get("avg_words_per_sentence", 0) > 25:
                page_recs.append("✏️ Consider shorter sentences for better readability")
            
            if page_recs:
                recommendations.append({
                    "page": page_name,
                    "recommendations": page_recs
                })
        
        return recommendations
    
    def run_full_analysis(self):
        """Run complete site analysis"""
        print("🔍 Advanced Jekyll Site Analysis")
        print("=" * 80)
        
        pages_to_test = [
            ("/", "Homepage"),
            ("/eng/features/", "Features EN"),
            ("/ita/features/", "Features IT"),
            ("/eng/technology/", "Technology EN"),
            ("/ita/technology/", "Technology IT"),
            ("/eng/invest/", "Invest EN"),
            ("/ita/invest/", "Invest IT"),
            ("/eng/roadmap/", "Roadmap EN"),
            ("/ita/roadmap/", "Roadmap IT"),
            ("/eng/tokenomics/", "Tokenomics EN"),
            ("/ita/tokenomics/", "Tokenomics IT")
        ]
        
        for path, name in pages_to_test:
            print(f"📄 Analyzing {name}...")
            self.results["pages"][name] = self.analyze_page(path, name)
        
        # Generate recommendations
        self.results["recommendations"] = self.generate_recommendations()
        
        # Print summary
        self._print_summary()
        
        # Save detailed report
        self._save_report()
    
    def _print_summary(self):
        """Print analysis summary"""
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 80)
        
        successful_pages = [name for name, data in self.results["pages"].items() 
                           if "error" not in data]
        failed_pages = [name for name, data in self.results["pages"].items() 
                       if "error" in data]
        
        print(f"✅ Successfully analyzed: {len(successful_pages)}/{len(self.results['pages'])}")
        if failed_pages:
            print(f"❌ Failed pages: {', '.join(failed_pages)}")
        
        if successful_pages:
            # Performance summary
            avg_load_time = sum(self.results["pages"][page]["load_time_ms"] 
                              for page in successful_pages) / len(successful_pages)
            avg_size = sum(self.results["pages"][page]["content_size"] 
                          for page in successful_pages) / len(successful_pages)
            
            print(f"\n⚡ Average load time: {avg_load_time:.1f}ms")
            print(f"📦 Average page size: {avg_size/1024:.1f}KB")
            
            # SEO summary
            pages_with_meta_desc = sum(1 for page in successful_pages 
                                     if self.results["pages"][page].get("seo", {}).get("meta_description"))
            print(f"🔍 Pages with meta description: {pages_with_meta_desc}/{len(successful_pages)}")
            
            # Accessibility summary
            total_images = sum(self.results["pages"][page].get("accessibility", {}).get("images_total", 0) 
                             for page in successful_pages)
            images_with_alt = sum(self.results["pages"][page].get("accessibility", {}).get("images_with_alt", 0) 
                                for page in successful_pages)
            if total_images > 0:
                alt_percentage = (images_with_alt / total_images) * 100
                print(f"♿ Images with alt text: {alt_percentage:.1f}% ({images_with_alt}/{total_images})")
        
        # Print recommendations
        if self.results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 80)
            for page_rec in self.results["recommendations"]:
                print(f"\n📄 {page_rec['page']}:")
                for rec in page_rec["recommendations"]:
                    print(f"   {rec}")
        else:
            print(f"\n🎉 No major issues found! Your site is well optimized.")
    
    def _save_report(self):
        """Save detailed analysis report"""
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"reports/detailed-analysis-{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {filename}")

if __name__ == "__main__":
    analyzer = SiteAnalyzer()
    analyzer.run_full_analysis()
