"""Small local HTTP bridge for the Liminal display demo.

The server keeps frozen Pass 1 payloads in memory only. It deliberately returns
only the two user-facing readings and never exposes prompts, evidence objects,
provider receipts, or the configured API key to the browser.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
import time
from collections.abc import Callable, Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

from .contracts import ContractError
from .model_workflow import ModelWorkflow
from .pass2 import Pass2Pipeline
from .pipeline import Pass1Pipeline
from .providers import DEFAULT_ENV_PATH, DeepSeekClient, DeepSeekConfig, ProviderError


MAX_BODY_BYTES = 64 * 1024
MAX_TEXT_LENGTH = 12_000
SESSION_TTL_SECONDS = 3 * 60 * 60
MAX_SESSIONS = 64
DEFAULT_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
}


class Workflow(Protocol):
    def run_pass1(self, request: Mapping[str, Any]) -> dict[str, Any]: ...
    def run_pass2(self, request: Mapping[str, Any]) -> dict[str, Any]: ...


class DemoInputError(ValueError):
    """Raised for a browser request that is safe to describe to the caller."""


def _required_text(body: Mapping[str, Any], name: str) -> str:
    value = body.get(name)
    if not isinstance(value, str) or not value.strip():
        raise DemoInputError(f"{name} must be a non-empty string")
    value = value.strip()
    if len(value) > MAX_TEXT_LENGTH:
        raise DemoInputError(f"{name} is too long")
    return value


class DemoService:
    """Own the ephemeral session boundary between Pass 1 and Pass 2."""

    def __init__(
        self,
        *,
        env_path: Path = DEFAULT_ENV_PATH,
        workflow_factory: Callable[[], Workflow] | None = None,
    ) -> None:
        self.env_path = env_path
        self.pass1_pipeline = Pass1Pipeline()
        self.pass2_pipeline = Pass2Pipeline()
        self._workflow_factory = workflow_factory or self._default_workflow
        self._sessions: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def _default_workflow(self) -> Workflow:
        config = DeepSeekConfig.from_env(self.env_path)
        return ModelWorkflow(
            DeepSeekClient(config),
            pass1_pipeline=self.pass1_pipeline,
            pass2_pipeline=self.pass2_pipeline,
        )

    def _prune_sessions(self) -> None:
        cutoff = time.time() - SESSION_TTL_SECONDS
        expired = [key for key, (created, _) in self._sessions.items() if created < cutoff]
        for key in expired:
            self._sessions.pop(key, None)
        while len(self._sessions) >= MAX_SESSIONS:
            oldest = min(self._sessions, key=lambda key: self._sessions[key][0])
            self._sessions.pop(oldest, None)

    def start_pass1(self, body: Mapping[str, Any]) -> dict[str, str]:
        card = _required_text(body, "card")
        transcript = _required_text(body, "transcript")
        orientation = body.get("orientation")
        if orientation not in {"upright", "reversed"}:
            raise DemoInputError("orientation must be upright or reversed")

        session_id = secrets.token_urlsafe(18)
        request = self.pass1_pipeline.prepare_request(
            session_id=session_id,
            card_ref=card,
            orientation=orientation,
            raw_transcript=transcript,
        )
        run = self._workflow_factory().run_pass1(request)
        frozen = run.get("frozen_pass1")
        output = run.get("output")
        if not isinstance(frozen, dict) or not isinstance(output, Mapping):
            raise ContractError("Pass 1 workflow returned an incomplete result")
        reading = output.get("user_display", {}).get("integrated_reading")
        if not isinstance(reading, str) or not reading.strip():
            raise ContractError("Pass 1 workflow omitted its user-facing reading")

        with self._lock:
            self._prune_sessions()
            self._sessions[session_id] = (time.time(), frozen)
        return {"session_id": session_id, "reading": reading}

    def start_pass2(self, body: Mapping[str, Any]) -> dict[str, str]:
        session_id = _required_text(body, "session_id")
        question = _required_text(body, "question")
        question_shift = body.get("question_shift")
        if question_shift not in {
            "unchanged",
            "clarified",
            "shifted_focus",
            "different_question",
        }:
            raise DemoInputError("question_shift is invalid")
        note = body.get("question_shift_note")
        if note is not None:
            if not isinstance(note, str):
                raise DemoInputError("question_shift_note must be a string")
            note = note.strip() or None
            if note is not None and len(note) > MAX_TEXT_LENGTH:
                raise DemoInputError("question_shift_note is too long")

        with self._lock:
            self._prune_sessions()
            stored = self._sessions.get(session_id)
        if stored is None:
            raise KeyError(session_id)

        request = self.pass2_pipeline.prepare_request(
            frozen_pass1=stored[1],
            user_question=question,
            question_shift=question_shift,
            question_shift_note=note,
        )
        run = self._workflow_factory().run_pass2(request)
        output = run.get("output")
        if not isinstance(output, Mapping):
            raise ContractError("Pass 2 workflow returned an incomplete result")
        display = output.get("user_display")
        if not isinstance(display, Mapping):
            raise ContractError("Pass 2 workflow omitted its user-facing display")
        reading = display.get("complete_reading")
        takeaway = display.get("takeaway_question")
        if not isinstance(reading, str) or not isinstance(takeaway, str):
            raise ContractError("Pass 2 workflow omitted required user-facing text")
        return {"reading": reading, "takeaway_question": takeaway}


class DemoHTTPServer(ThreadingHTTPServer):
    service: DemoService
    allowed_origins: set[str]


class DemoRequestHandler(BaseHTTPRequestHandler):
    server: DemoHTTPServer

    def log_message(self, format: str, *args: object) -> None:
        # Keep normal access metadata while never logging request bodies.
        super().log_message(format, *args)

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin in self.server.allowed_origins

    def _send_json(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not self._origin_allowed():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Origin is not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/api/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._origin_allowed():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Origin is not allowed"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise DemoInputError("Request body size is invalid")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(body, Mapping):
                raise DemoInputError("Request body must be a JSON object")
            path = urlparse(self.path).path
            if path == "/api/pass1":
                result = self.server.service.start_pass1(body)
            elif path == "/api/pass2":
                result = self.server.service.start_pass2(body)
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            self._send_json(HTTPStatus.OK, result)
        except (DemoInputError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except KeyError:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "This reading session expired. Please begin a new reading."},
            )
        except (ContractError, ProviderError):
            self._send_json(
                HTTPStatus.BAD_GATEWAY,
                {"error": "The reading service could not complete this request."},
            )
        except Exception:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "The reading service encountered an unexpected error."},
            )


def parse_origins(value: str | None) -> set[str]:
    if not value:
        return set(DEFAULT_ORIGINS)
    return {item.strip().rstrip("/") for item in value.split(",") if item.strip()}


def build_server(
    host: str,
    port: int,
    *,
    env_path: Path = DEFAULT_ENV_PATH,
) -> DemoHTTPServer:
    server = DemoHTTPServer((host, port), DemoRequestHandler)
    server.service = DemoService(env_path=env_path)
    server.allowed_origins = parse_origins(os.environ.get("LIMINAL_DEMO_ORIGINS"))
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local Liminal display demo API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_PATH)
    args = parser.parse_args()
    server = build_server(args.host, args.port, env_path=args.env_file)
    print(f"Liminal demo API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
