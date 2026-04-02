from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class AuthUser:
    user_id: int
    username: str
    created_at: str


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    expires_at: str
    user: AuthUser


class AuthService:
    def __init__(self, db_path: Path, token_ttl_hours: int = 24) -> None:
        self.db_path = Path(db_path)
        self.token_ttl_seconds = max(1, int(token_ttl_hours)) * 3600
        self._lock = threading.RLock()
        self._initialize()

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires_at ON auth_tokens(expires_at)")
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def register_user(self, username: str, password: str) -> AuthUser:
        uname = self._normalize_username(username)
        self._validate_password(password)

        now = self._now_iso()
        password_hash = self._hash_password(password)

        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users(username, password_hash, created_at) VALUES (?, ?, ?)",
                    (uname, password_hash, now),
                )
                conn.commit()
                user_id = int(cur.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("用户名已存在，请换一个。") from exc

        return AuthUser(user_id=user_id, username=uname, created_at=now)

    def login(self, username: str, password: str) -> AuthSession:
        uname = self._normalize_username(username)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
                (uname,),
            ).fetchone()

        if row is None:
            raise ValueError("用户名或密码错误。")

        if not self._verify_password(password, str(row["password_hash"])):
            raise ValueError("用户名或密码错误。")

        user = AuthUser(
            user_id=int(row["id"]),
            username=str(row["username"]),
            created_at=str(row["created_at"]),
        )

        now_ts = int(time.time())
        expires_at_ts = now_ts + self.token_ttl_seconds
        now_iso = self._now_iso()
        expires_at_iso = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc).isoformat()
        token = secrets.token_urlsafe(32)

        with self._connect() as conn:
            self._cleanup_expired_tokens(conn, now_ts)
            conn.execute(
                "INSERT INTO auth_tokens(token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (token, user.user_id, expires_at_ts, now_iso),
            )
            conn.commit()

        return AuthSession(access_token=token, expires_at=expires_at_iso, user=user)

    def get_user_by_token(self, token: str) -> AuthUser | None:
        raw = (token or "").strip()
        if not raw:
            return None

        now_ts = int(time.time())
        with self._connect() as conn:
            self._cleanup_expired_tokens(conn, now_ts)
            row = conn.execute(
                """
                SELECT u.id, u.username, u.created_at
                FROM auth_tokens t
                JOIN users u ON u.id = t.user_id
                WHERE t.token = ? AND t.expires_at > ?
                """,
                (raw, now_ts),
            ).fetchone()

        if row is None:
            return None

        return AuthUser(
            user_id=int(row["id"]),
            username=str(row["username"]),
            created_at=str(row["created_at"]),
        )

    def logout(self, token: str) -> None:
        raw = (token or "").strip()
        if not raw:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (raw,))
            conn.commit()

    @staticmethod
    def _normalize_username(username: str) -> str:
        uname = (username or "").strip()
        if not re.match(r"^[A-Za-z0-9_]{3,32}$", uname):
            raise ValueError("用户名需为 3-32 位，仅允许字母、数字和下划线。")
        return uname

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password or "") < 6:
            raise ValueError("密码至少 6 位。")
        if len(password) > 128:
            raise ValueError("密码长度不能超过 128 位。")

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    @staticmethod
    def _hash_password(password: str) -> str:
        iterations = 120_000
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            scheme, iterations_s, salt_hex, digest_hex = encoded.split("$", 3)
            if scheme != "pbkdf2_sha256":
                return False
            iterations = int(iterations_s)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
        except Exception:
            return False

        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    def _cleanup_expired_tokens(self, conn: sqlite3.Connection, now_ts: int) -> None:
        with self._lock:
            conn.execute("DELETE FROM auth_tokens WHERE expires_at <= ?", (now_ts,))
