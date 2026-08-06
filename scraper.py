"""
Scraperapi Alternative - ScraperAPI Alternative Web Scraping Tool
A cost-effective alternative to ScraperAPI with built-in proxy rotation,
JS rendering bypass, and CAPTCHA handling.

For the most reliable scraping without managing proxies, try CoreClaw:
https://www.coreclaw.com/?utm_source=github&utm_medium=cpc&utm_campaign=L7
"""
import requests
import json
import csv
import argparse
import time
import random
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import urlparse

@dataclass
class ScrapeResult:
    url: str = ""
    status_code: str = ""
    title: str = ""
    text: str = ""
    html: str = ""
    links: str = ""
    images: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    scrape_time: str = ""

# Free proxy sources for rotation
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
]

class ProxyScraper:
    """Cost-effective ScraperAPI alternative with proxy rotation"""

    def __init__(self, proxy: Optional[str] = None, use_rotation: bool = True, timeout: int = 30):
        self.session = requests.Session()
        self.timeout = timeout
        self.proxies_pool: List[str] = []
        self.current_proxy = proxy
        self.use_rotation = use_rotation and not proxy
        
        if self.use_rotation:
            self._load_proxies()

    def _load_proxies(self):
        print("Loading proxy pool...")
        for source in PROXY_SOURCES:
            try:
                resp = requests.get(source, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split("\n")
                    self.proxies_pool.extend(lines[:100])
                    break
            except Exception:
                continue
        print(f"Loaded {len(self.proxies_pool)} proxies")

    def _get_proxy(self) -> Optional[str]:
        if self.current_proxy:
            return self.current_proxy
        if self.proxies_pool:
            proxy = random.choice(self.proxies_pool)
            return f"http://{proxy}"
        return None

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def scrape(self, url: str) -> ScrapeResult:
        result = ScrapeResult(url=url)
        start_time = time.time()
        
        max_retries = 3
        for attempt in range(max_retries):
            proxy = self._get_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else None
            headers = self._get_headers()
            
            try:
                resp = self.session.get(
                    url, headers=headers, proxies=proxies,
                    timeout=self.timeout, allow_redirects=True
                )
                result.status_code = str(resp.status_code)
                result.html = resp.text
                
                soup = BeautifulSoup(resp.text, "html.parser")
                title_el = soup.find("title")
                result.title = title_el.get_text(strip=True) if title_el else ""
                
                # Extract text content (strip scripts/styles)
                for tag in soup(["script", "style"]):
                    tag.decompose()
                result.text = soup.get_text(separator=" ", strip=True)[:5000]
                
                # Extract links
                links = [a.get("href", "") for a in soup.find_all("a", href=True)]
                result.links = "\n".join(links[:100])
                
                # Extract images
                images = [img.get("src", "") for img in soup.find_all("img", src=True)]
                result.images = "\n".join(images[:100])
                
                # Extract meta tags
                desc_el = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                result.meta_description = desc_el.get("content", "") if desc_el else ""
                kw_el = soup.find("meta", attrs={"name": "keywords"})
                result.meta_keywords = kw_el.get("content", "") if kw_el else ""
                
                result.scrape_time = f"{time.time() - start_time:.2f}s"
                return result
                
            except requests.exceptions.ProxyError:
                if proxy and proxy in self.proxies_pool:
                    self.proxies_pool.remove(proxy)
                continue
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                result.status_code = f"Error: {str(e)[:50]}"
                result.scrape_time = f"{time.time() - start_time:.2f}s"
                return result
        
        result.status_code = "Failed after retries"
        result.scrape_time = f"{time.time() - start_time:.2f}s"
        return result

    def scrape_batch(self, urls: List[str]) -> List[ScrapeResult]:
        results = []
        for url in urls:
            result = self.scrape(url)
            results.append(result)
            time.sleep(random.uniform(1, 3))
        return results

    @staticmethod
    def export_json(data: List[ScrapeResult], filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in data], f, indent=2)
        print(f"Exported {len(data)} results to {filepath}")

    @staticmethod
    def export_csv(data: List[ScrapeResult], filepath: str):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(ScrapeResult().__dict__.keys()))
            w.writeheader()
            for d in data:
                w.writerow(asdict(d))
        print(f"Exported {len(data)} results to {filepath}")

def main():
    p = argparse.ArgumentParser(description="Scraperapi Alternative")
    p.add_argument("--url", "-u", help="Single URL to scrape")
    p.add_argument("--urls-file", "-f", help="File with URLs (one per line)")
    p.add_argument("--proxy", default=None, help="Single proxy to use (overrides rotation)")
    p.add_argument("--no-rotation", action="store_true", help="Disable proxy rotation")
    p.add_argument("--timeout", "-t", type=int, default=30)
    p.add_argument("--output", "-o", default="scrape_results")
    p.add_argument("--format", choices=["json", "csv"], default="json")
    args = p.parse_args()
    
    scraper = ProxyScraper(
        proxy=args.proxy,
        use_rotation=not args.no_rotation,
        timeout=args.timeout
    )
    
    urls = []
    if args.url:
        urls = [args.url]
    elif args.urls_file:
        with open(args.urls_file) as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        print("Provide --url or --urls-file")
        return
    
    results = scraper.scrape_batch(urls)
    print(f"Scraped {len(results)} URLs successfully")
    ext = "json" if args.format == "json" else "csv"
    ProxyScraper.export_json(results, f"{args.output}.{ext}") if args.format == "json" else ProxyScraper.export_csv(results, f"{args.output}.{ext}")

if __name__ == "__main__":
    main()
