import pytest

from voice_to_text__app.application.bench.selection import _to_float, pick_best


# ---------------------------------------------------------------------------
# _to_float
# ---------------------------------------------------------------------------

class TestToFloat:
    def test_none_returns_none(self):
        assert _to_float(None) is None

    def test_empty_string_returns_none(self):
        assert _to_float("") is None

    def test_valid_int(self):
        assert _to_float(42) == 42.0

    def test_valid_float(self):
        assert _to_float(3.14) == pytest.approx(3.14)

    def test_valid_string_float(self):
        assert _to_float("2.5") == pytest.approx(2.5)

    def test_invalid_string_returns_none(self):
        assert _to_float("abc") is None

    def test_zero_int(self):
        assert _to_float(0) == 0.0

    def test_zero_string(self):
        assert _to_float("0") == 0.0

    def test_object_returns_none(self):
        assert _to_float(object()) is None


# ---------------------------------------------------------------------------
# pick_best
# ---------------------------------------------------------------------------

class TestPickBest:

    # --- edge cases ---

    def test_empty_list_returns_none(self):
        assert pick_best([]) is None

    def test_all_failed_returns_none(self):
        rows = [
            {"status": "failed", "wer": 0.1, "wall_time_sec": 1.0},
            {"status": "failed", "wer": 0.2, "wall_time_sec": 2.0},
        ]
        assert pick_best(rows) is None

    def test_single_ok_row_is_returned(self):
        row = {"status": "ok", "wall_time_sec": 5.0, "rtf": 0.5}
        assert pick_best([row]) is row

    def test_no_status_field_treated_as_ok(self):
        row = {"wall_time_sec": 3.0}
        assert pick_best([row]) is row

    # --- failed filtering ---

    def test_failed_rows_are_excluded(self):
        good = {"status": "ok", "wall_time_sec": 5.0}
        bad = {"status": "failed", "wall_time_sec": 1.0}
        assert pick_best([bad, good]) is good

    def test_only_ok_rows_compete(self):
        bad1 = {"status": "failed", "wall_time_sec": 0.1}
        bad2 = {"status": "failed", "wall_time_sec": 0.2}
        good = {"status": "ok", "wall_time_sec": 99.0}
        assert pick_best([bad1, bad2, good]) is good

    # --- no-wer mode: sort by wall then rtf ---

    def test_no_wer_picks_fastest_wall(self):
        slow = {"status": "ok", "wall_time_sec": 10.0, "rtf": 1.0}
        fast = {"status": "ok", "wall_time_sec": 2.0, "rtf": 0.2}
        assert pick_best([slow, fast]) is fast

    def test_no_wer_tiebreak_by_rtf(self):
        a = {"status": "ok", "wall_time_sec": 5.0, "rtf": 0.8}
        b = {"status": "ok", "wall_time_sec": 5.0, "rtf": 0.3}
        assert pick_best([a, b]) is b

    # --- wer mode: sort by wer → cer → wall → rtf ---

    def test_wer_mode_lower_wer_wins_despite_slower_speed(self):
        worse = {"status": "ok", "wer": 0.5, "cer": 0.5, "wall_time_sec": 1.0, "rtf": 0.1}
        better = {"status": "ok", "wer": 0.1, "cer": 0.1, "wall_time_sec": 10.0, "rtf": 1.0}
        assert pick_best([worse, better]) is better

    def test_wer_tiebreak_by_cer(self):
        a = {"status": "ok", "wer": 0.1, "cer": 0.2, "wall_time_sec": 1.0, "rtf": 0.1}
        b = {"status": "ok", "wer": 0.1, "cer": 0.05, "wall_time_sec": 5.0, "rtf": 0.5}
        assert pick_best([a, b]) is b

    def test_wer_tiebreak_by_wall_after_cer(self):
        a = {"status": "ok", "wer": 0.1, "cer": 0.1, "wall_time_sec": 10.0, "rtf": 0.5}
        b = {"status": "ok", "wer": 0.1, "cer": 0.1, "wall_time_sec": 3.0, "rtf": 0.5}
        assert pick_best([a, b]) is b

    def test_row_without_wer_loses_to_row_with_wer_in_wer_mode(self):
        with_wer = {"status": "ok", "wer": 0.3, "cer": 0.1, "wall_time_sec": 5.0}
        without_wer = {"status": "ok", "wer": None, "cer": None, "wall_time_sec": 1.0}
        # has_wer is True because at least one row has a valid wer
        # None row gets wer=1e18, so with_wer wins
        assert pick_best([without_wer, with_wer]) is with_wer

    # --- mode detection ---

    def test_single_wer_value_activates_wer_mode(self):
        """Even a single wer score triggers wer-based ranking."""
        scored = {"status": "ok", "wer": 0.5, "wall_time_sec": 5.0}
        fast_unscored = {"status": "ok", "wer": None, "wall_time_sec": 0.1}
        result = pick_best([scored, fast_unscored])
        assert result is scored