from voice_to_text__app.infrastructure.audio.targets import _hash, is_url


# ---------------------------------------------------------------------------
# is_url
# ---------------------------------------------------------------------------

class TestIsUrl:
    def test_http_scheme_is_url(self):
        assert is_url("http://example.com") is True

    def test_https_scheme_is_url(self):
        assert is_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_absolute_path_is_not_url(self):
        assert is_url("/home/user/audio.mp3") is False

    def test_relative_path_is_not_url(self):
        assert is_url("audio.mp3") is False

    def test_empty_string_is_not_url(self):
        assert is_url("") is False

    def test_ftp_scheme_is_not_url(self):
        # only http/https are supported
        assert is_url("ftp://example.com") is False

    def test_url_with_query_params(self):
        assert is_url("https://example.com/watch?v=abc&t=10") is True

    def test_http_without_double_slash_is_not_url(self):
        assert is_url("http:example.com") is False


# ---------------------------------------------------------------------------
# _hash
# ---------------------------------------------------------------------------

class TestHash:
    def test_returns_exactly_12_chars(self):
        assert len(_hash("some text")) == 12

    def test_result_is_string(self):
        assert isinstance(_hash("hello"), str)

    def test_deterministic_same_input(self):
        assert _hash("hello") == _hash("hello")

    def test_different_inputs_produce_different_hashes(self):
        assert _hash("abc") != _hash("xyz")

    def test_empty_string_produces_valid_hash(self):
        h = _hash("")
        assert isinstance(h, str)
        assert len(h) == 12

    def test_unicode_input(self):
        h = _hash("привет мир")
        assert len(h) == 12

    def test_long_input_still_12_chars(self):
        long_text = "a" * 10_000
        assert len(_hash(long_text)) == 12

    def test_hash_is_hex(self):
        h = _hash("test")
        assert all(c in "0123456789abcdef" for c in h)