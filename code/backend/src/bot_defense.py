import re
import time
from typing import Dict, List, Optional, Tuple, Any
from fastapi import Request


# Known malicious security scanner and exploit framework signatures in User-Agent headers
BAD_BOT_PATTERN = re.compile(
    r"(sqlmap|nikto|acunetix|dirbuster|gobuster|nuclei|wpscan|masscan|zgrab|"
    r"censys|shodan|havij|whatweb|burpcollaborator|nmap|morfeus|nessus)",
    re.IGNORECASE
)

# Common exploit probe paths automated bots scan for
EXPLOIT_PROBE_PATHS = frozenset({
    "/wp-admin",
    "/wp-login.php",
    "/xmlrpc.php",
    "/phpmyadmin",
    "/.env",
    "/.git",
    "/.aws",
    "/.svn",
    "/bot-trap",
    "/api/bot-trap"
})


class BotJail:
    """
    In-memory temporary IP ban store for abusive bots.
    Enforces maximum capacity and automatic expiration eviction to prevent memory exhaustion DoS.
    """
    def __init__(self, max_capacity: int = 5000, default_ban_duration: float = 3600.0):
        self.max_capacity = max_capacity
        self.default_ban_duration = default_ban_duration
        self._banned_ips: Dict[str, float] = {}
        self._last_cleanup = 0.0

    def ban_ip(self, ip: str, duration: Optional[float] = None, reason: str = "") -> None:
        """Add an IP to the temporary ban list."""
        ban_seconds = duration if duration is not None else self.default_ban_duration
        now = time.time()
        self.cleanup_expired(now)

        # Enforce hard capacity bounds
        if len(self._banned_ips) >= self.max_capacity:
            # Evict the oldest entry
            oldest_ip = min(self._banned_ips.keys(), key=lambda k: self._banned_ips[k])
            self._banned_ips.pop(oldest_ip, None)

        self._banned_ips[ip] = now + ban_seconds

    def is_ip_banned(self, ip: str) -> bool:
        """Check if an IP is currently banned."""
        now = time.time()
        ban_expiry = self._banned_ips.get(ip)
        if ban_expiry is None:
            return False
        if now >= ban_expiry:
            self._banned_ips.pop(ip, None)
            return False
        return True

    def unban_ip(self, ip: str) -> None:
        """Manually remove an IP from the ban list."""
        self._banned_ips.pop(ip, None)

    def cleanup_expired(self, now: Optional[float] = None) -> None:
        """Evict all expired bans."""
        current_time = now if now is not None else time.time()
        if current_time - self._last_cleanup < 30.0 and len(self._banned_ips) < self.max_capacity:
            return
        self._last_cleanup = current_time

        expired = [ip for ip, expiry in self._banned_ips.items() if current_time >= expiry]
        for ip in expired:
            self._banned_ips.pop(ip, None)

    def clear(self) -> None:
        """Clear all bans (used for test isolation)."""
        self._banned_ips.clear()


