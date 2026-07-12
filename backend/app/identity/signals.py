import logging
from fastapi import Request
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RequestSignals:
    def __init__(
            self,
            ip_address: str,
            user_agent: str,
            endpoint: str,
            method: str,
            timestamp: datetime,
            # 🔥 Enhanced signals for fingerprinting
            accept_language: Optional[str] = None,
            accept_encoding: Optional[str] = None,
            accept: Optional[str] = None,
            sec_ch_ua: Optional[str] = None,
            sec_ch_ua_platform: Optional[str] = None,
            sec_ch_ua_platform_version: Optional[str] = None,
            sec_ch_ua_arch: Optional[str] = None,
            sec_ch_ua_bitness: Optional[str] = None,
            sec_ch_ua_full_version: Optional[str] = None,
            sec_ch_ua_mobile: Optional[str] = None,
            sec_ch_ua_model: Optional[str] = None,
            sec_fetch_dest: Optional[str] = None,
            sec_fetch_mode: Optional[str] = None,
            sec_fetch_site: Optional[str] = None,
            origin: Optional[str] = None,
            referer: Optional[str] = None,
            dnt: Optional[str] = None,
            connection: Optional[str] = None,
            cache_control: Optional[str] = None,
            timezone: Optional[str] = None,
            screen_resolution: Optional[str] = None,
            color_depth: Optional[str] = None,
    ):
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.endpoint = endpoint
        self.method = method
        self.timestamp = timestamp
        
        # Enhanced signals
        self.accept_language = accept_language
        self.accept_encoding = accept_encoding
        self.accept = accept
        self.sec_ch_ua = sec_ch_ua
        self.sec_ch_ua_platform = sec_ch_ua_platform
        self.sec_ch_ua_platform_version = sec_ch_ua_platform_version
        self.sec_ch_ua_arch = sec_ch_ua_arch
        self.sec_ch_ua_bitness = sec_ch_ua_bitness
        self.sec_ch_ua_full_version = sec_ch_ua_full_version
        self.sec_ch_ua_mobile = sec_ch_ua_mobile
        self.sec_ch_ua_model = sec_ch_ua_model
        self.sec_fetch_dest = sec_fetch_dest
        self.sec_fetch_mode = sec_fetch_mode
        self.sec_fetch_site = sec_fetch_site
        self.origin = origin
        self.referer = referer
        self.dnt = dnt
        self.connection = connection
        self.cache_control = cache_control
        self.timezone = timezone
        self.screen_resolution = screen_resolution
        self.color_depth = color_depth


async def extract_signals(request: Request) -> RequestSignals:
    """
    Extract all available signals from the request including Client Hints.
    
    Client Hints are automatically sent by modern browsers and provide
    rich fingerprinting data without tracking users.
    """
    # Support X-Forwarded-For (for simulation + proxies)
    forwarded_ip = request.headers.get("X-Forwarded-For")

    if forwarded_ip:
        ip = forwarded_ip.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else 'unknown'

    # ── BASIC SIGNALS ──
    user_agent = request.headers.get("user-agent", "unknown")
    endpoint = request.url.path
    method = request.method
    timestamp = datetime.utcnow()

    # ── HTTP HEADERS ──
    accept_language = request.headers.get("accept-language")
    accept_encoding = request.headers.get("accept-encoding")
    accept = request.headers.get("accept")
    dnt = request.headers.get("dnt")
    connection = request.headers.get("connection")
    cache_control = request.headers.get("cache-control")
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    # ── CLIENT HINTS (Modern Browsers) ──
    # These are high-entropy signals that make fingerprinting unique
    sec_ch_ua = request.headers.get("sec-ch-ua")
    sec_ch_ua_platform = request.headers.get("sec-ch-ua-platform")
    sec_ch_ua_platform_version = request.headers.get("sec-ch-ua-platform-version")
    sec_ch_ua_arch = request.headers.get("sec-ch-ua-arch")
    sec_ch_ua_bitness = request.headers.get("sec-ch-ua-bitness")
    sec_ch_ua_full_version = request.headers.get("sec-ch-ua-full-version")
    sec_ch_ua_mobile = request.headers.get("sec-ch-ua-mobile")
    sec_ch_ua_model = request.headers.get("sec-ch-ua-model")

    # ── SEC-FETCH HEADERS (Modern Browsers) ──
    sec_fetch_dest = request.headers.get("sec-fetch-dest")
    sec_fetch_mode = request.headers.get("sec-fetch-mode")
    sec_fetch_site = request.headers.get("sec-fetch-site")

    # ── CUSTOM HEADERS (for enhanced tracking) ──
    timezone = request.headers.get("x-timezone")
    screen_resolution = request.headers.get("x-screen-resolution")
    color_depth = request.headers.get("x-color-depth")

    logger.info(
        f"{method} {endpoint} | IP={ip} | "
        f"UA={user_agent[:30]}... | "
        f"Platform={sec_ch_ua_platform or 'unknown'}"
    )

    return RequestSignals(
        ip_address=ip,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        timestamp=timestamp,
        # Enhanced signals
        accept_language=accept_language,
        accept_encoding=accept_encoding,
        accept=accept,
        sec_ch_ua=sec_ch_ua,
        sec_ch_ua_platform=sec_ch_ua_platform,
        sec_ch_ua_platform_version=sec_ch_ua_platform_version,
        sec_ch_ua_arch=sec_ch_ua_arch,
        sec_ch_ua_bitness=sec_ch_ua_bitness,
        sec_ch_ua_full_version=sec_ch_ua_full_version,
        sec_ch_ua_mobile=sec_ch_ua_mobile,
        sec_ch_ua_model=sec_ch_ua_model,
        sec_fetch_dest=sec_fetch_dest,
        sec_fetch_mode=sec_fetch_mode,
        sec_fetch_site=sec_fetch_site,
        origin=origin,
        referer=referer,
        dnt=dnt,
        connection=connection,
        cache_control=cache_control,
        timezone=timezone,
        screen_resolution=screen_resolution,
        color_depth=color_depth,
    )