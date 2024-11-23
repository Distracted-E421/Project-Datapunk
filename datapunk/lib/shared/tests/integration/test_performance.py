import pytest
import asyncio
import time
from typing import List, Dict
import json

@pytest.mark.asyncio
async def test_concurrent_operations(services):
    """Test concurrent operations across services"""
    start_time = time.time()
    operation_count = 100
    
    async def single_operation(i: int):
        # Cache operation
        cache_key = f"test:concurrent:{i}"
        await services["cache"].set(cache_key, {"index": i})
        
        # Database operation
        await services["db"].execute(
            """
            INSERT INTO test_events (event_type, payload)
            VALUES ($1, $2)
            """,
            "concurrent_test",
            json.dumps({"operation": i})
        )
        
        # Message operation
        await services["mq"].publish(
            "test_concurrent",
            "test.concurrent",
            {"operation": i}
        )
    
    # Run concurrent operations
    tasks = [single_operation(i) for i in range(operation_count)]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    
    # Verify results
    db_count = await services["db"].execute(
        "SELECT COUNT(*) FROM test_events WHERE event_type = $1",
        "concurrent_test"
    )
    
    assert db_count == operation_count
    print(f"Completed {operation_count} concurrent operations in {duration:.2f} seconds")

@pytest.mark.asyncio
async def test_load_distribution(services):
    """Test load distribution across services"""
    message_count = 1000
    chunk_size = 100
    received_count = 0
    
    async def process_message(message: Dict):
        nonlocal received_count
        # Simulate processing
        await asyncio.sleep(0.001)
        received_count += 1
    
    # Subscribe to test channel
    await services["mq"].subscribe(
        "test_load",
        "load.test",
        process_message
    )
    
    # Send messages in chunks
    for i in range(0, message_count, chunk_size):
        tasks = []
        for j in range(chunk_size):
            tasks.append(
                services["mq"].publish(
                    "test_load",
                    "load.test",
                    {"index": i + j}
                )
            )
        await asyncio.gather(*tasks)
    
    # Wait for processing
    await asyncio.sleep(2)
    
    assert received_count == message_count 