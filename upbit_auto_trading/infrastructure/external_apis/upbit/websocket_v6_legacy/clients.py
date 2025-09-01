import asyncio

class UpbitWebSocketPublicClient:
    """
    Handles the low-level connection to the Upbit Public WebSocket API.
    
    This class is managed by the GlobalWebSocketManager and should not be used directly.
    """
    def __init__(self, on_message_callback: asyncio.Queue):
        self._queue = on_message_callback
        self._connection = None
        self._is_connected = False

    async def connect(self):
        """Establishes the WebSocket connection."""
        print("Public client connecting...")
        self._is_connected = True
        # Actual connection logic using a library like 'websockets' will go here.
        # e.g., self._connection = await websockets.connect("wss://api.upbit.com/websocket/v1")
        # asyncio.create_task(self._listen())

    async def _listen(self):
        """Listens for incoming messages and puts them into the queue."""
        # while self._is_connected:
        #     message = await self._connection.recv()
        #     await self._queue.put(("public", message))
        pass

    async def send(self, message: str):
        """Sends a message to the WebSocket server."""
        # if self._is_connected:
        #     await self._connection.send(message)
        pass

    async def close(self):
        """Closes the WebSocket connection."""
        self._is_connected = False
        # if self._connection:
        #     await self._connection.close()
        print("Public client disconnected.")

    def is_connected(self) -> bool:
        return self._is_connected


class UpbitWebSocketPrivateClient:
    """
    Handles the low-level connection to the Upbit Private WebSocket API.
    
    This class is managed by the GlobalWebSocketManager and should not be used directly.
    """
    def __init__(self, on_message_callback: asyncio.Queue):
        self._queue = on_message_callback
        self._connection = None
        self._is_connected = False

    async def connect(self, access_key: str, secret_key: str):
        """Establishes the WebSocket connection with JWT authentication."""
        print("Private client connecting...")
        # 1. Generate JWT token using upbit_auth module
        # 2. Connect to the websocket endpoint
        # 3. Send auth message
        self._is_connected = True

    async def send(self, message: str):
        """Sends a message to the WebSocket server."""
        pass

    async def close(self):
        """Closes the WebSocket connection."""
        self._is_connected = False
        print("Private client disconnected.")

    def is_connected(self) -> bool:
        return self._is_connected
