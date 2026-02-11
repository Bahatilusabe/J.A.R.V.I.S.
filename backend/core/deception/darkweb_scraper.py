"""
Dark-web / OSINT fetcher (ethical, non-actionable).

This module provides a safe wrapper for fetching publicly available
resources for OSINT and research. It explicitly refuses to access
`.onion` or other darknet-only addresses and will not instruct how to
use Tor or other anonymizing networks.

The implementation uses `requests` if available, falling back to
`urllib.request`. It provides simple parsing helpers for extracting
email addresses, IPv4s, and domain names from text blobs.

Do NOT use this module to facilitate illegal activity. Use it only on
resources you are permitted to access.
"""
from __future__ import annotations

import logging
import re
import json
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# Simple regexes for lightweight parsing
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_IPV4_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
_DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.I)


class DarkWebScraper:
    """Safe fetcher and processor for publicly-available OSINT resources.

    Safety constraints (by design):
    - `.onion` URLs are rejected and not fetched.
    - No instructions or automation to run Tor or connect to darknet services
      are provided.
    - Parsing may surface indicators (emails, domains, ips) but will not
      automatically follow or expand darknet-only links.

    Integrations:
    - BeautifulSoup (bs4) for HTML parsing if installed (lazy import).
    - MindNLP: optional summarization/analyzer if a package named
      `mindnlp` (or similar) is installed; otherwise a conservative
      fallback summarizer is used.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        # Lazy import of requests to avoid hard dependency
        try:
            import requests  # type: ignore

            self._requests = requests
        except Exception:
            self._requests = None

        # lazy imports for bs4 and MindNLP-like API
        self._bs4 = None
        self._mindnlp = None

    def _is_forbidden(self, url: str) -> bool:
        # Refuse .onion and other darknet-only schemes
        if ".onion" in url.lower():
            return True
        return False

    def fetch(self, url: str) -> Optional[str]:
        """Fetch a URL and return its text, or None if forbidden or failed.

        Returns None if the URL is a darknet address or if fetching failed.
        """
        if self._is_forbidden(url):
            logger.warning("Refusing to fetch darknet URL: %s", url)
            return None
        try:
            if self._requests:
                r = self._requests.get(url, timeout=self.timeout)
                r.raise_for_status()
                return r.text
            else:
                # fallback to urllib
                from urllib.request import urlopen

                with urlopen(url, timeout=self.timeout) as fh:
                    return fh.read().decode("utf-8", errors="replace")
        except Exception as exc:
            logger.debug("Failed to fetch %s: %s", url, exc)
            return None

    def fetch_many(self, urls: Iterable[str]) -> Dict[str, Optional[str]]:
        """Fetch multiple URLs and return a mapping url -> text|None."""
        results: Dict[str, Optional[str]] = {}
        for u in urls:
            results[u] = self.fetch(u)
        return results

    def _ensure_bs4(self):
        if self._bs4 is None:
            try:
                from bs4 import BeautifulSoup  # type: ignore

                self._bs4 = BeautifulSoup
            except Exception:
                self._bs4 = None

    def _ensure_mindnlp(self):
        if self._mindnlp is None:
            try:
                import mindnlp  # type: ignore

                self._mindnlp = mindnlp
            except Exception:
                self._mindnlp = None

    def parse_basic_indicators(self, text: str) -> Dict[str, List[str]]:
        """Parse a text blob for simple indicators (emails, ipv4, domains).

        This function is intentionally conservative and returns unique
        matches only.
        """
        emails = sorted(set(_EMAIL_RE.findall(text)))
        ips = sorted(set(_IPV4_RE.findall(text)))
        domains = sorted(set(_DOMAIN_RE.findall(text)))
        return {"emails": emails, "ipv4": ips, "domains": domains}

    def process_html(self, html: str) -> Dict[str, object]:
        """Extract text, links and basic metadata from HTML using BeautifulSoup.

        Returns a dict: {"text": str, "links": [str], "title": Optional[str]}.
        If BeautifulSoup is not installed, falls back to a naive text extraction.
        """
        self._ensure_bs4()
        if self._bs4:
            soup = self._bs4(html, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            # extract visible text
            for s in soup(['script', 'style', 'noscript']):
                s.extract()
            text = soup.get_text(separator=' ', strip=True)
            links = []
            for a in soup.find_all('a', href=True):
                links.append(a['href'])
            return {"text": text, "links": links, "title": title}
        else:
            # naive fallback: strip tags
            text = re.sub(r'<[^>]+>', ' ', html)
            return {"text": text, "links": [], "title": None}

    def analyze_text(self, text: str, max_sentences: int = 3) -> Dict[str, object]:
        """Analyze and summarize text using MindNLP if available, else fallback.

        Returns a dict with keys: summary, indicators (emails/domains/ips).
        """
        self._ensure_mindnlp()
        summary = None
        if self._mindnlp:
            try:
                # Hypothetical MindNLP API: mindnlp.summarize(text, max_sentences=...)
                summary = getattr(self._mindnlp, 'summarize', lambda t, **kw: None)(text, max_sentences=max_sentences)
            except Exception:
                logger.debug("MindNLP summarization failed, falling back")
                summary = None

        if not summary:
            # conservative extractive fallback: pick sentences with most keyword overlap
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if not sentences:
                summary = ''
            else:
                # score by number of alpha words
                scored = [(len(re.findall(r"\w+", s)), i, s) for i, s in enumerate(sentences)]
                scored.sort(reverse=True)
                top = [s for _, _, s in scored[:max_sentences]]
                summary = ' '.join(top).strip()

        indicators = self.parse_basic_indicators(text)
        return {"summary": summary, "indicators": indicators}

    def analyze_and_report(self, text: str, manager=None, metric_prefix: str = "darkweb") -> Dict[str, object]:
        """Analyze `text`, optionally record a simulated interaction in `manager`,
        and emit lightweight metrics via `utils.metrics.increment` if present.

        Safety: this function only records in-memory simulation state (via
        `HoneypotManager.record_interaction`) and calls a minimal metrics
        increment function if available. It does not perform network calls.
        """
        result = self.analyze_text(text)

        # Emit telemetry/metrics if available (non-fatal)
        try:
            from backend.utils import metrics as _metrics

            def _inc(n: str, v: int = 1):
                try:
                    _metrics.increment(n, v)
                except Exception:
                    # metrics stub or failing backend should not break analysis
                    logger.debug("metrics.increment failed for %s", n)
        except Exception:
            _inc = lambda n, v=1: None

        inds = result.get("indicators", {})
        num_emails = len(inds.get("emails", []))
        num_ips = len(inds.get("ipv4", []))
        num_domains = len(inds.get("domains", []))

        try:
            _inc(f"{metric_prefix}.indicators.emails", num_emails)
            _inc(f"{metric_prefix}.indicators.ipv4", num_ips)
            _inc(f"{metric_prefix}.indicators.domains", num_domains)
            _inc(f"{metric_prefix}.summary.generated", 1)
        except Exception:
            logger.debug("metrics emission failed")

        # If a HoneypotManager-like object is given, record a simulated event.
        if manager is not None:
            try:
                summary = (result.get("summary") or "")[:240]
                notes = {"indicators": inds}
                # Use a safe, short honeypot name for reporting
                hp_name = getattr(manager, "default_honeypot_name", "darkweb-scraper")
                # manager.record_interaction(honeypot_name, client_ip, client_port, payload_summary, notes)
                manager.record_interaction(hp_name, None, None, f"analysis:{summary}", notes=json.dumps(notes))
            except Exception:
                logger.exception("failed to record analysis into manager")

        # Attempt to send a visualization/telemetry event to Huawei AOM if configured.
        # This is optional and will be a no-op when the integration is not configured.
        try:
            try:
                from backend.integrations.huawei_aom import send_event  # type: ignore
            except Exception:
                send_event = None

            if send_event is not None:
                payload = {
                    "summary": (result.get("summary") or "")[:512],
                    "indicators": inds,
                    "counts": {"emails": num_emails, "ipv4": num_ips, "domains": num_domains},
                    "source": "darkweb_scraper",
                }
                try:
                    send_event("darkweb_alert", payload)
                except Exception:
                    logger.debug("Huawei AOM send_event failed in darkweb_scraper")
        except Exception:
            # keep analyzer fully fault-tolerant
            logger.debug("Error while attempting to send Huawei AOM event")

        return result


__all__ = ["DarkWebScraper"]
