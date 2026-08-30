import asyncio
import time
from typing import Any
import httpx
from app.sources.donetick import DoneTickSource

class MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, num_chores: int = 50, delay_per_request: float = 0.05) -> None:
        self.num_chores = num_chores
        self.delay_per_request = delay_per_request

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(self.delay_per_request)
        url_str = str(request.url)
        if url_str.endswith("/eapi/v1/chore"):
            chores = [
                {
                    "id": i,
                    "name": f"Chore {i}",
                    "labels": ["home"],
                    "nextDueDate": "2025-01-01T10:00:00Z",
                    "status": 0,
                    "subTasks": [],
                }
                for i in range(1, self.num_chores + 1)
            ]
            return httpx.Response(200, json=chores)
        elif "/details" in url_str:
            chore_id = url_str.split("/")[-2]
            return httpx.Response(
                200,
                json={
                    "res": {
                        "subTasks": [
                            {"id": f"sub_{chore_id}_1", "name": f"Subtask for {chore_id}"}
                        ]
                    }
                },
            )
        return httpx.Response(404, json={"error": "not found"})


async def run_benchmark():
    num_chores = 50
    delay = 0.02  # 20ms delay per HTTP request simulate latency
    transport = MockTransport(num_chores=num_chores, delay_per_request=delay)

    # We patch httpx.AsyncClient to use our transport in DoneTickSource.fetch
    orig_client = httpx.AsyncClient

    def custom_client(*args, **kwargs):
        kwargs["transport"] = transport
        return orig_client(*args, **kwargs)

    httpx.AsyncClient = custom_client

    source = DoneTickSource()
    start_time = time.perf_counter()
    result = await source.fetch(date_filter="all")
    elapsed = time.perf_counter() - start_time

    httpx.AsyncClient = orig_client

    print(f"Fetched {len(result['tasks'])} tasks in {elapsed:.4f} seconds.")
    return elapsed


if __name__ == "__main__":
    asyncio.run(run_benchmark())
