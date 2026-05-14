import pytest

from voice_to_text__app.domain.models import TranscribeConfig
from voice_to_text__app.domain.run_logic import (
    make_run_key,
    resolve_compute_type,
    txt_name_for_bench,
    txt_name_for_prod,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cfg(**overrides) -> TranscribeConfig:
    defaults = dict(
        model="large-v3",
        device="cpu",
        compute_type=None,
        threads=4,
        workers=1,
        beam_size=5,
        patience=1.0,
        vad=False,
        lang="auto",
    )
    defaults.update(overrides)
    return TranscribeConfig(**defaults)


# ---------------------------------------------------------------------------
# resolve_compute_type
# ---------------------------------------------------------------------------

class TestResolveComputeType:
    def test_explicit_compute_type_returned_unchanged(self):
        cfg = make_cfg(compute_type="int8")
        assert resolve_compute_type(cfg) == "int8"

    def test_cuda_without_explicit_type_returns_float16(self):
        cfg = make_cfg(device="cuda", compute_type=None)
        assert resolve_compute_type(cfg) == "float16"

    def test_cpu_without_explicit_type_returns_int8(self):
        cfg = make_cfg(device="cpu", compute_type=None)
        assert resolve_compute_type(cfg) == "int8"

    def test_explicit_type_overrides_cuda_default(self):
        cfg = make_cfg(device="cuda", compute_type="int8_float16")
        assert resolve_compute_type(cfg) == "int8_float16"

    def test_explicit_type_overrides_cpu_default(self):
        cfg = make_cfg(device="cpu", compute_type="float32")
        assert resolve_compute_type(cfg) == "float32"

    def test_device_case_insensitive(self):
        cfg = make_cfg(device="CUDA", compute_type=None)
        assert resolve_compute_type(cfg) == "float16"


# ---------------------------------------------------------------------------
# make_run_key
# ---------------------------------------------------------------------------

class TestMakeRunKey:
    def test_key_contains_target_id(self):
        key = make_run_key("target_abc", make_cfg(), "int8")
        assert "target_abc" in key

    def test_key_contains_model(self):
        key = make_run_key("t", make_cfg(model="medium"), "int8")
        assert "medium" in key

    def test_key_contains_device(self):
        key = make_run_key("t", make_cfg(device="cpu"), "int8")
        assert "cpu" in key

    def test_key_contains_compute_type(self):
        key = make_run_key("t", make_cfg(), "int8")
        assert "int8" in key

    def test_key_contains_threads(self):
        key = make_run_key("t", make_cfg(threads=8), "int8")
        assert "thr=8" in key

    def test_key_contains_workers(self):
        key = make_run_key("t", make_cfg(workers=3), "int8")
        assert "wrk=3" in key

    def test_key_contains_beam_size(self):
        key = make_run_key("t", make_cfg(beam_size=10), "int8")
        assert "beam=10" in key

    def test_key_contains_patience(self):
        key = make_run_key("t", make_cfg(patience=1.5), "int8")
        assert "pat=1.5" in key

    def test_vad_true_encoded_as_1(self):
        key = make_run_key("t", make_cfg(vad=True), "int8")
        assert "vad=1" in key

    def test_vad_false_encoded_as_0(self):
        key = make_run_key("t", make_cfg(vad=False), "int8")
        assert "vad=0" in key

    def test_key_contains_lang(self):
        key = make_run_key("t", make_cfg(lang="ru"), "int8")
        assert "lang=ru" in key

    def test_key_is_deterministic(self):
        cfg = make_cfg()
        assert make_run_key("t1", cfg, "int8") == make_run_key("t1", cfg, "int8")

    def test_different_targets_produce_different_keys(self):
        cfg = make_cfg()
        assert make_run_key("t1", cfg, "int8") != make_run_key("t2", cfg, "int8")

    def test_different_threads_produce_different_keys(self):
        assert (
            make_run_key("t", make_cfg(threads=4), "int8")
            != make_run_key("t", make_cfg(threads=8), "int8")
        )

    def test_different_compute_types_produce_different_keys(self):
        cfg = make_cfg()
        assert make_run_key("t", cfg, "int8") != make_run_key("t", cfg, "float16")

    def test_key_is_pipe_separated_string(self):
        key = make_run_key("t", make_cfg(), "int8")
        assert "|" in key
        assert len(key.split("|")) == 10  # exactly 10 parts


# ---------------------------------------------------------------------------
# txt_name_for_prod
# ---------------------------------------------------------------------------

class TestTxtNameForProd:
    def test_simple_name(self):
        assert txt_name_for_prod("interview") == "interview.txt"

    def test_name_with_underscores(self):
        assert txt_name_for_prod("audio_2024_01") == "audio_2024_01.txt"

    def test_always_ends_with_txt(self):
        assert txt_name_for_prod("anything").endswith(".txt")


# ---------------------------------------------------------------------------
# txt_name_for_bench
# ---------------------------------------------------------------------------

class TestTxtNameForBench:
    def test_starts_with_base_name(self):
        cfg = make_cfg()
        key = make_run_key("t", cfg, "int8")
        assert txt_name_for_bench("audio", key).startswith("audio__")

    def test_ends_with_txt(self):
        cfg = make_cfg()
        key = make_run_key("t", cfg, "int8")
        assert txt_name_for_bench("audio", key).endswith(".txt")

    def test_deterministic(self):
        cfg = make_cfg()
        key = make_run_key("t", cfg, "int8")
        assert txt_name_for_bench("audio", key) == txt_name_for_bench("audio", key)

    def test_different_keys_produce_different_names(self):
        key_a = make_run_key("t", make_cfg(threads=4), "int8")
        key_b = make_run_key("t", make_cfg(threads=8), "int8")
        assert txt_name_for_bench("audio", key_a) != txt_name_for_bench("audio", key_b)

    def test_different_base_names_produce_different_files(self):
        cfg = make_cfg()
        key = make_run_key("t", cfg, "int8")
        assert txt_name_for_bench("file_a", key) != txt_name_for_bench("file_b", key)

    def test_suffix_has_fixed_length(self):
        """The hash suffix (10 chars) gives predictable filename length."""
        cfg = make_cfg()
        key = make_run_key("t", cfg, "int8")
        name = txt_name_for_bench("base", key)
        # format: base__<10-char-hash>.txt
        suffix = name.removeprefix("base__").removesuffix(".txt")
        assert len(suffix) == 10