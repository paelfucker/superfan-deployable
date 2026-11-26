"""Small in-memory helpers that protect your API bill. No third-party deps.

State lives in one process. That is fine for a hobby app on Cloud Run with
--max-instances 1 or 2; with more instances each one keeps its own counts.
"""
import threading
import time
from collections import OrderedDict, deque
from datetime import datetime, timezone


class RateLimiter:
    """Per-client sliding window plus a global daily cap."""

    def __init__(self, per_client: int, window_seconds: int, daily_cap: int):
        self.per_client = per_client
        self.window = window_seconds
        self.daily_cap = daily_cap
        self._hits: dict[str, deque] = {}
        self._day = self._today()
        self._day_count = 0
        self._lock = threading.Lock()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def check(self, client: str, now: float | None = None) -> str | None:
        """Record a request. Returns None if allowed, else a reason string."""
        now = time.time() if now is None else now
        with self._lock:
            today = self._today()
            if today != self._day:
                self._day, self._day_count = today, 0
            if self._day_count >= self.daily_cap:
                return "daily_cap"

            hits = self._hits.setdefault(client, deque())
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) >= self.per_client:
                return "rate_limit"

            hits.append(now)
            self._day_count += 1

            # Keep memory bounded.
            if len(self._hits) > 5000:
                for key in [k for k, v in self._hits.items() if not v]:
                    del self._hits[key]
            return None


class SessionStore:
    """Short per-visitor chat history, so visitors don't share a conversation."""

    def __init__(self, max_sessions: int = 500, max_messages: int = 8):
        self.max_sessions = max_sessions
        self.max_messages = max_messages
        self._data: OrderedDict[str, list] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str) -> list:
        with self._lock:
            history = self._data.get(session_id, [])
            if session_id in self._data:
                self._data.move_to_end(session_id)
            return list(history)

    def add_turn(self, session_id: str, user_text: str, reply: str) -> None:
        with self._lock:
            history = self._data.setdefault(session_id, [])
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            del history[: -self.max_messages]
            self._data.move_to_end(session_id)
            while len(self._data) > self.max_sessions:
                self._data.popitem(last=False)
