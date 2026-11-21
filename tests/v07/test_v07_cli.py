from __future__ import annotations

from types import SimpleNamespace

from industrialops.evaluation.v07 import run


def test_judge_profile_executes_the_approved_suite_before_writing_the_unified_report(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / "data" / "evaluation").mkdir(parents=True)
    (tmp_path / "data" / "evaluation" / "scenario_eval_v1.jsonl").write_text("{}\n")
    (tmp_path / "data" / "evaluation" / "guardrail_eval_v1.jsonl").write_text("{}\n")
    suite = tmp_path / "approved.jsonl"
    suite.write_text("{}\n", encoding="utf-8")
    judge_env = tmp_path / "judge.env"
    judge_env.write_text("private", encoding="utf-8")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        run,
        "load_explicit_judge_configuration",
        lambda path: calls.append(("load-settings", path))
        or SimpleNamespace(
            evaluation_judge_provider="deepseek",
            evaluation_judge_model="deepseek-chat",
        ),
    )
    monkeypatch.setattr(
        run,
        "execute_live_judge_suite",
        lambda **kwargs: calls.append(("execute-suite", kwargs["suite_path"]))
        or (
            {
                "case_id": "approved-1",
                "hard_gate_passed": True,
                "judge_metrics": {
                    "ragas_faithfulness": 1.0,
                    "deepeval_faithfulness": 0.9,
                },
            },
        ),
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        run,
        "run_deterministic_evaluation",
        lambda **kwargs: captured.update(kwargs),
    )

    run.main(
        [
            "--project-root",
            str(tmp_path),
            "--run-id",
            "judge-live-001",
            "--profile",
            "judge",
            "--judge-env-file",
            str(judge_env),
            "--judge-suite-file",
            str(suite),
        ]
    )

    assert calls == [("load-settings", judge_env), ("execute-suite", suite)]
    assert captured["profile"] == "judge"
    assert captured["case_results"] == (
        {
            "case_id": "approved-1",
            "hard_gate_passed": True,
            "judge_metrics": {
                "ragas_faithfulness": 1.0,
                "deepeval_faithfulness": 0.9,
            },
        },
    )
    assert captured["framework_results"] == {
        "ragas": "completed",
        "deepeval": "completed",
        "judge": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "temperature": 0,
            "thinking": "disabled",
        },
    }


def test_judge_profile_propagates_framework_error_status(tmp_path, monkeypatch) -> None:
    (tmp_path / "data" / "evaluation").mkdir(parents=True)
    (tmp_path / "data" / "evaluation" / "scenario_eval_v1.jsonl").write_text("{}\n")
    (tmp_path / "data" / "evaluation" / "guardrail_eval_v1.jsonl").write_text("{}\n")
    suite = tmp_path / "approved.jsonl"
    suite.write_text("{}\n", encoding="utf-8")
    judge_env = tmp_path / "judge.env"
    judge_env.write_text("private", encoding="utf-8")
    monkeypatch.setattr(
        run,
        "load_explicit_judge_configuration",
        lambda _: SimpleNamespace(
            evaluation_judge_provider="deepseek",
            evaluation_judge_model="deepseek-chat",
        ),
    )
    monkeypatch.setattr(
        run,
        "execute_live_judge_suite",
        lambda **_: (
            {
                "case_id": "approved-1",
                "hard_gate_passed": True,
                "judge_status": "error",
                "judge_metrics": {
                    "ragas_faithfulness": None,
                    "deepeval_faithfulness": 0.9,
                },
                "judge_errors": {"ragas": "EVALUATION_RAGAS_JUDGE_FAILED"},
            },
        ),
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(run, "run_deterministic_evaluation", lambda **kwargs: captured.update(kwargs))

    run.main(
        [
            "--project-root",
            str(tmp_path),
            "--run-id",
            "judge-live-error-001",
            "--profile",
            "judge",
            "--judge-env-file",
            str(judge_env),
            "--judge-suite-file",
            str(suite),
        ]
    )

    assert captured["framework_results"] == {
        "ragas": "error",
        "deepeval": "completed",
        "judge": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "temperature": 0,
            "thinking": "disabled",
        },
    }