class LoginRateLimiter:
    """
    Strict per-IP and per-account rate limiter and brute-force lockout tracker for authentication.
    - Limits request frequency (e.g. max 10 requests per 60s per IP).
    - Locks out after consecutive failures (e.g. 5 failures within 15 minutes).
    - Enforces memory capacity bounds and TTL pruning.
    """
    def __init__(
        self,
        window_seconds: float = 60.0,
        max_requests_per_window: int = 10,
        max_consecutive_failures: int = 5,
        lockout_duration_seconds: float = 900.0,  # 15 minutes
        max_capacity: int = 5000
    ):
        self.window_seconds = window_seconds
        self.max_requests_per_window = max_requests_per_window
        self.max_consecutive_failures = max_consecutive_failures
        self.lockout_duration_seconds = lockout_duration_seconds
        self.max_capacity = max_capacity

        # Tracks IP -> list of recent request timestamps
        self._requests_by_ip: Dict[str, List[float]] = {}
        # Tracks identifier/IP -> {"failures": int, "lockout_until": float}
        self._failure_tracker: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = 0.0

    def check_login_attempt(self, client_ip: str, identifier: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validates if a login attempt is allowed.
        Returns (is_allowed, error_detail).
        """
        now = time.time()
        self.cleanup_expired(now)

        # 1. Check IP lockout
        ip_lock = self._failure_tracker.get(client_ip)
        if ip_lock and now < ip_lock.get("lockout_until", 0.0):
            remaining = int(ip_lock["lockout_until"] - now)
            return False, f"Too many failed login attempts from this IP. Temporarily locked out for {remaining} seconds."

        # 2. Check identifier lockout (if provided)
        if identifier:
            id_key = f"user:{identifier.lower()}"
            user_lock = self._failure_tracker.get(id_key)
            if user_lock and now < user_lock.get("lockout_until", 0.0):
                remaining = int(user_lock["lockout_until"] - now)
                return False, f"Account temporarily locked due to multiple failed login attempts. Try again in {remaining} seconds."

        # 3. Check sliding-window request rate limit per IP
        timestamps = [
            t for t in self._requests_by_ip.get(client_ip, [])
            if now - t < self.window_seconds
        ]
        if len(timestamps) >= self.max_requests_per_window:
            return False, "Rate limit exceeded for login attempts. Please wait a minute before trying again."

        timestamps.append(now)
        self._requests_by_ip[client_ip] = timestamps
        return True, None

    def record_login_failure(self, client_ip: str, identifier: Optional[str] = None) -> None:
        """Record a failed login attempt for IP and username, triggering lockout if threshold reached."""
        now = time.time()

        keys_to_update = [client_ip]
        if identifier:
            keys_to_update.append(f"user:{identifier.lower()}")

        for key in keys_to_update:
            data = self._failure_tracker.setdefault(key, {"failures": 0, "lockout_until": 0.0})
            data["failures"] += 1
            if data["failures"] >= self.max_consecutive_failures:
                data["lockout_until"] = now + self.lockout_duration_seconds

    def record_login_success(self, client_ip: str, identifier: Optional[str] = None) -> None:
        """Reset consecutive failure counter upon successful authentication."""
        self._failure_tracker.pop(client_ip, None)
        if identifier:
            self._failure_tracker.pop(f"user:{identifier.lower()}", None)

    def cleanup_expired(self, now: Optional[float] = None) -> None:
        """Evict expired request windows and expired lockouts."""
        current_time = now if now is not None else time.time()
        if current_time - self._last_cleanup < 30.0 and len(self._requests_by_ip) < self.max_capacity:
            return
        self._last_cleanup = current_time

        # Cleanup requests
        expired_ips = [
            ip for ip, timestamps in self._requests_by_ip.items()
            if not timestamps or (current_time - timestamps[-1] >= self.window_seconds)
        ]
        for ip in expired_ips:
            self._requests_by_ip.pop(ip, None)

        # Cleanup failure tracker
        expired_locks = [
            key for key, data in self._failure_tracker.items()
            if data.get("lockout_until", 0.0) <= current_time and data.get("failures", 0) == 0
        ]
        for key in expired_locks:
            self._failure_tracker.pop(key, None)

        # Enforce memory capacity bounds
        if len(self._requests_by_ip) >= self.max_capacity:
            overflow = len(self._requests_by_ip) - (self.max_capacity // 2)
            for k in list(self._requests_by_ip.keys())[:overflow]:
                self._requests_by_ip.pop(k, None)

        if len(self._failure_tracker) >= self.max_capacity:
            overflow = len(self._failure_tracker) - (self.max_capacity // 2)
            for k in list(self._failure_tracker.keys())[:overflow]:
                self._failure_tracker.pop(k, None)

    def clear(self) -> None:
        """Clear all rate limit state (used for test isolation)."""
        self._requests_by_ip.clear()
        self._failure_tracker.clear()


# Global singleton instances
bot_jail = BotJail()
login_rate_limiter = LoginRateLimiter()


def extract_client_ip(request: Request) -> str:
    """
    Safely extract client IP address.
    Behind reverse proxy (Nginx), X-Real-IP is set from $remote_addr and cannot be spoofed.
    Falls back to client host if direct connection.
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def is_malicious_user_agent(user_agent: Optional[str]) -> bool:
    """Detect if User-Agent matches known security scanners or exploit tools."""
    if not user_agent:
        return False
    return bool(BAD_BOT_PATTERN.search(user_agent))


def is_empty_user_agent(user_agent: Optional[str]) -> bool:
    """Check if User-Agent header is missing or empty."""
    return not user_agent or not user_agent.strip()


def reset_bot_defense_state() -> None:
    """Reset all in-memory bot defense state (for test isolation)."""
    bot_jail.clear()
    login_rate_limiter.clear()
