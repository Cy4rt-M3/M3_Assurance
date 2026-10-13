class _FakeClient:
    response: _FakeResponse

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    async def get(
        self, _url: str, params: dict[str, str] | None = None
    ) -> _FakeResponse:
        assert params is not None
        return type(self).response


def _patch_client(monkeypatch: pytest.MonkeyPatch, response: _FakeResponse) -> None:
    _FakeClient.response = response
    monkeypatch.setattr(threat_intel.httpx, "AsyncClient", _FakeClient)
