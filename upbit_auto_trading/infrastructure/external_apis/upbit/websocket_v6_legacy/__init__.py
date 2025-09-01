"""
WebSocket v6: A robust, centralized, and easy-to-use WebSocket client for Upbit.

This package provides a high-level interface for interacting with the Upbit WebSocket API,
abstracting away the complexities of connection management, subscription handling, and
error recovery.

Key Components:
- WebSocketClientProxy: The primary entry point for application components to use the
  WebSocket service. It delegates all requests to the GlobalWebSocketManager.
- GlobalWebSocketManager: A singleton that manages the physical WebSocket connections,
  consolidates subscriptions, and routes incoming data.

Basic Usage:

  from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import WebSocketClientProxy

  async def on_data_callback(symbol, data_type, data):
      print(f"Received {data_type} for {symbol}: {data}")

  async with WebSocketClientProxy("my_chart_module") as ws:
      await ws.subscribe_ticker(["KRW-BTC"], on_data_callback)
      await asyncio.sleep(60) # Listen for 60 seconds

"""

from .proxy import WebSocketClientProxy

__all__ = ["WebSocketClientProxy"]
