# datapunk/datapunk-stream/tests/test_websocket.py

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/test-client-123"
    
    async with websockets.connect(uri) as websocket:
        # Test message
        test_message = {
            "message": "Hello, this is a test message"
        }
        
        # Send message
        await websocket.send(json.dumps(test_message))
        print(f"Sent: {test_message}")
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # Send another message
        test_message2 = {
            "message": "How are you doing?"
        }
        await websocket.send(json.dumps(test_message2))
        print(f"Sent: {test_message2}")
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received: {response}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test_websocket())