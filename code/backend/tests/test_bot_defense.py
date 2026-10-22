"""
Comprehensive bot defense test suite covering Normal, Edge, and Extraordinary cases.
Tests:
- Scanner and malicious bot User-Agent detection and blocking.
- Honeypot trap routes and dynamic IP banning.
- Honeypot form field validation.
- Login rate limiting and brute-force consecutive failure lockout.
- Missing User-Agent enforcement on state-modifying endpoints.
- In-memory bounds and eviction.
"""
import os
import time
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

# Ensure test environment variables are loaded
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-12345678901234567890")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET_NAME", "artifacts")

from src.main import app
from src.bot_defense import (
    BotJail,
    LoginRateLimiter,
    is_malicious_user_agent,
    is_empty_user_agent,
    extract_client_ip,
    reset_bot_defense_state,
    bot_jail,
    login_rate_limiter,
)
from src.auth import get_password_hash
from src.models import Base, User
from src.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_env():
    """Reset database and in-memory defense stores before every test."""
    reset_bot_defense_state()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)

    # Seed an admin test user
    db = TestingSessionLocal()
    user = User(
        username="admin_user",
        email="admin@example.com",
        password_hash=get_password_hash("ValidAdminPass!2026"),
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    reset_bot_defense_state()


# ==============================================================================
# 1. Normal Cases (The Happy Path)
# ==============================================================================
class TestBotDefenseNormalCases:
    """Tests normal, expected client interactions with legitimate requests."""

    def test_legitimateUserAgent_passesMiddleware_returnsSuccess(self):
        # Arrange
        client = TestClient(app)
        legit_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Act
        response = client.get("/", headers={"User-Agent": legit_ua})

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "Academic Artifact Research Database API"}

    def test_legitimateLogin_withEmptyHoneypot_authenticatesSuccessfully(self):
        # Arrange
        client = TestClient(app)
        payload = {
            "username": "admin_user",
            "password": "ValidAdminPass!2026",
            "honeypot": None,
            "website": "",
        }

        # Act
        response = client.post("/auth/login", json=payload, headers={"User-Agent": "Mozilla/5.0"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin_user"
        assert data["is_admin"] is True
        assert "access_token" in response.cookies

    def test_robotsTxt_returnsDisallowAndCrawlDelay(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/robots.txt")

        # Assert
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "Disallow: /api/" in response.text
        assert "Disallow: /auth/" in response.text
        assert "Crawl-delay: 5" in response.text
        assert "User-agent: GPTBot" in response.text

    def test_isMaliciousUserAgent_standardBrowsers_returnsFalse(self):
        # Arrange & Act & Assert
        assert not is_malicious_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        assert not is_malicious_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)")
        assert not is_malicious_user_agent("curl/7.68.0")
        assert not is_malicious_user_agent("python-requests/2.31.0")


# ==============================================================================
# 2. Edge Cases (Boundary Conditions)
# ==============================================================================
class TestBotDefenseEdgeCases:
    """Tests boundary thresholds for rate limits, lockouts, capacities, and IP extraction."""

    def test_loginRateLimiter_atBoundary_allowsUpToMaxAndThrottlesNext(self):
        # Arrange
        limiter = LoginRateLimiter(window_seconds=60.0, max_requests_per_window=3)
        client_ip = "192.168.1.100"

        # Act & Assert: first 3 attempts succeed
        allowed_1, err_1 = limiter.check_login_attempt(client_ip)
        assert allowed_1 is True
        assert err_1 is None

        allowed_2, err_2 = limiter.check_login_attempt(client_ip)
        assert allowed_2 is True
        assert err_2 is None

        allowed_3, err_3 = limiter.check_login_attempt(client_ip)
        assert allowed_3 is True
        assert err_3 is None

        # 4th attempt at boundary must be throttled
        allowed_4, err_4 = limiter.check_login_attempt(client_ip)
        assert allowed_4 is False
        assert "Rate limit exceeded" in err_4

    def test_loginRateLimiter_consecutiveFailures_lockoutTriggeredAtThreshold(self):
        # Arrange
        limiter = LoginRateLimiter(max_consecutive_failures=3, lockout_duration_seconds=300.0)
        client_ip = "10.0.0.50"
        user = "test_target"

        # Act: 2 failed attempts
        limiter.record_login_failure(client_ip, user)
        limiter.record_login_failure(client_ip, user)
        allowed, _ = limiter.check_login_attempt(client_ip, user)
        assert allowed is True

        # 3rd failure hits threshold
        limiter.record_login_failure(client_ip, user)
        allowed_locked, err_locked = limiter.check_login_attempt(client_ip, user)

        # Assert
        assert allowed_locked is False
        assert "locked out" in err_locked.lower() or "locked" in err_locked.lower()

    def test_loginRateLimiter_successfulLogin_resetsFailureCounters(self):
        # Arrange
        limiter = LoginRateLimiter(max_consecutive_failures=3)
        client_ip = "10.0.0.60"
        user = "reset_user"

        # Act: 2 failed attempts, followed by 1 successful login
        limiter.record_login_failure(client_ip, user)
        limiter.record_login_failure(client_ip, user)
        limiter.record_login_success(client_ip, user)

        # 1 new failed attempt
        limiter.record_login_failure(client_ip, user)
        allowed, _ = limiter.check_login_attempt(client_ip, user)

        # Assert: Still allowed because counter was reset
        assert allowed is True

    def test_botJail_capacityLimit_evictsOldestEntryWithoutCrashing(self):
        # Arrange
        jail = BotJail(max_capacity=3, default_ban_duration=600.0)

        # Act
        jail.ban_ip("1.1.1.1", duration=100.0)
        jail.ban_ip("2.2.2.2", duration=200.0)
        jail.ban_ip("3.3.3.3", duration=300.0)
        # Adding 4th exceeds capacity=3
        jail.ban_ip("4.4.4.4", duration=400.0)

        # Assert
        assert len(jail._banned_ips) == 3
        # Oldest (1.1.1.1) evicted
        assert not jail.is_ip_banned("1.1.1.1")
        assert jail.is_ip_banned("4.4.4.4")

    def test_extractClientIp_usesXRealIpOverDirectClient(self):
        # Arrange
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: "203.0.113.195" if h == "X-Real-IP" else None
        mock_request.client.host = "10.0.0.1"

        # Act
        ip = extract_client_ip(mock_request)

        # Assert
        assert ip == "203.0.113.195"

    def test_honeypot_withWhitespaceOnly_isTreatedAsEmpty(self):
        # Arrange
        client = TestClient(app)
        payload = {
            "username": "admin_user",
            "password": "ValidAdminPass!2026",
            "honeypot": "   ",
            "website": "   ",
        }

        # Act
        response = client.post("/auth/login", json=payload, headers={"User-Agent": "Mozilla/5.0"})

        # Assert: Whitespace is stripped and considered safe
        assert response.status_code == 200


# ==============================================================================
# 3. Extraordinary Cases (The Sad Path & Security Anomalies)
# ==============================================================================
class TestBotDefenseExtraordinaryCases:
    """Tests defense behavior against malicious bots, automated scanners, exploit probes, and honeypot triggers."""

    @pytest.mark.parametrize("scanner_name", [
        "sqlmap/1.5#stable",
        "Mozilla/5.0 (Nikto/2.1.6)",
        "Acunetix-Product",
        "dirbuster-1.0",
        "gobuster/3.1",
        "nuclei - v2.9.0",
        "WPScan v3.8.22",
        "masscan/1.3",
        "Nmap Scripting Engine",
        "CensysInspect/1.1",
        "Shodan-Scanner",
    ])
    def test_maliciousScannerUserAgent_blockedWith403_andIpBanned(self, scanner_name):
        # Arrange
        client = TestClient(app)
        attacker_ip = "198.51.100.77"

        # Act: Scanner sends a request
        response = client.get("/", headers={"User-Agent": scanner_name, "X-Real-IP": attacker_ip})

        # Assert
        assert response.status_code == 403
        assert "automated security scanner detected" in response.json()["detail"]

        # Assert: IP is now in BotJail
        assert bot_jail.is_ip_banned(attacker_ip)

        # Assert: Subsequent requests from the banned IP with a normal User-Agent are still blocked!
        subsequent_res = client.get("/", headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": attacker_ip})
        assert subsequent_res.status_code == 403
        assert "automated bot activity detected" in subsequent_res.json()["detail"]

    @pytest.mark.parametrize("probe_path", [
        "/bot-trap",
        "/api/bot-trap",
        "/wp-admin",
        "/wp-login.php",
        "/xmlrpc.php",
        "/phpmyadmin",
        "/.env",
        "/.git",
        "/.aws",
    ])
    def test_exploitProbeOrHoneypot_blockedWith403_andIpBanned(self, probe_path):
        # Arrange
        client = TestClient(app)
        crawler_ip = "198.51.100.88"

        # Act: Crawler hits honeypot/exploit probe path
        response = client.get(probe_path, headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": crawler_ip})

        # Assert
        assert response.status_code == 403
        assert bot_jail.is_ip_banned(crawler_ip)

        # Subsequent legitimate query is now blocked because IP is jailed
        denied_res = client.get("/objects/search", headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": crawler_ip})
        assert denied_res.status_code == 403

    def test_stateModifyingRequest_withMissingUserAgent_rejectedWith400(self):
        # Arrange
        client = TestClient(app)

        # Act: POST without User-Agent header (empty header)
        response = client.post(
            "/auth/login",
            json={"username": "test", "password": "password"},
            headers={"User-Agent": ""}
        )

        # Assert
        assert response.status_code == 400
        assert "User-Agent header is required" in response.json()["detail"]

    def test_loginForm_withPopulatedHoneypotField_rejectsAndBansIp(self):
        # Arrange
        client = TestClient(app)
        bot_ip = "198.51.100.99"
        payload = {
            "username": "admin_user",
            "password": "ValidAdminPass!2026",
            "honeypot": "https://spam-payload.evil.com",
            "website": "buy-cheap-drugs.com",
        }

        # Act: Automated bot filled the hidden honeypot field
        response = client.post(
            "/auth/login",
            json=payload,
            headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": bot_ip}
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid request submission" in response.json()["detail"]
        assert bot_jail.is_ip_banned(bot_ip)

    def test_bruteForceAttack_locksOutAttackerAfterFiveConsecutiveFailures(self):
        # Arrange
        client = TestClient(app)
        attacker_ip = "198.51.100.111"
        target_username = "admin_user"

        # Act: 5 consecutive failed login attempts
        for i in range(5):
            res = client.post(
                "/auth/login",
                json={"username": target_username, "password": f"WrongPass{i}!"},
                headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": attacker_ip}
            )
            assert res.status_code == 401

        # Act: 6th attempt with the CORRECT password
        res_locked = client.post(
            "/auth/login",
            json={"username": target_username, "password": "ValidAdminPass!2026"},
            headers={"User-Agent": "Mozilla/5.0", "X-Real-IP": attacker_ip}
        )

        # Assert: 429 Too Many Requests lockout even though the password was valid!
        assert res_locked.status_code == 429
        assert "locked out" in res_locked.json()["detail"].lower()
