import rnet
import json
import asyncio
import traceback
import random
from typing import Dict, Optional, Callable, Awaitable
from dataclasses import dataclass
from rnet import WebSocket, Message
from loguru import logger
from localization import t


@dataclass
class ConnectionState:
    is_connected: bool = False
    reconnect_attempts: int = 0
    max_reconnect_attempts: int = 5


class KickWebSocket:
    def __init__(
        self,
        data: Dict[str, str],
        proxy: Optional[str] = None,
        on_disconnect: Optional[Callable[[], Awaitable]] = None,
    ):
        self.ws: Optional[WebSocket] = None
        self.data = data
        self.proxy = proxy
        self.on_disconnect = on_disconnect
        self.state = ConnectionState()
        self.handshake_task: Optional[asyncio.Task] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self) -> bool:
        if not self.data.get("token"):
            logger.error(t("token_must_not_be_empty"))
            return False

        try:
            ch = self.data.get("channelId", "?")
            logger.info(t(
                "websocket_connecting", channel_id=ch
            ))

            ws_url = (
                "wss://websockets.kick.com/viewer/v1/connect"
                f"?token={self.data['token']}"
            )

            ws_kwargs = dict(
                url=ws_url,
                read_buffer_size=4096,
                write_buffer_size=4096,
                max_message_size=4096,
            )

            # Пробуем с прокси
            if self.proxy:
                ws_kwargs["proxy"] = self.proxy

            try:
                self.ws = await rnet.websocket(**ws_kwargs)
            except TypeError:
                if self.proxy:
                    logger.warning(
                        "rnet.websocket no longer supports proxy"
                    )
                ws_kwargs.pop("proxy", None)
                self.ws = await rnet.websocket(**ws_kwargs)

            logger.success(t("websocket_connected"))
            self.state.is_connected = True
            self.state.reconnect_attempts = 0

            await self._send_initial_messages()
            await self._start_background_tasks()
            await self._listen_for_messages()

            return True

        except Exception as e:
            logger.error(t(
                "websocket_connection_failed", error=str(e)
            ))
            logger.debug(t(
                "connection_traceback",
                traceback=traceback.format_exc(),
            ))
            self.state.is_connected = False
            await self._handle_reconnection()
            return False

    async def _send_initial_messages(self):
        await self._send_handshake()
        await self._send_ping()

    async def _start_background_tasks(self):
        self._running = True
        self.handshake_task = asyncio.create_task(
            self._handshake_loop()
        )
        self.tracking_task = asyncio.create_task(
            self._tracking_loop()
        )

    async def _handshake_loop(self):
        while self._running and self.state.is_connected:
            try:
                await asyncio.sleep(random.uniform(25, 35))
                if self.state.is_connected:
                    await self._send_handshake()
                    await self._send_ping()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(t(
                    "handshake_loop_error", error=str(e)
                ))
                break

    async def _tracking_loop(self):
        while self._running and self.state.is_connected:
            try:
                await asyncio.sleep(random.uniform(9.5, 12.5))
                if self.state.is_connected:
                    await self._send_user_event()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(t(
                    "tracking_loop_error", error=str(e)
                ))
                break

    async def _listen_for_messages(self):
        try:
            while self.state.is_connected and self._running:
                message = await self.ws.recv()
                await self._handle_message(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(t(
                "message_listening_error", error=str(e)
            ))
            self.state.is_connected = False
            await self._handle_reconnection()

    async def _handle_message(self, message):
        try:
            if isinstance(message, Message):
                msg = (
                    message.text
                    if hasattr(message, "text")
                    else str(message)
                )
            else:
                msg = str(message)

            if not msg or msg.strip() == "":
                return

            if msg.strip() == "ping":
                await self._send_pong()
                return

            try:
                parsed = json.loads(msg)
            except json.JSONDecodeError:
                return

            msg_type = parsed.get("type", "unknown")
            logger.debug(t(
                "received_message_type", type=msg_type
            ))

            if msg_type == "channel_handshake":
                ch_id = None
                data_msg = parsed.get("data", {})
                if isinstance(data_msg, dict):
                    message_inner = data_msg.get("message", {})
                    if isinstance(message_inner, dict):
                        ch_id = message_inner.get("channelId")
                if ch_id:
                    logger.info(t(
                        "channel_handshake_received",
                        channel_id=ch_id,
                    ))

            elif msg_type == "ping":
                await self._send_pong()

            elif msg_type == "pong":
                pass

            elif msg_type == "error":
                err_data = parsed.get("data", {})
                err = (
                    err_data.get("message", "Unknown")
                    if isinstance(err_data, dict)
                    else "Unknown"
                )
                logger.error(t("websocket_error", error=err))

            elif msg_type == "user_event":
                pass

        except Exception as e:
            logger.error(t(
                "message_handling_error", error=str(e)
            ))

    async def _handle_reconnection(self):
        if (
            self.state.reconnect_attempts
            < self.state.max_reconnect_attempts
        ):
            self.state.reconnect_attempts += 1
            logger.info(t(
                "attempting_reconnect",
                attempt=self.state.reconnect_attempts,
                max=self.state.max_reconnect_attempts,
            ))
            await self._cleanup_tasks()

            delay = min(
                5 * (2 ** (self.state.reconnect_attempts - 1)),
                120,
            )
            logger.info(f"Reconnect delay: {delay}s")
            await asyncio.sleep(delay)
            await self.connect()
        else:
            logger.error(t("max_reconnection_attempts"))
            await self.disconnect()
            if self.on_disconnect:
                await self.on_disconnect()

    async def _cleanup_tasks(self):
        self._running = False
        for task in (self.handshake_task, self.tracking_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def disconnect(self):
        self.state.is_connected = False
        await self._cleanup_tasks()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        logger.info(t("websocket_closed"))

    async def _send_handshake(self):
        if not self.state.is_connected:
            return
        payload = {
            "type": "channel_handshake",
            "data": {
                "message": {
                    "channelId": int(
                        self.data.get("channelId", 0)
                    ),
                }
            },
        }
        try:
            await self.ws.send(
                Message.from_text(json.dumps(payload))
            )
            logger.debug(t(
                "sent_handshake",
                channel_id=self.data.get("channelId", "?"),
            ))
        except Exception as e:
            logger.error(t(
                "failed_send_handshake", error=str(e)
            ))
            self.state.is_connected = False

    async def _send_ping(self):
        if not self.state.is_connected:
            return
        try:
            await self.ws.send(
                Message.from_text(json.dumps({"type": "ping"}))
            )
            logger.debug(t("sent_ping"))
        except Exception as e:
            logger.error(t("failed_send_ping", error=str(e)))
            self.state.is_connected = False

    async def _send_pong(self):
        if not self.state.is_connected:
            return
        try:
            await self.ws.send(
                Message.from_text(json.dumps({"type": "pong"}))
            )
        except Exception:
            pass

    async def _send_user_event(self):
        if not self.state.is_connected:
            return
        payload = {
            "type": "user_event",
            "data": {
                "message": {
                    "name": "tracking.user.watch.livestream",
                    "channel_id": int(
                        self.data.get("channelId", 0)
                    ),
                    "livestream_id": int(
                        self.data.get("streamId", 0)
                    ),
                }
            },
        }
        try:
            await self.ws.send(
                Message.from_text(json.dumps(payload))
            )
            logger.debug(t(
                "sent_user_event",
                channel_id=self.data.get("channelId", "?"),
                stream_id=self.data.get("streamId", "?"),
            ))
        except Exception as e:
            logger.error(t(
                "failed_send_user_event", error=str(e)
            ))
            self.state.is_connected = False