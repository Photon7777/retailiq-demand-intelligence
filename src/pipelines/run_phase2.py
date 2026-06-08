"""Run the RetailIQ Phase 2 data and analytics buildout."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from getpass import getpass
import os
from pathlib import Path
import shlex
import subprocess
import sys


@dataclass(frozen=True)
class CommandStep:
    """One shell command in the Phase 2 workflow."""

    name: str
    command: tuple[str, ...]
    cwd: Path


@dataclass(frozen=True)
class Phase2PipelineConfig:
    """Configuration for building the Phase 2 command plan."""

    project_root: Path
    python_executable: str
    dbt_executable: str
    input_dir: Path
    processed_dir: Path
    model_dir: Path
    output_dir: Path
    dbt_dir: Path
    random_seed: int
    n_estimators: int
    max_depth: int
    min_samples_leaf: int
    max_samples: float
    truncate_first: bool
    skip_prepare: bool
    skip_raw_load: bool
    skip_train: bool
    skip_predictions: bool
    skip_ml_load: bool
    skip_dbt: bool
    upload_gcs: bool
    gcs_prefix: str


def _append_if(command: list[str], condition: bool, *values: str) -> None:
    if condition:
        command.extend(values)


def build_phase2_steps(config: Phase2PipelineConfig) -> list[CommandStep]:
    """Build the ordered Phase 2 commands without executing them."""
    root = config.project_root
    steps: list[CommandStep] = []

    if not config.skip_prepare:
        steps.append(
            CommandStep(
                name="Prepare Walmart canonical CSVs",
                cwd=root,
                command=(
                    config.python_executable,
                    "-m",
                    "src.ingestion.prepare_walmart_data",
                    "--input-dir",
                    str(config.input_dir),
                    "--output-dir",
                    str(config.processed_dir),
                    "--random-seed",
                    str(config.random_seed),
                ),
            )
        )

    if config.upload_gcs:
        steps.append(
            CommandStep(
                name="Upload prepared CSVs to GCS",
                cwd=root,
                command=(
                    config.python_executable,
                    "-m",
                    "src.ingestion.upload_to_gcs",
                    "--sample-dir",
                    str(config.processed_dir),
                    "--prefix",
                    config.gcs_prefix,
                ),
            )
        )

    if not config.skip_raw_load:
        command = [
            config.python_executable,
            "-m",
            "src.ingestion.load_to_snowflake",
            "--sample-dir",
            str(config.processed_dir),
        ]
        _append_if(command, config.truncate_first, "--truncate-first")
        steps.append(CommandStep(name="Load RAW tables into Snowflake", cwd=root, command=tuple(command)))

    if not config.skip_train:
        steps.append(
            CommandStep(
                name="Train forecast model",
                cwd=root,
                command=(
                    config.python_executable,
                    "-m",
                    "src.ml.train_forecast_model",
                    "--data-dir",
                    str(config.processed_dir),
                    "--model-dir",
                    str(config.model_dir),
                    "--n-estimators",
                    str(config.n_estimators),
                    "--max-depth",
                    str(config.max_depth),
                    "--min-samples-leaf",
                    str(config.min_samples_leaf),
                    "--max-samples",
                    str(config.max_samples),
                    "--random-state",
                    str(config.random_seed),
                ),
            )
        )

    if not config.skip_predictions:
        steps.append(
            CommandStep(
                name="Generate forecast, stockout, and anomaly outputs",
                cwd=root,
                command=(
                    config.python_executable,
                    "-m",
                    "src.ml.generate_predictions",
                    "--data-dir",
                    str(config.processed_dir),
                    "--model-path",
                    str(config.model_dir / "retailiq_forecast_model.pkl"),
                    "--output-dir",
                    str(config.output_dir),
                ),
            )
        )

    if not config.skip_ml_load:
        command = [
            config.python_executable,
            "-m",
            "src.ingestion.load_ml_outputs_to_snowflake",
            "--output-dir",
            str(config.output_dir),
        ]
        _append_if(command, config.truncate_first, "--truncate-first")
        steps.append(CommandStep(name="Load ML output tables into Snowflake", cwd=root, command=tuple(command)))

    if not config.skip_dbt:
        steps.append(CommandStep(name="Build dbt marts", cwd=config.dbt_dir, command=(config.dbt_executable, "run")))
        steps.append(CommandStep(name="Test dbt marts", cwd=config.dbt_dir, command=(config.dbt_executable, "test")))

    return steps


def format_command(command: tuple[str, ...]) -> str:
    """Return a shell-readable command string without executing it."""
    return shlex.join(command)


def run_step(step: CommandStep, env: dict[str, str], dry_run: bool = False) -> None:
    """Run one command step with clear terminal output."""
    print(f"\n==> {step.name}")
    print(format_command(step.command))
    if dry_run:
        return
    subprocess.run(step.command, cwd=step.cwd, env=env, check=True)


def _runtime_env(snowflake_passcode: str | None, prompt_passcode: bool) -> dict[str, str]:
    env = os.environ.copy()
    passcode = snowflake_passcode
    if prompt_passcode:
        passcode = getpass("Snowflake MFA code: ")
    if passcode:
        env["SNOWFLAKE_PASSCODE"] = passcode
    return env


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RetailIQ Phase 2 workflow.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/walmart"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed/walmart"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/ml_outputs"))
    parser.add_argument("--dbt-dir", type=Path, default=Path("dbt_retailiq"))
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--dbt-executable", default="dbt")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=50)
    parser.add_argument("--max-depth", type=int, default=16)
    parser.add_argument("--min-samples-leaf", type=int, default=5)
    parser.add_argument("--max-samples", type=float, default=0.65)
    parser.add_argument("--truncate-first", action="store_true")
    parser.add_argument("--local-only", action="store_true", help="Run prep, training, and local ML output generation only.")
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--skip-raw-load", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-predictions", action="store_true")
    parser.add_argument("--skip-ml-load", action="store_true")
    parser.add_argument("--skip-dbt", action="store_true")
    parser.add_argument("--upload-gcs", action="store_true")
    parser.add_argument("--gcs-prefix", default="retailiq/raw")
    parser.add_argument("--snowflake-passcode", help="Current MFA code. Prefer --prompt-passcode for interactive use.")
    parser.add_argument("--prompt-passcode", action="store_true", help="Prompt securely for the current Snowflake MFA code.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command plan without executing it.")
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> Phase2PipelineConfig:
    root = _project_root()
    local_only = bool(args.local_only)
    return Phase2PipelineConfig(
        project_root=root,
        python_executable=args.python_executable,
        dbt_executable=args.dbt_executable,
        input_dir=args.input_dir,
        processed_dir=args.processed_dir,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        dbt_dir=root / args.dbt_dir,
        random_seed=args.random_seed,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        max_samples=args.max_samples,
        truncate_first=args.truncate_first,
        skip_prepare=args.skip_prepare,
        skip_raw_load=local_only or args.skip_raw_load,
        skip_train=args.skip_train,
        skip_predictions=args.skip_predictions,
        skip_ml_load=local_only or args.skip_ml_load,
        skip_dbt=local_only or args.skip_dbt,
        upload_gcs=args.upload_gcs,
        gcs_prefix=args.gcs_prefix,
    )


def main() -> None:
    args = parse_args()
    config = config_from_args(args)
    steps = build_phase2_steps(config)
    env = _runtime_env(args.snowflake_passcode, args.prompt_passcode)

    print("RetailIQ Phase 2 workflow")
    print(f"Project root: {config.project_root}")
    print(f"Steps: {len(steps)}")

    for step in steps:
        run_step(step, env=env, dry_run=args.dry_run)

    if args.dry_run:
        print("\nDry run complete. No commands were executed.")
    else:
        print("\nPhase 2 workflow complete.")


if __name__ == "__main__":
    main()
