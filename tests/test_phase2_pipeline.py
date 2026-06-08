from __future__ import annotations

from pathlib import Path

from src.pipelines.run_phase2 import Phase2PipelineConfig, build_phase2_steps, format_command


def make_config(**overrides) -> Phase2PipelineConfig:
    config = {
        "project_root": Path("/repo"),
        "python_executable": "python",
        "dbt_executable": "dbt",
        "input_dir": Path("data/raw/walmart"),
        "processed_dir": Path("data/processed/walmart"),
        "model_dir": Path("models"),
        "output_dir": Path("data/ml_outputs"),
        "dbt_dir": Path("/repo/dbt_retailiq"),
        "random_seed": 42,
        "n_estimators": 50,
        "max_depth": 16,
        "min_samples_leaf": 5,
        "max_samples": 0.65,
        "truncate_first": True,
        "skip_prepare": False,
        "skip_raw_load": False,
        "skip_train": False,
        "skip_predictions": False,
        "skip_ml_load": False,
        "skip_dbt": False,
        "upload_gcs": False,
        "gcs_prefix": "retailiq/raw",
    }
    config.update(overrides)
    return Phase2PipelineConfig(**config)


def test_local_only_phase2_plan_skips_snowflake_and_dbt() -> None:
    steps = build_phase2_steps(
        make_config(
            skip_raw_load=True,
            skip_ml_load=True,
            skip_dbt=True,
        )
    )

    assert [step.name for step in steps] == [
        "Prepare Walmart canonical CSVs",
        "Train forecast model",
        "Generate forecast, stockout, and anomaly outputs",
    ]


def test_full_phase2_plan_loads_raw_ml_and_runs_dbt() -> None:
    steps = build_phase2_steps(make_config())
    commands = [format_command(step.command) for step in steps]

    assert [step.name for step in steps][-4:] == [
        "Generate forecast, stockout, and anomaly outputs",
        "Load ML output tables into Snowflake",
        "Build dbt marts",
        "Test dbt marts",
    ]
    assert "--truncate-first" in commands[1]
    assert "--truncate-first" in commands[4]


def test_phase2_plan_can_include_gcs_upload() -> None:
    steps = build_phase2_steps(make_config(upload_gcs=True, skip_raw_load=True, skip_ml_load=True, skip_dbt=True))

    assert [step.name for step in steps][:2] == [
        "Prepare Walmart canonical CSVs",
        "Upload prepared CSVs to GCS",
    ]
