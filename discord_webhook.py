import json
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger

try:
    from curl_cffi import requests as cffi_requests
    USE_CFFI = True
except ImportError:
    import requests as std_requests
    USE_CFFI = False

from localization import t


class DiscordWebhook:

    def __init__(self, config: dict):
        discord_cfg = config.get("Discord", {})

        self.enabled = discord_cfg.get("enabled", False)
        self.webhook_url = discord_cfg.get("webhook_url", "")
        self.username = discord_cfg.get("username", "KickMiner")
        self.avatar_url = discord_cfg.get("avatar_url", "")

        # Какие уведомления отправлять
        self.notify_points = discord_cfg.get(
            "notify_points", True
        )
        self.notify_status = discord_cfg.get(
            "notify_status_change", True
        )
        self.notify_errors = discord_cfg.get(
            "notify_errors", True
        )
        self.notify_startup = discord_cfg.get(
            "notify_startup", True
        )
        self.min_points_gain = discord_cfg.get(
            "min_points_gain", 10
        )

        # Цвета (десятичные)
        self.color_success = discord_cfg.get(
            "color_success", 3461464  # #34D168
        )
        self.color_info = discord_cfg.get(
            "color_info", 5793266  # #5865F2
        )
        self.color_warning = discord_cfg.get(
            "color_warning", 16763904  # #FFA500
        )
        self.color_error = discord_cfg.get(
            "color_error", 15746887  # #F04747
        )

        # Rate limiting
        self._last_send_time = 0
        self._min_interval = 1.0
        self._lock = threading.Lock()

        if self.enabled and not self.webhook_url:
            logger.error(t("discord_webhook_url_missing"))
            self.enabled = False

        if self.enabled:
            logger.success(t("discord_webhook_initialized"))

    def _send_raw(self, payload: dict) -> bool:
        """Отправка payload в Discord webhook"""
        if not self.enabled:
            return False

        with self._lock:
            # Rate limit
            now = time.time()
            elapsed = now - self._last_send_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)

            try:
                headers = {"Content-Type": "application/json"}
                data = json.dumps(payload)

                if USE_CFFI:
                    resp = cffi_requests.post(
                        self.webhook_url,
                        headers=headers,
                        data=data,
                        timeout=10,
                    )
                    status = resp.status_code
                else:
                    resp = std_requests.post(
                        self.webhook_url,
                        headers=headers,
                        data=data,
                        timeout=10,
                    )
                    status = resp.status_code

                self._last_send_time = time.time()

                if status == 204:
                    logger.debug(t("discord_message_sent"))
                    return True
                elif status == 429:
                    retry_after = 5
                    try:
                        body = resp.json()
                        retry_after = body.get(
                            "retry_after", 5
                        )
                    except Exception:
                        pass
                    logger.warning(t(
                        "discord_rate_limited",
                        retry_after=retry_after,
                    ))
                    time.sleep(retry_after)
                    return False
                else:
                    logger.error(t(
                        "discord_send_failed",
                        status=status,
                    ))
                    return False

            except Exception as e:
                logger.error(t(
                    "discord_send_error", error=str(e)
                ))
                return False

    def _send_in_thread(self, payload: dict):
        """Отправка в фоновом потоке"""
        thread = threading.Thread(
            target=self._send_raw,
            args=(payload,),
            daemon=True,
        )
        thread.start()

    def _build_payload(
        self,
        embeds: List[dict],
        content: str = None,
    ) -> dict:
        payload = {}

        if self.username:
            payload["username"] = self.username
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds

        return payload

    def _embed(
        self,
        title: str,
        description: str = "",
        color: int = None,
        fields: List[dict] = None,
        footer: str = None,
        url: str = None,
        thumbnail_url: str = None,
    ) -> dict:
        embed: Dict[str, Any] = {"title": title}

        if description:
            embed["description"] = description
        if color is not None:
            embed["color"] = color
        if url:
            embed["url"] = url
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = {"text": footer}

        embed["timestamp"] = datetime.utcnow().isoformat()

        return embed

    def _field(
        self, name: str, value: str, inline: bool = True
    ) -> dict:
        return {
            "name": name,
            "value": value,
            "inline": inline,
        }

    def send_startup(
        self,
        accounts: List[dict],
    ):
        """Уведомление о запуске майнера"""
        if not self.enabled or not self.notify_startup:
            return

        fields = []
        for acc in accounts:
            alias = acc.get("alias", "Unknown")
            streamers = acc.get("streamer_order", [])
            limit = acc.get("max_concurrent", 0)
            proxy = "🔒 Proxy" if acc.get("proxy") else "🌐 Direct"

            streamer_list = ", ".join(
                streamers[:5]
            )
            if len(streamers) > 5:
                streamer_list += f" +{len(streamers) - 5} more"

            fields.append(self._field(
                name=f"👤 {alias}",
                value=(
                    f"{proxy} · Limit: {limit}\n"
                    f"`{streamer_list}`"
                ),
                inline=False,
            ))

        embed = self._embed(
            title="🚀 KickMiner Started",
            description=(
                f"**{len(accounts)}** account(s) loaded"
            ),
            color=self.color_success,
            fields=fields,
            footer="Kick Channel Points Miner",
        )

        payload = self._build_payload([embed])
        self._send_in_thread(payload)

    def send_points_update(
        self,
        account_alias: str,
        streamer: str,
        old_amount: int,
        new_amount: int,
    ):
        """Уведомление о начислении поинтов"""
        if not self.enabled or not self.notify_points:
            return

        gain = new_amount - old_amount
        if gain < self.min_points_gain:
            return

        embed = self._embed(
            title="💰 Points Earned",
            color=self.color_success,
            url=f"https://kick.com/{streamer}",
            fields=[
                self._field("Streamer", f"[{streamer}](https://kick.com/{streamer})"),
                self._field("Gained", f"+{gain:,}"),
                self._field("Total", f"{new_amount:,}"),
                self._field("Account", account_alias),
            ],
        )

        payload = self._build_payload([embed])
        self._send_in_thread(payload)

    def send_streamer_online(
        self,
        account_alias: str,
        streamer: str,
        priority: int,
        action: str = "started",
    ):
        """Уведомление: стример вышел в онлайн / начали смотреть"""
        if not self.enabled or not self.notify_status:
            return

        if action == "started":
            title = "▶️ Now Watching"
            color = self.color_success
            desc = (
                f"Started watching "
                f"[{streamer}](https://kick.com/{streamer})"
            )
        elif action == "displaced":
            title = "⏹ Streamer Displaced"
            color = self.color_warning
            desc = (
                f"[{streamer}](https://kick.com/{streamer}) "
                f"was displaced by higher priority"
            )
        elif action == "online":
            title = "🟢 Streamer Online"
            color = self.color_info
            desc = (
                f"[{streamer}](https://kick.com/{streamer}) "
                f"went live"
            )
        elif action == "offline":
            title = "🔴 Streamer Offline"
            color = self.color_warning
            desc = (
                f"[{streamer}](https://kick.com/{streamer}) "
                f"went offline"
            )
        else:
            title = f"📡 {action}"
            color = self.color_info
            desc = streamer

        embed = self._embed(
            title=title,
            description=desc,
            color=color,
            fields=[
                self._field("Account", account_alias),
                self._field("Priority", f"#{priority}"),
            ],
        )

        payload = self._build_payload([embed])
        self._send_in_thread(payload)

    def send_error(
        self,
        account_alias: str,
        streamer: str,
        error: str,
    ):
        """Уведомление об ошибке"""
        if not self.enabled or not self.notify_errors:
            return

        safe_error = str(error)[:500]

        embed = self._embed(
            title="❌ Error",
            description=f"```\n{safe_error}\n```",
            color=self.color_error,
            fields=[
                self._field("Account", account_alias),
                self._field("Streamer", streamer),
            ],
        )

        payload = self._build_payload([embed])
        self._send_in_thread(payload)

    def send_status_summary(
        self,
        accounts_status: List[dict],
    ):
        """Полный статус всех аккаунтов (по запросу)"""
        if not self.enabled:
            return

        embeds = []
        grand_total = 0

        for acc in accounts_status:
            alias = acc.get("alias", "Unknown")
            active = acc.get("active_count", 0)
            limit = acc.get("max_concurrent", 0)
            proxy = "🔒" if acc.get("proxy") else "🌐"
            streamers = acc.get("streamers", {})
            order = acc.get("streamer_order", list(streamers.keys()))

            acc_total = 0
            lines = []

            for name in order:
                info = streamers.get(name, {})
                pts = info.get("points", 0)
                acc_total += pts

                if info.get("watching"):
                    icon = "👁"
                elif info.get("online"):
                    icon = "🟢"
                else:
                    icon = "⚫"

                pri = info.get("priority", "?")
                err = (
                    f" ⚠️x{info['errors']}"
                    if info.get("errors", 0) > 0
                    else ""
                )

                lines.append(
                    f"{icon} #{pri} **{name}** — "
                    f"{pts:,} pts{err}"
                )

            grand_total += acc_total

            description = "\n".join(lines) if lines else "No streamers"

            embed = self._embed(
                title=f"{proxy} {alias} [{active}/{limit}]",
                description=description,
                color=self.color_info,
                fields=[
                    self._field(
                        "Subtotal",
                        f"**{acc_total:,}** pts",
                    ),
                ],
            )
            embeds.append(embed)

        if len(embeds) > 10:
            embeds = embeds[:10]

        if embeds:
            embeds[-1]["footer"] = {
                "text": f"Grand Total: {grand_total:,} pts",
            }

        payload = self._build_payload(embeds)
        self._send_in_thread(payload)

    def send_restart(self, reason: str = "Manual"):
        """Уведомление о перезапуске"""
        if not self.enabled:
            return

        embed = self._embed(
            title="🔄 Miner Restarting",
            description=f"Reason: {reason}",
            color=self.color_warning,
        )

        payload = self._build_payload([embed])
        self._send_raw(payload)

    def send_custom(
        self,
        title: str,
        description: str,
        color: int = None,
    ):
        """Произвольное сообщение"""
        if not self.enabled:
            return

        embed = self._embed(
            title=title,
            description=description,
            color=color or self.color_info,
        )

        payload = self._build_payload([embed])
        self._send_in_thread(payload)