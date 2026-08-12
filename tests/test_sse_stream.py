import asyncio
import pytest
from app.services.trainer_engine import trainer_engine


@pytest.mark.anyio
async def test_sse_stream_response_format():
    """Verify Server-Sent Events (SSE) telemetry streaming output format."""
    sub_gen = trainer_engine.subscribe()

    task = asyncio.create_task(anext(sub_gen))
    await asyncio.sleep(0.01)

    test_packet = {"type": "telemetry", "step": 1, "loss": 0.42}
    trainer_engine._notify_subscribers(test_packet)

    sse_frame = await task
    assert sse_frame.startswith("data: ")
    assert '"type": "telemetry"' in sse_frame
    assert '"loss": 0.42' in sse_frame
