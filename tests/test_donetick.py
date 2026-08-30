import pytest
import httpx
from app.sources.donetick import DoneTickSource

@pytest.mark.anyio
async def test_donetick_fetch_success():
    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if url_str.endswith("/eapi/v1/chore"):
                chores = [
                    {
                        "id": 1,
                        "name": "Chore 1",
                        "labels": ["home"],
                        "nextDueDate": "2025-01-01T10:00:00Z",
                        "status": 0,
                    },
                    {
                        "id": 2,
                        "name": "Chore 2",
                        "labels": ["work"],
                        "nextDueDate": "2025-01-01T10:00:00Z",
                        "status": 1,
                    },
                ]
                return httpx.Response(200, json=chores)
            elif "/chores/1/details" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "res": {
                            "subTasks": [
                                {"id": "sub1", "name": "Subtask 1", "status": 0}
                            ]
                        }
                    },
                )
            elif "/chores/2/details" in url_str:
                # Test error handling on detail endpoint
                return httpx.Response(500, json={"error": "failed"})
            return httpx.Response(404)

    source = DoneTickSource()
    async with httpx.AsyncClient(transport=MockTransport()) as client:
        # Patch AsyncClient in module or pass custom client
        pass

    # We can test DoneTickSource with transport mock
    orig_client = httpx.AsyncClient
    transport = MockTransport()

    def custom_client(*args, **kwargs):
        kwargs["transport"] = transport
        return orig_client(*args, **kwargs)

    httpx.AsyncClient = custom_client
    try:
        res = await source.fetch(date_filter="all")
    finally:
        httpx.AsyncClient = orig_client

    assert res["ok"] is True
    assert len(res["tasks"]) == 2
    task1 = res["tasks"][0]
    assert task1["id"] == "1"
    assert task1["title"] == "Chore 1"
    assert len(task1["subtasks"]) == 1
    assert task1["subtasks"][0]["title"] == "Subtask 1"

    task2 = res["tasks"][1]
    assert task2["id"] == "2"
    assert task2["completed"] is True
    assert len(task2["subtasks"]) == 0
