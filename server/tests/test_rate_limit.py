from app import rate_limit


def test_requests_under_the_limit_are_allowed(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 3)
    rate_limit.reset()
    for _ in range(3):
        rate_limit.check_rate_limit("client-a")


def test_the_request_over_the_limit_is_rejected(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 2)
    rate_limit.reset()
    rate_limit.check_rate_limit("client-b")
    rate_limit.check_rate_limit("client-b")
    try:
        rate_limit.check_rate_limit("client-b")
        assert False, "expected RateLimitExceeded"
    except rate_limit.RateLimitExceeded:
        pass


def test_clients_are_tracked_independently(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 1)
    rate_limit.reset()
    rate_limit.check_rate_limit("client-c")
    rate_limit.check_rate_limit("client-d")


def test_old_hits_outside_the_window_no_longer_count(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 1)
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_WINDOW_SECONDS", 10)
    rate_limit.reset()
    fake_now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: fake_now[0])
    rate_limit.check_rate_limit("client-e")
    fake_now[0] += 11
    rate_limit.check_rate_limit("client-e")


def test_reset_clears_all_tracked_clients(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 1)
    rate_limit.reset()
    rate_limit.check_rate_limit("client-f")
    rate_limit.reset()
    rate_limit.check_rate_limit("client-f")
