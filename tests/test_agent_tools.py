import pytest

from jax_agent import safe_path, analyze_code

def test_safe_path_rejects_env():
    with pytest.raises(ValueError):
        safe_path(".env")


def test_safe_path_rejects_outside_project():
    with pytest.raises(ValueError):
        safe_path("../outside.py")


def test_analyze_code_detects_syntax_error():
    result = analyze_code(
        "if True print('hello')",
        "example.py",
    )

    assert "Syntax error" in result


def test_analyze_code_accepts_valid_code():
    result = analyze_code(
        "print('hello')",
        "example.py",
    )

    assert "syntax check passed" in result.lower()