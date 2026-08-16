"""Command-line entry points for the Phase 3 testable Pass 1 workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .pipeline import Pass1Pipeline


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _transcript(args: argparse.Namespace) -> str:
    if args.transcript_file:
        return Path(args.transcript_file).read_text(encoding="utf-8")
    return args.transcript


def _add_request_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--card", required=True, help="Card id or exact English card name")
    parser.add_argument("--orientation", choices=("upright", "reversed"), required=True)
    transcript = parser.add_mutually_exclusive_group(required=True)
    transcript.add_argument("--transcript")
    transcript.add_argument("--transcript-file")
    parser.add_argument("--speaking-duration-seconds", type=float)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Liminal v2 Phase 3 tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-pass1", help="Print a question-blind Pass 1 request")
    _add_request_arguments(prepare)

    render = subparsers.add_parser(
        "render-observations", help="Render the Stage 1 evidence model prompt"
    )
    _add_request_arguments(render)

    patterns = subparsers.add_parser("render-patterns", help="Render the Stage 2 process prompt")
    patterns.add_argument("--request", required=True)
    patterns.add_argument("--evidence", required=True)

    compensation = subparsers.add_parser(
        "render-compensation", help="Render the Stage 3 compensation prompt"
    )
    compensation.add_argument("--request", required=True)
    compensation.add_argument("--evidence", required=True)
    compensation.add_argument("--patterns", required=True)

    writing = subparsers.add_parser("render-writing", help="Render the Stage 4 writing prompt")
    writing.add_argument("--request", required=True)
    writing.add_argument("--evidence", required=True)
    writing.add_argument("--patterns", required=True)
    writing.add_argument("--compensation", required=True)

    assemble = subparsers.add_parser("assemble-pass1", help="Assemble staged Pass 1 output")
    assemble.add_argument("--request", required=True)
    assemble.add_argument("--evidence", required=True)
    assemble.add_argument("--patterns", required=True)
    assemble.add_argument("--compensation", required=True)
    assemble.add_argument("--writing", required=True)

    validate = subparsers.add_parser("validate-pass1", help="Validate a Pass 1 output JSON file")
    validate.add_argument("--input", required=True)

    freeze = subparsers.add_parser("freeze-pass1", help="Validate and freeze a Pass 1 output")
    freeze.add_argument("--output", required=True)
    freeze.add_argument("--request", required=True)

    verify = subparsers.add_parser("verify-frozen", help="Verify a frozen Pass 1 JSON file")
    verify.add_argument("--input", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline = Pass1Pipeline()

    if args.command in {"prepare-pass1", "render-observations"}:
        request = pipeline.prepare_request(
            session_id=args.session_id,
            card_ref=args.card,
            orientation=args.orientation,
            raw_transcript=_transcript(args),
            speaking_duration_seconds=args.speaking_duration_seconds,
        )
        if args.command == "prepare-pass1":
            print(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(pipeline.render_observation_prompt(request))
        return 0

    if args.command == "render-patterns":
        print(pipeline.render_pattern_prompt(_load_json(args.request), _load_json(args.evidence)))
        return 0

    if args.command == "render-compensation":
        print(
            pipeline.render_compensation_prompt(
                _load_json(args.request),
                _load_json(args.evidence),
                _load_json(args.patterns),
            )
        )
        return 0

    if args.command == "render-writing":
        print(
            pipeline.render_writing_prompt(
                _load_json(args.request),
                _load_json(args.evidence),
                _load_json(args.patterns),
                _load_json(args.compensation),
            )
        )
        return 0

    if args.command == "assemble-pass1":
        output = pipeline.assemble(
            _load_json(args.request),
            _load_json(args.evidence),
            _load_json(args.patterns),
            _load_json(args.compensation),
            _load_json(args.writing),
        )
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "validate-pass1":
        from .contracts import validate_pass1_output

        validate_pass1_output(_load_json(args.input))
        print("Pass 1 output is valid.")
        return 0

    if args.command == "freeze-pass1":
        frozen = pipeline.freeze(_load_json(args.output), _load_json(args.request))
        print(json.dumps(frozen.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    pipeline.verify_frozen(_load_json(args.input))
    print("Frozen Pass 1 is valid and unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
