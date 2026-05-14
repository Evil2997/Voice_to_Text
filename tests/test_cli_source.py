import pytest

from voice_to_text__app.infrastructure.config.cli_source import _coerce_value, parse_argv


# ---------------------------------------------------------------------------
# _coerce_value
# ---------------------------------------------------------------------------

class TestCoerceValue:

    # --- booleans ---

    @pytest.mark.parametrize("raw", ["true", "True", "TRUE", "1", "yes", "y", "on"])
    def test_truthy_strings(self, raw):
        assert _coerce_value(raw) is True

    @pytest.mark.parametrize("raw", ["false", "False", "FALSE", "0", "no", "n", "off"])
    def test_falsy_strings(self, raw):
        assert _coerce_value(raw) is False

    # --- integers ---

    def test_positive_integer(self):
        result = _coerce_value("42")
        assert result == 42
        assert isinstance(result, int)

    def test_negative_integer(self):
        result = _coerce_value("-5")
        assert result == -5
        assert isinstance(result, int)

    def test_zero_as_integer(self):
        # "0" is falsy bool string → returns False, not int 0
        assert _coerce_value("0") is False

    # --- floats ---

    def test_float_with_dot(self):
        result = _coerce_value("3.14")
        assert result == pytest.approx(3.14)

    def test_float_with_scientific_notation(self):
        result = _coerce_value("1e3")
        assert result == pytest.approx(1000.0)

    def test_negative_float(self):
        result = _coerce_value("-2.5")
        assert result == pytest.approx(-2.5)

    # --- plain strings ---

    def test_model_name_stays_string(self):
        assert _coerce_value("large-v3") == "large-v3"

    def test_path_like_stays_string(self):
        assert _coerce_value("./audio.mp3") == "./audio.mp3"

    def test_arbitrary_string_stays_string(self):
        assert _coerce_value("hello world") == "hello world"


# ---------------------------------------------------------------------------
# parse_argv
# ---------------------------------------------------------------------------

class TestParseArgv:
    def test_empty_returns_empty_dict(self):
        assert parse_argv([]) == {}

    def test_simple_string_value(self):
        assert parse_argv(["--mode", "prod"]) == {"mode": "prod"}

    def test_integer_value_coerced(self):
        result = parse_argv(["--whisper.threads", "8"])
        assert result["whisper"]["threads"] == 8

    def test_nested_key_creates_nested_dict(self):
        result = parse_argv(["--whisper.threads", "4"])
        assert "whisper" in result
        assert "threads" in result["whisper"]

    def test_deeply_nested_key(self):
        result = parse_argv(["--a.b.c", "42"])
        assert result["a"]["b"]["c"] == 42

    def test_flag_without_value_becomes_true(self):
        result = parse_argv(["--whisper.vad"])
        assert result["whisper"]["vad"] is True

    def test_flag_before_another_flag(self):
        result = parse_argv(["--whisper.vad", "--mode", "prod"])
        assert result["whisper"]["vad"] is True
        assert result["mode"] == "prod"

    def test_comma_separated_ints_become_tuple(self):
        result = parse_argv(["--bench.threads", "4,8,12"])
        assert result["bench"]["threads"] == (4, 8, 12)

    def test_comma_separated_strings_become_tuple(self):
        result = parse_argv(["--bench.computes", "int8,float16"])
        assert result["bench"]["computes"] == ("int8", "float16")

    def test_multiple_args_parsed(self):
        result = parse_argv([
            "--mode", "bench",
            "--whisper.model", "large-v3",
            "--whisper.threads", "4",
        ])
        assert result["mode"] == "bench"
        assert result["whisper"]["model"] == "large-v3"
        assert result["whisper"]["threads"] == 4

    def test_non_flag_tokens_skipped(self):
        result = parse_argv(["positional", "--mode", "prod"])
        assert result == {"mode": "prod"}

    def test_bool_value_coerced(self):
        result = parse_argv(["--whisper.vad", "true"])
        assert result["whisper"]["vad"] is True

    def test_float_value_coerced(self):
        result = parse_argv(["--whisper.patience", "1.5"])
        assert result["whisper"]["patience"] == pytest.approx(1.5)