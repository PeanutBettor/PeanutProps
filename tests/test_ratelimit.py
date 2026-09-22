import pytest
import requests

from peanut_soccer.http import FetchError, HttpClient, RateLimiter


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def test_first_call_does_not_wait():
    c = FakeClock()
    rl = RateLimiter(3.0, clock=c.now, sleep=c.sleep)
    assert rl.wait() == 0 and c.sleeps == []


def test_enforces_min_interval():
    c = FakeClock()
    rl = RateLimiter(3.0, clock=c.now, sleep=c.sleep)
    rl.wait()
    c.t += 1.0
    assert rl.wait() == pytest.approx(2.0)
    rl.wait()  # immediately again -> full 3s
    assert c.sleeps == [pytest.approx(2.0), pytest.approx(3.0)]


def test_no_wait_when_interval_already_elapsed():
    c = FakeClock()
    rl = RateLimiter(3.0, clock=c.now, sleep=c.sleep)
    rl.wait()
    c.t += 10
    assert rl.wait() == 0


def test_real_clock_spacing():
    import time
    rl = RateLimiter(0.2)
    t0 = time.monotonic()
    for _ in range(3):
        rl.wait()
    assert time.monotonic() - t0 >= 0.4


def test_default_interval_is_at_least_3s():
    assert RateLimiter().min_interval >= 3.0


class _Resp:
    def __init__(self, code):
        self.status_code = code
        self.content = b"{}"
        self.text = "{}"
        self.url = "https://example.test/x"


class _Session:
    def __init__(self, codes):
        self.codes = list(codes)
        self.headers = {}
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return _Resp(self.codes.pop(0))


def _client(codes, log):
    c = FakeClock()
    return HttpClient("t", limiter=RateLimiter(3.0, clock=c.now, sleep=c.sleep), session=_Session(codes),
                      backoff_base=1, sleep=lambda s: log.append(s),
                      on_fetch=lambda *a: log.append(a)), c


def test_retries_with_backoff_then_succeeds():
    log = []
    client, _ = _client([503, 429, 200], log)
    assert client.get("https://example.test/x").status == 200
    backoffs = [x for x in log if isinstance(x, (int, float))]
    assert backoffs == [1, 2]
    assert [x[2] for x in log if isinstance(x, tuple)] == ["503", "429", "200"]


def test_does_not_retry_403():
    log = []
    client, _ = _client([403], log)
    with pytest.raises(FetchError):
        client.get("https://example.test/x")
    assert client.session.calls == 1


def test_gives_up_after_max_retries():
    log = []
    client, _ = _client([503] * 10, log)
    client.max_retries = 2
    with pytest.raises(FetchError):
        client.get("https://example.test/x")
    assert client.session.calls == 3
