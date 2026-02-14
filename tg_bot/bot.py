import os
import json
import asyncio
import sys
import html
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from loguru import logger

if TYPE_CHECKING:
    from account_manager import AccountManager

try:
    from localization import t as loc_t

    def t(key, **kwargs):
        val = loc_t(key, **kwargs)
        return val if val else key
except ImportError:
    def t(key, **kwargs):
        return key


class TelegramBot:
    def __init__(self, config: dict):
        self.active = False
        self.application: Optional[Application] = None
        self.user_language: dict[int, str] = {}
        self.language_files: dict[str, dict] = {}
        self.config = config
        self.account_manager: Optional["AccountManager"] = None

        # Обратная совместимость
        self._legacy_streamers: list[str] = []
        self._legacy_points: dict = {}

        self.load_language_files()

    def set_account_manager(self, manager: "AccountManager"):
        self.account_manager = manager
        logger.info(
            f"TG Bot: подключён AccountManager "
            f"({len(manager.workers)} аккаунтов)"
        )

    def set_streamers(self, streamers: list[str]):
        self._legacy_streamers = streamers

    def set_points_data(self, streamer_name: str, points: int):
        now = datetime.now().strftime("%H:%M:%S")
        if streamer_name not in self._legacy_points:
            self._legacy_points[streamer_name] = {"history": []}
        self._legacy_points[streamer_name].update({
            "amount": points,
            "last_update": now,
        })
        history = self._legacy_points[streamer_name]["history"]
        history.append((now, points))
        if len(history) > 10:
            self._legacy_points[streamer_name]["history"] = (
                history[-10:]
            )

    async def start(self):
        tg_conf = self.config.get("Telegram", {})
        if not tg_conf.get("enabled", False):
            logger.info("Telegram bot disabled in config.")
            return

        token = tg_conf.get("bot_token", "")
        if not token:
            logger.error("Telegram token not found!")
            return

        try:
            self.application = (
                Application.builder().token(token).build()
            )

            handlers = [
                CommandHandler("start", self.cmd_start),
                CommandHandler("status", self.cmd_status),
                CommandHandler("balance", self.cmd_balance),
                CommandHandler("accounts", self.cmd_accounts),
                CommandHandler("restart", self.cmd_restart),
                CommandHandler("help", self.cmd_help),
                CommandHandler("language", self.cmd_language),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    self.handle_message,
                ),
            ]

            for h in handlers:
                self.application.add_handler(h)

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                drop_pending_updates=True
            )

            self.active = True
            logger.success("✅ Telegram bot initialized")
            await self._send_startup()

        except Exception as e:
            logger.error(f"❌ Telegram init failed: {e}")
            self.active = False

    async def stop(self):
        if self.application:
            try:
                if self.application.updater.running:
                    await self.application.updater.stop()
                if self.application.running:
                    await self.application.stop()
                await self.application.shutdown()
                self.active = False
            except Exception as e:
                logger.error(f"Error stopping TG bot: {e}")

    def load_language_files(self):
        lang_dir = "tg_bot/lang"
        os.makedirs(lang_dir, exist_ok=True)
        for lang in ("en", "ru"):
            path = os.path.join(lang_dir, f"{lang}.lang")
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        self.language_files[lang] = json.load(f)
                else:
                    self.language_files[lang] = {}
            except Exception as e:
                logger.error(f"Error loading lang {lang}: {e}")
                self.language_files[lang] = {}

    def get_text(self, key, lang="en", **kwargs):
        d = self.language_files.get(
            lang.lower(),
            self.language_files.get("en", {}),
        )
        text = d.get(key, f"🔑 {key}")
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

    def _lang(self, uid: int) -> str:
        return self.user_language.get(
            uid, self.config.get("Language", "en")
        )

    def get_keyboard(self, lang="en", is_admin=False):
        d = self.language_files.get(
            lang, self.language_files.get("en", {})
        )
        btn_stat = d.get("btn_status", "📊 Status")
        btn_bal = d.get("btn_balance", "💰 Balance")
        btn_help = d.get("btn_help", "❓ Help")
        btn_acc = d.get("btn_accounts", "👥 Accounts")

        keyboard = [[btn_stat, btn_bal], [btn_acc]]

        if is_admin:
            btn_restart = d.get("btn_restart", "🔄 Restart")
            keyboard.append([btn_help, btn_restart])
        else:
            keyboard.append([btn_help])

        return ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True
        )

    def is_user_allowed(self, user_id: int) -> bool:
        conf = self.config.get("Telegram", {})
        allowed = conf.get("allowed_users", [])
        owner = conf.get("chat_id")
        ids = {str(u) for u in allowed}
        if owner:
            ids.add(str(owner))
        return bool(ids) and str(user_id) in ids

    def is_admin(self, user_id: int) -> bool:
        owner = self.config.get("Telegram", {}).get("chat_id")
        return str(user_id) == str(owner)

    def _build_status_text(self, lang: str) -> str:
        if self.account_manager:
            return self._build_multi_status(lang)
        return self._build_legacy_status(lang)

    def _build_multi_status(self, lang: str) -> str:
        lines = ["<b>📊 Multi-Account Status</b>\n"]
        now = datetime.now().strftime("%H:%M:%S")

        for worker in self.account_manager.workers:
            st = worker.get_status()
            alias = html.escape(st["alias"])
            active = st["active_count"]
            limit = st["max_concurrent"]
            proxy = "🔒" if st["proxy"] else "🌐"

            lines.append(
                f"{proxy} <b>{alias}</b> [{active}/{limit}]"
            )

            for name in worker.state.streamer_order:
                info = st["streamers"].get(name, {})
                pri = info.get("priority", "?")
                online = info.get("online", False)
                watching = info.get("watching", False)
                pts = info.get("points", 0)
                errors = info.get("errors", 0)

                if watching:
                    icon = "👁"
                elif online:
                    icon = "🟢"
                else:
                    icon = "⚫"

                err_str = f" ⚠️x{errors}" if errors else ""
                name_esc = html.escape(name)

                lines.append(
                    f"  {icon} #{pri} "
                    f"<code>{name_esc}</code> "
                    f"— {pts} pts{err_str}"
                )
            lines.append("")

        lines.append(f"🕐 {now}")
        return "\n".join(lines)

    def _build_legacy_status(self, lang: str) -> str:
        if not self._legacy_streamers:
            return self.get_text("status_inactive", lang)
        sl = "\n".join([
            f"• <code>{html.escape(str(s))}</code>"
            for s in self._legacy_streamers
        ])
        now = datetime.now().strftime("%H:%M:%S")
        return self.get_text(
            "status_active", lang,
            streamers=sl, last_update=now, rate="120",
        )

    def _build_balance_text(self, lang: str) -> str:
        if self.account_manager:
            return self._build_multi_balance(lang)
        return self._build_legacy_balance(lang)

    def _build_multi_balance(self, lang: str) -> str:
        lines = ["<b>💰 Points by Account</b>\n"]
        total_all = 0

        for worker in self.account_manager.workers:
            st = worker.get_status()
            alias = html.escape(st["alias"])
            lines.append(f"<b>{alias}</b>:")
            acc_total = 0

            for name in worker.state.streamer_order:
                info = st["streamers"].get(name, {})
                pts = info.get("points", 0)
                last = info.get("last_update")
                watching = info.get("watching", False)
                acc_total += pts

                ts = (
                    last.split("T")[1][:8] if last else "N/A"
                )
                icon = "👁" if watching else "  "
                lines.append(
                    f"  {icon} <code>{html.escape(name)}</code>"
                    f": <b>{pts}</b> ({ts})"
                )

            total_all += acc_total
            lines.append(
                f"  📊 Subtotal: <b>{acc_total}</b>\n"
            )

        lines.append(f"🏆 <b>Total: {total_all}</b>")
        return "\n".join(lines)

    def _build_legacy_balance(self, lang: str) -> str:
        if not self._legacy_streamers:
            return self.get_text("balance_no_streamers", lang)
        msgs = []
        for s in self._legacy_streamers:
            data = self._legacy_points.get(
                s, {"amount": 0, "last_update": "N/A"}
            )
            msgs.append(self.get_text(
                "balance_info", lang,
                streamer=html.escape(str(s)),
                amount=data["amount"],
                time=data["last_update"],
            ))
        text = "\n\n".join(msgs)
        return text[:4000] if len(text) <= 4000 else text[:4000] + "..."

    def _build_accounts_text(self) -> str:
        if not self.account_manager:
            return "No AccountManager"

        lines = ["<b>👥 Accounts Overview</b>\n"]

        for i, worker in enumerate(
            self.account_manager.workers
        ):
            st = worker.get_status()
            alias = html.escape(st["alias"])
            proxy = "🔒 proxy" if st["proxy"] else "🌐 direct"
            active = st["active_count"]
            limit = st["max_concurrent"]
            total = len(st["streamers"])
            online = sum(
                1 for s in st["streamers"].values()
                if s.get("online")
            )

            order = " > ".join(worker.state.streamer_order)

            lines.append(
                f"<b>#{i + 1} {alias}</b>\n"
                f"  {proxy}\n"
                f"  Стримеров: {total} (онлайн: {online})\n"
                f"  Активно: {active}/{limit}\n"
                f"  Приоритет: {order}\n"
            )

        return "\n".join(lines)

    async def cmd_start(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        lang = self._lang(uid)
        self.user_language[uid] = lang
        await update.message.reply_text(
            self.get_text("start_message", lang),
            reply_markup=self.get_keyboard(
                lang, self.is_admin(uid)
            ),
            parse_mode=ParseMode.HTML,
        )

    async def cmd_status(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        text = self._build_status_text(self._lang(uid))
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML
        )

    async def cmd_balance(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        text = self._build_balance_text(self._lang(uid))
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await update.message.reply_text(
                    text[i:i + 4000],
                    parse_mode=ParseMode.HTML,
                )
        else:
            await update.message.reply_text(
                text, parse_mode=ParseMode.HTML
            )

    async def cmd_accounts(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        await update.message.reply_text(
            self._build_accounts_text(),
            parse_mode=ParseMode.HTML,
        )

    async def cmd_restart(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        lang = self._lang(uid)
        if not self.is_admin(uid):
            await update.message.reply_text(
                self.get_text(
                    "not_enough_permissions", lang
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        await update.message.reply_text(
            self.get_text("restart_confirmation", lang),
            parse_mode=ParseMode.HTML,
        )
        await asyncio.sleep(1)
        logger.info("Restart requested via Telegram")
        sys.exit(1)

    async def cmd_help(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        lang = self._lang(uid)
        extra = (
            "\n\n<b>Multi-account commands:</b>\n"
            "/accounts — Accounts overview\n"
            "/status — Status with priorities\n"
            "/balance — Points by account"
        )
        await update.message.reply_text(
            self.get_text("help_message", lang) + extra,
            parse_mode=ParseMode.HTML,
        )

    async def cmd_language(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        if not self.is_admin(uid):
            lang = self._lang(uid)
            await update.message.reply_text(
                self.get_text(
                    "not_enough_permissions", lang
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        if not context.args:
            await update.message.reply_text(
                "Usage: /language [en/ru]"
            )
            return
        code = context.args[0].lower()
        if code in ("en", "ru"):
            self.user_language[uid] = code
            await update.message.reply_text(
                self.get_text(
                    "language_changed", code,
                    language=code.upper(),
                ),
                reply_markup=self.get_keyboard(
                    code, is_admin=True
                ),
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text(
                "Supported: en, ru"
            )

    async def handle_message(self, update: Update, context):
        uid = update.effective_user.id
        if not self.is_user_allowed(uid):
            return
        text = update.message.text
        lang = self._lang(uid)
        d = self.language_files.get(
            lang, self.language_files.get("en", {})
        )
        btn_map = {
            d.get("btn_status", "📊 Status"): self.cmd_status,
            d.get("btn_balance", "💰 Balance"): self.cmd_balance,
            d.get("btn_help", "❓ Help"): self.cmd_help,
            d.get("btn_restart", "🔄 Restart"): self.cmd_restart,
            d.get("btn_accounts", "👥 Accounts"): self.cmd_accounts,
        }
        handler = btn_map.get(text)
        if handler:
            await handler(update, context)

    async def _send_startup(self):
        if not self.active:
            return
        owner = self.config.get("Telegram", {}).get("chat_id")
        if not owner:
            return

        if self.account_manager:
            text = "🚀 <b>Miner Started!</b>\n\n"
            text += self._build_accounts_text()
        else:
            sl = "\n".join([
                f"• <code>{html.escape(str(s))}</code>"
                for s in self._legacy_streamers
            ]) if self._legacy_streamers else "None"
            lang = self._lang(int(owner))
            text = self.get_text(
                "startup_notification", lang, streamers=sl
            )

        await self._send(owner, text)

    async def send_points_update(
        self, streamer, old_amount, new_amount,
        account_alias="",
    ):
        if not self.active:
            return
        gain = new_amount - old_amount
        if gain <= 0:
            return
        conf = self.config.get("Telegram", {})
        recipients = set(conf.get("allowed_users", []))
        owner = conf.get("chat_id")
        if owner:
            recipients.add(owner)
        prefix = (
            f"[{html.escape(account_alias)}] "
            if account_alias else ""
        )
        for uid in recipients:
            await self._send(
                uid,
                f"{prefix}💰 <b>{html.escape(streamer)}</b>"
                f": +{gain} (Total: {new_amount})",
            )

    async def send_alert(self, streamers):
        if not self.active:
            return
        owner = self.config.get("Telegram", {}).get("chat_id")
        if owner:
            names = ", ".join(html.escape(s) for s in streamers)
            await self._send(
                owner, f"⚠️ Нет начислений: {names}"
            )

    async def send_restart_notification(self):
        if not self.active:
            return
        owner = self.config.get("Telegram", {}).get("chat_id")
        if owner:
            await self._send(owner, "🔄 Перезапуск...")

    async def send_streamer_started(self, streamer):
        pass

    async def send_streamer_error(self, streamer, error):
        if not self.active:
            return
        owner = self.config.get("Telegram", {}).get("chat_id")
        if not owner:
            return
        safe = html.escape(str(error)[:300])
        lang = self._lang(int(owner))
        await self._send(
            owner,
            self.get_text(
                "streamer_error", lang,
                streamer=streamer, error=safe,
            ),
        )

    async def _send(self, user_id, text):
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            logger.error(f"TG send to {user_id} failed: {e}")