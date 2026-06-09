"""OpenAI-backed RetailIQ analyst orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import pandas as pd
from openai import OpenAI
from openai import OpenAIError

from src.ai.prompt_templates import ANSWER_SYNTHESIS_PROMPT, SYSTEM_PROMPT
from src.ai.sql_agent import SqlGenerationResult, execute_governed_sql, generate_sql_from_question
from src.utils.config import AppConfig, get_config


@dataclass(frozen=True)
class AnalystResponse:
    """Complete response from the RetailIQ analyst flow."""

    question: str
    answer: str
    sql: str
    rationale: str
    row_count: int
    result_preview: list[dict[str, Any]]
    used_openai: bool
    model: str | None = None
    warning: str | None = None


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 4)
    return value


def dataframe_preview(df: pd.DataFrame, max_rows: int = 12) -> list[dict[str, Any]]:
    """Return a JSON-safe preview of a Snowflake result frame."""
    if df.empty:
        return []
    records = df.head(max_rows).to_dict(orient="records")
    return [{key: _clean_value(value) for key, value in record.items()} for record in records]


def _format_metric_value(key: str, value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        if any(token in key for token in ("sales", "demand", "inventory")):
            return f"${value:,.0f}"
        if "wape" in key or "rate" in key:
            return f"{value:.1%}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def deterministic_answer(question: str, result_df: pd.DataFrame, sql_result: SqlGenerationResult) -> str:
    """Build a useful non-LLM answer from a governed SQL result."""
    if result_df.empty:
        return "I ran the governed Snowflake query, but it returned no rows for this question."

    preview = dataframe_preview(result_df, max_rows=3)
    first_row = preview[0]
    if len(result_df) == 1:
        metrics = ", ".join(
            f"{str(key).replace('_', ' ')} = {_format_metric_value(str(key), value)}"
            for key, value in first_row.items()
        )
        return f"Snowflake returned one summary row: {metrics}."

    lead = ", ".join(
        f"{str(key).replace('_', ' ')}: {_format_metric_value(str(key), value)}"
        for key, value in first_row.items()
    )
    return (
        f"Snowflake returned {len(result_df):,} rows for this question. "
        f"The top row is {lead}. Review the query result preview for the remaining rows."
    )


def _parse_answer(raw_content: str) -> str:
    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content.strip()
    return str(payload.get("answer", "")).strip()


def synthesize_openai_answer(
    question: str,
    sql: str,
    result_df: pd.DataFrame,
    config: AppConfig,
) -> str:
    """Use OpenAI to synthesize a concise answer from SQL results."""
    client = OpenAI(api_key=config.openai_api_key)
    payload = {
        "question": question,
        "sql": sql,
        "row_count": int(len(result_df)),
        "columns": list(result_df.columns),
        "preview_rows": dataframe_preview(result_df),
    }
    response = client.chat.completions.create(
        model=config.openai_model or "gpt-5-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": ANSWER_SYNTHESIS_PROMPT},
            {"role": "user", "content": json.dumps(payload, default=str)},
        ],
    )
    answer = _parse_answer(response.choices[0].message.content or "")
    return answer or deterministic_answer(question, result_df, SqlGenerationResult(sql, "", True, config.openai_model))


def answer_business_question(
    question: str,
    config: AppConfig | None = None,
    row_limit: int = 100,
) -> AnalystResponse:
    """Answer a business question using governed SQL and optional OpenAI synthesis."""
    config = config or get_config()
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be blank.")

    sql_result = generate_sql_from_question(question, config=config, row_limit=row_limit)
    result_df = execute_governed_sql(sql_result.sql, config=config, row_limit=row_limit)

    warning = sql_result.warning
    if config.openai_api_key and sql_result.used_openai:
        try:
            answer = synthesize_openai_answer(question, sql_result.sql, result_df, config)
            used_openai = True
        except OpenAIError:
            answer = deterministic_answer(question, result_df, sql_result)
            warning = "OpenAI answer synthesis failed, so RetailIQ used a deterministic summary."
            used_openai = False
    else:
        answer = deterministic_answer(question, result_df, sql_result)
        used_openai = False

    return AnalystResponse(
        question=question,
        answer=answer,
        sql=sql_result.sql,
        rationale=sql_result.rationale,
        row_count=int(len(result_df)),
        result_preview=dataframe_preview(result_df),
        used_openai=used_openai,
        model=sql_result.model or config.openai_model,
        warning=warning,
    )
