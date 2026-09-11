"""Command-line entry points for the Phase 3–4 two-pass workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .contracts import ContractError
from .model_workflow import ModelWorkflow
from .pipeline import Pass1Pipeline
from .pass2 import Pass2Pipeline
from .providers import DEFAULT_ENV_PATH, DeepSeekClient, DeepSeekConfig, ProviderError


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _secure_write_json(path: str, value: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(output_path, 0o600)
    return output_path


def _add_provider_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Local ignored environment file containing DeepSeek settings",
    )


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
    parser = argparse.ArgumentParser(description="Liminal v2 Phase 3–4 tooling")
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

    prepare_pass2 = subparsers.add_parser(
        "prepare-pass2", help="Prepare question reveal and a Pass 2 request"
    )
    prepare_pass2.add_argument("--frozen-pass1", required=True)
    prepare_pass2.add_argument("--question", required=True)
    prepare_pass2.add_argument(
        "--question-shift",
        choices=("unchanged", "clarified", "shifted_focus", "different_question"),
        required=True,
    )
    prepare_pass2.add_argument("--question-shift-note")

    render_situated = subparsers.add_parser(
        "render-situated", help="Render isolated situated traditional prompt"
    )
    render_situated.add_argument("--request", required=True)

    render_integration = subparsers.add_parser(
        "render-pass2-integration", help="Render Pass 2 context-integration prompt"
    )
    render_integration.add_argument("--request", required=True)
    render_integration.add_argument("--situated", required=True)

    render_pass2_writing = subparsers.add_parser(
        "render-pass2-writing", help="Render final Pass 2 writing prompt"
    )
    render_pass2_writing.add_argument("--request", required=True)
    render_pass2_writing.add_argument("--situated", required=True)
    render_pass2_writing.add_argument("--integration", required=True)

    assemble_pass2 = subparsers.add_parser(
        "assemble-pass2", help="Assemble and validate a Pass 2 output"
    )
    assemble_pass2.add_argument("--request", required=True)
    assemble_pass2.add_argument("--situated", required=True)
    assemble_pass2.add_argument("--integration", required=True)
    assemble_pass2.add_argument("--writing", required=True)

    smoke = subparsers.add_parser(
        "deepseek-smoke", help="Run one minimal paid JSON connectivity request"
    )
    _add_provider_arguments(smoke)

    run_pass1 = subparsers.add_parser(
        "run-pass1-model", help="Run all four locked Pass 1 stages with DeepSeek"
    )
    _add_request_arguments(run_pass1)
    _add_provider_arguments(run_pass1)
    run_pass1.add_argument("--output", required=True)

    run_pass2 = subparsers.add_parser(
        "run-pass2-model", help="Run all three locked Pass 2 stages with DeepSeek"
    )
    run_pass2.add_argument("--pass1-run", required=True)
    run_pass2.add_argument("--question", required=True)
    run_pass2.add_argument(
        "--question-shift",
        choices=("unchanged", "clarified", "shifted_focus", "different_question"),
        required=True,
    )
    run_pass2.add_argument("--question-shift-note")
    _add_provider_arguments(run_pass2)
    run_pass2.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline = Pass1Pipeline()
    pass2_pipeline = Pass2Pipeline()

    if args.command in {"deepseek-smoke", "run-pass1-model", "run-pass2-model"}:
        try:
            config = DeepSeekConfig.from_env(Path(args.env_file))
            client = DeepSeekClient(config)
            workflow = ModelWorkflow(
                client,
                pass1_pipeline=pipeline,
                pass2_pipeline=pass2_pipeline,
                on_stage=lambda stage: print(
                    f"Running {stage}...", file=sys.stderr, flush=True
                ),
            )
            if args.command == "deepseek-smoke":
                response = client.complete_json(
                    'Return exactly this JSON object and nothing else: {"status":"ok"}',
                    stage="connectivity_smoke",
                )
                if response.payload != {"status": "ok"}:
                    raise ProviderError("smoke response did not match the expected object")
                print(json.dumps({"status": "ok", "receipt": response.receipt}, indent=2))
                return 0
            if args.command == "run-pass1-model":
                request = pipeline.prepare_request(
                    session_id=args.session_id,
                    card_ref=args.card,
                    orientation=args.orientation,
                    raw_transcript=_transcript(args),
                    speaking_duration_seconds=args.speaking_duration_seconds,
                )
                run = workflow.run_pass1(request)
                output_path = _secure_write_json(args.output, run)
                print(
                    json.dumps(
                        {
                            "status": "ok",
                            "output": str(output_path),
                            "pass1_sha256": run["frozen_pass1"]["pass1_sha256"],
                            "provider_receipts": run["provider_receipts"],
                        },
                        indent=2,
                    )
                )
                return 0
            pass1_run = _load_json(args.pass1_run)
            frozen_pass1 = pass1_run.get("frozen_pass1")
            if not isinstance(frozen_pass1, dict):
                raise ProviderError("pass1 run file does not contain frozen_pass1")
            request = pass2_pipeline.prepare_request(
                frozen_pass1=frozen_pass1,
                user_question=args.question,
                question_shift=args.question_shift,
                question_shift_note=args.question_shift_note,
            )
            run = workflow.run_pass2(request)
            output_path = _secure_write_json(args.output, run)
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "output": str(output_path),
                        "pass1_sha256": run["output"]["pass1_sha256"],
                        "provider_receipts": run["provider_receipts"],
                    },
                    indent=2,
                )
            )
            return 0
        except (ProviderError, ContractError) as exc:
            print(f"Model workflow error: {exc}")
            return 2

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

    if args.command == "verify-frozen":
        pipeline.verify_frozen(_load_json(args.input))
        print("Frozen Pass 1 is valid and unchanged.")
        return 0

    if args.command == "prepare-pass2":
        request = pass2_pipeline.prepare_request(
            frozen_pass1=_load_json(args.frozen_pass1),
            user_question=args.question,
            question_shift=args.question_shift,
            question_shift_note=args.question_shift_note,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    request = _load_json(args.request)
    if args.command == "render-situated":
        print(pass2_pipeline.render_situated_prompt(request))
        return 0
    if args.command == "render-pass2-integration":
        print(
            pass2_pipeline.render_integration_prompt(
                request, _load_json(args.situated)
            )
        )
        return 0
    if args.command == "render-pass2-writing":
        print(
            pass2_pipeline.render_writing_prompt(
                request,
                _load_json(args.situated),
                _load_json(args.integration),
            )
        )
        return 0
    output = pass2_pipeline.assemble(
        request,
        _load_json(args.situated),
        _load_json(args.integration),
        _load_json(args.writing),
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
