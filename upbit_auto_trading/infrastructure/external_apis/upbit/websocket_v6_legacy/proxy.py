import asyncio
import weakref
from typing import List, Callable, Coroutine, Dict, Any, Set

# Forward reference for type hinting
# from .global_manager import GlobalWebSocketManager
# from .events import TickerEvent, OrderbookEvent, TradeEvent, CandleEvent, MyOrderEvent, MyAssetEvent

class WebSocketClientProxy:
    """
    A proxy client for interacting with the WebSocket service.

    This class provides a simplified, component-specific interface to the global
    WebSocket manager. It handles automatic subscription cleanup when the object
    is garbage collected.
    """

    def __init__(self, client_id: str, owner_component: str = "default"):
        """
        Initializes the WebSocketClientProxy.

        Args:
            client_id (str): A unique identifier for this client instance.
                             It's recommended to use a format like '<module_name>_<instance_id>'.
            owner_component (str): A descriptive name of the component owning this proxy.
        """
        if not client_id:
            raise ValueError("client_id cannot be empty.")

        self.client_id = client_id
        self.owner_component = owner_component
        # self._manager = GlobalWebSocketManager.get_instance() # To be implemented

        # WeakRef-based cleanup to prevent resource leaks if the proxy is not properly closed.
        weakref.finalize(self, self._cleanup_subscriptions)
        print(f"WebSocketClientProxy '{self.client_id}' initialized.") # For debugging

    # --- Context Management ---

    async def __aenter__(self):
        """Enables use of 'async with' statement for automatic cleanup."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleans up all subscriptions created by this proxy upon exiting the 'async with' block."""
        await self.unsubscribe_all()

    # --- Public API (as defined in API_REFERENCE.md) ---

    async def subscribe_ticker(self, symbols: List[str], callback: Callable[..., Coroutine]):
        """Subscribes to the real-time ticker (current price) stream."""
        pass

    async def subscribe_orderbook(self, symbols: List[str], callback: Callable[..., Coroutine]):
        """Subscribes to the real-time orderbook stream."""
        pass

    async def subscribe_trade(self, symbols: List[str], callback: Callable[..., Coroutine]):
        """Subscribes to the real-time trade (execution) stream."""
        pass

    async def subscribe_candle(self, symbols: List[str], interval: str, callback: Callable[..., Coroutine]):
        """
        Subscribes to the real-time candle stream.
        
        Args:
            interval (str): Candle interval. e.g., "1m", "5m", "1h", "4h", "1d".
        """
        pass

    async def subscribe_my_orders(self, callback: Callable[..., Coroutine]):
        """Subscribes to real-time updates for the user's own orders (Private)."""
        pass

    async def subscribe_my_assets(self, callback: Callable[..., Coroutine]):
        """Subscribes to real-time updates for the user's own assets (Private)."""
        pass

    # --- Snapshot Data ---

    async def get_ticker_snapshot(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetches a one-time snapshot of the current ticker data."""
        return {}

    async def get_orderbook_snapshot(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetches a one-time snapshot of the current orderbook data."""
        return {}

    async def get_candle_snapshot(self, symbols: List[str], interval: str) -> Dict[str, Any]:
        """Fetches a one-time snapshot of the most recent candle data."""
        return {}

    # --- Subscription Management ---

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribes from a specific subscription using its ID."""
        pass

    async def unsubscribe_symbols(self, data_type: str, symbols: List[str]):
        """Removes specific symbols from a data type subscription."""
        pass

    async def unsubscribe_all(self):
        """Unsubscribes from all data streams associated with this proxy instance."""
        print(f"Cleaning up all subscriptions for client '{self.client_id}'.") # For debugging
        # await self._manager.unregister_component(self.client_id) # To be implemented

    async def get_active_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """Gets a list of all active subscriptions for this proxy."""
        return {}

    # --- Status & Health Check ---

    def is_public_available(self) -> bool:
        """Checks if the public WebSocket connection is currently active."""
        # return self._manager.is_public_connected()
        return False

    def is_private_available(self) -> bool:
        """Checks if the private WebSocket connection is currently active and authenticated."""
        # return self._manager.is_private_connected()
        return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Gets the overall status of the WebSocket system."""
        # return await self._manager.get_status()
        return {}

    async def health_check(self) -> Dict[str, Any]:
        """Performs a health check of the WebSocket system."""
        # return await self._manager.health_check()
        return {}
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Gets performance metrics of the WebSocket system."""
        # return await self._manager.get_metrics()
        return {}

    # --- Private Methods ---

    def _cleanup_subscriptions(self):
        """
        A finalizer method called by weakref when the proxy object is garbage collected.
        This is a fail-safe to ensure subscriptions are cleaned up.
        """
        print(f"Finalizer called for '{self.client_id}'. Scheduling cleanup.")
        try:
            # This method is synchronous, so we need to schedule the async cleanup
            # on the running event loop.
            loop = asyncio.get_running_loop()
            loop.create_task(self.unsubscribe_all())
        except RuntimeError:
            # Event loop might not be running if the application is shutting down.
            pass
