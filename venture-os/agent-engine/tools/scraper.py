# Web scraping tool
import json
import re
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScrapedContent:
    """Scraped content from a page."""

    url: str
    title: str
    text: str
    html: str
    links: List[str]
    images: List[str]
    metadata: Dict[str, Any]
    scraped_at: datetime


@dataclass
class ScrapedElement:
    """A scraped HTML element."""

    tag: str
    text: str
    html: str
    attributes: Dict[str, str]
    children: List["ScrapedElement"]


class Scraper:
    """Web scraping tool."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._session = None
        self._default_headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (compatible; VentureOS/1.0)"
        }
        self._rate_limit: float = 1.0  # seconds between requests
        self._request_history: List[Dict[str, Any]] = []
        self._stats: Dict[str, Any] = {"requests": 0, "errors": 0}
        self._cookies: Dict[str, str] = {}
        self._last_request_time: float = 0.0
        self._timeout: int = 30
        self._proxy: Optional[str] = None

    # ==================== Private Helpers ====================

    def _enforce_rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request_time = time.time()

    def _fetch(self, url: str) -> str:
        """Fetch URL and return HTML text."""
        import httpx

        self._enforce_rate_limit()
        proxies = {"http://": self._proxy, "https://": self._proxy} if self._proxy else None
        try:
            with httpx.Client(
                headers=self._default_headers,
                cookies=self._cookies,
                timeout=self._timeout,
                follow_redirects=True,
                **(dict(proxies=proxies) if proxies else {}),
            ) as client:
                resp = client.get(url)
                resp.raise_for_status()
                self._stats["requests"] = int(self._stats["requests"]) + 1
                self._request_history.append(
                    {"url": url, "status": resp.status_code, "timestamp": datetime.utcnow().isoformat()}
                )
                return resp.text
        except Exception as exc:
            self._stats["errors"] = int(self._stats["errors"]) + 1
            self._request_history.append(
                {"url": url, "error": str(exc), "timestamp": datetime.utcnow().isoformat()}
            )
            raise

    def _parse(self, html: str) -> Any:
        """Parse HTML, using BeautifulSoup if available else stdlib."""
        try:
            from bs4 import BeautifulSoup  # type: ignore[import]
            return BeautifulSoup(html, "html.parser")
        except ImportError:
            from html.parser import HTMLParser

            class _SimpleParser(HTMLParser):
                """Minimal parser — wraps raw HTML for fallback."""
                def __init__(self) -> None:
                    super().__init__()
                    self._html = ""

                def handle_data(self, data: str) -> None:
                    self._html += data

                @property
                def text(self) -> str:
                    return self._html

            p = _SimpleParser()
            p.feed(html)
            p._html_raw = html  # type: ignore[attr-defined]
            return p

    def _elem_to_scraped(self, tag: Any, html_str: str = "") -> "ScrapedElement":
        """Convert bs4 tag to ScrapedElement."""
        try:
            return ScrapedElement(
                tag=tag.name or "",
                text=tag.get_text(separator=" ", strip=True),
                html=str(tag),
                attributes=dict(tag.attrs) if tag.attrs else {},
                children=[],
            )
        except Exception:
            return ScrapedElement(tag="", text="", html=html_str, attributes={}, children=[])

    # ==================== Configuration ====================


    def set_user_agent(self, user_agent: str) -> None:
        """Set user agent string."""
        self._default_headers["User-Agent"] = user_agent

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers."""
        self._default_headers.update(headers)

    def add_header(self, key: str, value: str) -> None:
        """Add a header."""
        self._default_headers[key] = value

    def set_rate_limit(self, seconds: float) -> None:
        """Set rate limit between requests."""
        self._rate_limit = max(0.0, seconds)

    def set_timeout(self, timeout: int) -> None:
        """Set request timeout."""
        self._timeout = timeout

    def set_proxy(self, proxy_url: str) -> None:
        """Set proxy for requests."""
        self._proxy = proxy_url

    # ==================== Basic Scraping ====================

    def scrape(self, url: str) -> ScrapedContent:
        """Scrape a URL and return content."""
        html = self._fetch(url)
        soup = self._parse(html)
        title = ""
        try:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""
        except Exception:
            pass
        text = self.clean_text(self.remove_scripts(self.remove_styles(html)))
        try:
            links = [a.get("href", "") for a in soup.find_all("a", href=True)]
            links = [l for l in links if l.startswith("http")]
        except Exception:
            links = []
        try:
            images = [img.get("src", "") for img in soup.find_all("img", src=True)]
        except Exception:
            images = []
        return ScrapedContent(
            url=url,
            title=title,
            text=text,
            html=html,
            links=links,
            images=images,
            metadata={},
            scraped_at=datetime.utcnow(),
        )

    def scrape_text(self, url: str) -> str:
        """Scrape and return text content only."""
        html = self._fetch(url)
        return self.clean_text(self.remove_scripts(self.remove_styles(html)))

    def scrape_html(self, url: str) -> str:
        """Scrape and return raw HTML."""
        return self._fetch(url)

    def scrape_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        """Scrape multiple URLs."""
        results = []
        for url in urls:
            try:
                results.append(self.scrape(url))
            except Exception:
                pass
        return results

    def scrape_with_js(
        self, url: str, wait_for: Optional[str] = None
    ) -> ScrapedContent:
        """Scrape page with JavaScript rendering."""
        raise NotImplementedError(
            "JavaScript rendering requires playwright: pip install playwright"
        )

    # ==================== Element Selection ====================

    def select(self, url: str, selector: str) -> List[ScrapedElement]:
        """Select elements by CSS selector."""
        html = self._fetch(url)
        soup = self._parse(html)
        try:
            return [self._elem_to_scraped(tag) for tag in soup.select(selector)]
        except Exception:
            return []

    def select_one(self, url: str, selector: str) -> Optional[ScrapedElement]:
        """Select single element by CSS selector."""
        elems = self.select(url, selector)
        return elems[0] if elems else None

    def select_by_xpath(self, url: str, xpath: str) -> List[ScrapedElement]:
        """Select elements by XPath."""
        try:
            from lxml import etree  # type: ignore[import]
            html = self._fetch(url)
            tree = etree.fromstring(html.encode(), etree.HTMLParser())
            matches = tree.xpath(xpath)
            return [
                ScrapedElement(
                    tag=el.tag if hasattr(el, "tag") else "",
                    text=(el.text or "").strip() if hasattr(el, "text") else str(el),
                    html="",
                    attributes=dict(el.attrib) if hasattr(el, "attrib") else {},
                    children=[],
                )
                for el in matches
            ]
        except ImportError:
            raise NotImplementedError("XPath selection requires lxml: pip install lxml")

    def select_by_id(self, url: str, element_id: str) -> Optional[ScrapedElement]:
        """Select element by ID."""
        return self.select_one(url, f"#{element_id}")

    def select_by_class(self, url: str, class_name: str) -> List[ScrapedElement]:
        """Select elements by class name."""
        return self.select(url, f".{class_name}")

    def select_by_tag(self, url: str, tag_name: str) -> List[ScrapedElement]:
        """Select elements by tag name."""
        return self.select(url, tag_name)

    # ==================== Data Extraction ====================

    def extract_links(self, url: str, pattern: Optional[str] = None) -> List[str]:
        """Extract links from page."""
        html = self._fetch(url)
        soup = self._parse(html)
        try:
            hrefs = [a.get("href", "") for a in soup.find_all("a", href=True)]
        except Exception:
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        links = [h for h in hrefs if h.startswith("http")]
        if pattern:
            links = [l for l in links if re.search(pattern, l)]
        return links

    def extract_images(self, url: str) -> List[Dict[str, str]]:
        """Extract image URLs and alt text."""
        html = self._fetch(url)
        soup = self._parse(html)
        try:
            return [
                {"src": img.get("src", ""), "alt": img.get("alt", "")}
                for img in soup.find_all("img")
            ]
        except Exception:
            return [
                {"src": m, "alt": ""}
                for m in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
            ]

    def extract_tables(self, url: str) -> List[List[List[str]]]:
        """Extract tables as nested lists."""
        html = self._fetch(url)
        soup = self._parse(html)
        tables: List[List[List[str]]] = []
        try:
            for table in soup.find_all("table"):
                rows = []
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append(rows)
        except Exception:
            pass
        return tables

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract page metadata (title, description, etc.)."""
        html = self._fetch(url)
        soup = self._parse(html)
        meta: Dict[str, Any] = {}
        try:
            title_tag = soup.find("title")
            if title_tag:
                meta["title"] = title_tag.get_text(strip=True)
            for tag in soup.find_all("meta"):
                name = tag.get("name") or tag.get("property") or ""
                content = tag.get("content", "")
                if name and content:
                    meta[name] = content
        except Exception:
            meta["title"] = re.search(r"<title>([^<]+)</title>", html, re.I)
        return meta

    def extract_structured_data(self, url: str) -> Dict[str, Any]:
        """Extract JSON-LD and schema.org data."""
        html = self._fetch(url)
        items: List[Any] = []
        for match in re.finditer(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.DOTALL | re.IGNORECASE
        ):
            try:
                items.append(json.loads(match.group(1)))
            except Exception:
                pass
        return {"json_ld": items}

    def extract_by_pattern(self, url: str, pattern: str) -> List[str]:
        """Extract content matching regex pattern."""
        html = self._fetch(url)
        return re.findall(pattern, html)

    def extract_text_between(self, url: str, start_marker: str, end_marker: str) -> str:
        """Extract text between markers."""
        html = self._fetch(url)
        start = html.find(start_marker)
        if start == -1:
            return ""
        start += len(start_marker)
        end = html.find(end_marker, start)
        return html[start:end] if end != -1 else html[start:]

    # ==================== Form Interaction ====================

    def get_forms(self, url: str) -> List[Dict[str, Any]]:
        """Get all forms on page."""
        html = self._fetch(url)
        soup = self._parse(html)
        forms: List[Dict[str, Any]] = []
        try:
            for form in soup.find_all("form"):
                fields = []
                for inp in form.find_all(["input", "textarea", "select"]):
                    fields.append({
                        "name": inp.get("name", ""),
                        "type": inp.get("type", inp.name),
                        "value": inp.get("value", ""),
                    })
                forms.append({
                    "action": form.get("action", ""),
                    "method": form.get("method", "get").upper(),
                    "fields": fields,
                })
        except Exception:
            pass
        return forms

    def fill_form(self, url: str, form_selector: str, data: Dict[str, str]) -> str:
        """Fill and submit form, return result page."""
        forms = self.get_forms(url)
        if not forms:
            raise ValueError(f"No forms found at {url}")
        form = forms[0]
        method = form.get("method", "POST")
        action = form.get("action") or url
        return self.submit_form(action, data, method)

    def submit_form(
        self, url: str, form_data: Dict[str, str], method: str = "POST"
    ) -> str:
        """Submit form data."""
        import httpx
        self._enforce_rate_limit()
        with httpx.Client(
            headers=self._default_headers,
            cookies=self._cookies,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            if method.upper() == "POST":
                resp = client.post(url, data=form_data)
            else:
                resp = client.get(url, params=form_data)
            resp.raise_for_status()
            self._stats["requests"] = int(self._stats["requests"]) + 1
            return resp.text

    # ==================== Pagination ====================

    def scrape_paginated(
        self, start_url: str, next_selector: str, max_pages: int = 10
    ) -> List[ScrapedContent]:
        """Scrape paginated content."""
        results = []
        url: Optional[str] = start_url
        visited = set()
        while url and len(results) < max_pages and url not in visited:
            try:
                content = self.scrape(url)
                results.append(content)
                visited.add(url)
                html = content.html
                soup = self._parse(html)
                next_tag = soup.select_one(next_selector)
                url = next_tag.get("href") if next_tag else None
            except Exception:
                break
        return results

    def scrape_infinite_scroll(self, url: str, max_scrolls: int = 10) -> ScrapedContent:
        """Scrape infinite scroll page."""
        raise NotImplementedError(
            "Infinite scroll scraping requires playwright: pip install playwright"
        )

    # ==================== Crawling ====================

    def crawl(
        self, start_url: str, max_depth: int = 2, max_pages: int = 100
    ) -> List[ScrapedContent]:
        """Crawl website starting from URL."""
        results: List[ScrapedContent] = []
        visited: set = set()
        queue: List[tuple] = [(start_url, 0)]
        base = re.match(r"https?://[^/]+", start_url)
        base_domain = base.group(0) if base else start_url

        while queue and len(results) < max_pages:
            url, depth = queue.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            try:
                content = self.scrape(url)
                results.append(content)
                if depth < max_depth:
                    for link in content.links:
                        if link.startswith(base_domain) and link not in visited:
                            queue.append((link, depth + 1))
            except Exception:
                pass
        return results

    def crawl_sitemap(self, sitemap_url: str) -> List[str]:
        """Extract URLs from sitemap."""
        html = self._fetch(sitemap_url)
        return re.findall(r"<loc>([^<]+)</loc>", html)

    def follow_links(
        self, url: str, link_pattern: str, max_links: int = 10
    ) -> List[ScrapedContent]:
        """Follow and scrape matching links."""
        links = self.extract_links(url, pattern=link_pattern)
        return self.scrape_multiple(links[:max_links])

    # ==================== Content Processing ====================

    def clean_text(self, text: str) -> str:
        """Clean scraped text."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        text = re.sub(r"[\r\n\t]+", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def remove_scripts(self, html: str) -> str:
        """Remove script tags from HTML."""
        return re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)

    def remove_styles(self, html: str) -> str:
        """Remove style tags from HTML."""
        return re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

    def html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown (basic regex-based)."""
        md = html
        # Headings
        for i in range(6, 0, -1):
            md = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", "#" * i + r" \1\n", md, flags=re.IGNORECASE | re.DOTALL)
        # Bold / italic
        md = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", md, flags=re.IGNORECASE | re.DOTALL)
        # Links
        md = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", md, flags=re.IGNORECASE | re.DOTALL)
        # Images
        md = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>',
                    r"![\2](\1)", md, flags=re.IGNORECASE)
        md = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*/?>',
                    r"![](\1)", md, flags=re.IGNORECASE)
        # Lists
        md = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"</?[uo]l[^>]*>", "", md, flags=re.IGNORECASE)
        # Paragraphs and line breaks
        md = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<br\s*/?>", "\n", md, flags=re.IGNORECASE)
        # Strip remaining tags
        md = re.sub(r"<[^>]+>", "", md)
        # Collapse whitespace
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip()

    def parse_html(self, html: str) -> Any:
        """Parse HTML string."""
        return self._parse(html)

    # ==================== Error Handling ====================

    def handle_captcha(self, url: str, captcha_selector: str) -> Optional[str]:
        """Handle captcha (placeholder for integration)."""
        return None  # Requires manual or third-party CAPTCHA solving

    def retry_on_failure(
        self, url: str, max_retries: int = 3
    ) -> Optional[ScrapedContent]:
        """Retry scraping on failure."""
        for attempt in range(max_retries):
            try:
                return self.scrape(url)
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def get_error_pages(self) -> List[Dict[str, Any]]:
        """Get list of failed scrapes."""
        return [r for r in self._request_history if "error" in r]

    # ==================== Session Management ====================

    def create_session(self) -> None:
        """Create persistent session."""
        import httpx
        self._session = httpx.Client(
            headers=self._default_headers,
            cookies=self._cookies,
            timeout=self._timeout,
            follow_redirects=True,
        )

    def close_session(self) -> None:
        """Close session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def save_cookies(self, filepath: str) -> bool:
        """Save session cookies."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._cookies, f)
        return True

    def load_cookies(self, filepath: str) -> bool:
        """Load session cookies."""
        with open(filepath, "r", encoding="utf-8") as f:
            self._cookies = json.load(f)
        return True

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            "total_requests": self._stats["requests"],
            "errors": self._stats["errors"],
            "history_count": len(self._request_history),
        }

    def get_request_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get request history."""
        return self._request_history[-limit:]

    def clear_history(self) -> None:
        """Clear request history."""
        self._request_history.clear()
        self._stats = {"requests": 0, "errors": 0}
