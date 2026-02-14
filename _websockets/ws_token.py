from curl_cffi import requests
import json
from loguru import logger
import time
import random
import traceback
from localization import t


class KickPoints:
    def __init__(self, token: str, proxy: str = None):
        self.token = token
        self.proxy = proxy

        proxies = None
        if proxy:
            proxies = {"http": proxy, "https": proxy}

        self.session = requests.Session(
            impersonate="chrome120",
            proxies=proxies,
        )

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://kick.com",
            "Referer": "https://kick.com/",
            "Sec-Ch-Ua": (
                '"Chromium";v="120", "Google Chrome";v="120", '
                '"Not?A_Brand";v="99"'
            ),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Client-Token": (
                "e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Authorization": f"Bearer {self.token}",
            "Connection": "keep-alive",
        })

        self._initialized = False


    def _ensure_session(self):
        if self._initialized:
            return

        try:
            logger.info(t("initializing_session"))
            response = self.session.get("https://kick.com", timeout=15)
            logger.debug(t(
                "base_page_status", status=response.status_code
            ))

            if response.status_code == 200:
                logger.success(t("bypass_success"))
                logger.debug(t(
                    "cookies_after_bypass",
                    cookies=dict(self.session.cookies),
                ))
            elif response.status_code == 403:
                logger.error(
                    "403 при инициализации — "
                    "IP заблокирован или нужен другой прокси"
                )
            else:
                logger.error(t(
                    "failed_bypass", status=response.status_code
                ))

            for name, value in {
                "showMatureContent": "true",
                "USER_LOCALE": "en",
            }.items():
                self.session.cookies.set(
                    name, value, domain="kick.com"
                )

            time.sleep(random.uniform(0.5, 1.5))
            self._initialized = True

        except Exception as e:
            logger.error(t("session_init_error", error=str(e)))
            logger.debug(t(
                "init_traceback", traceback=traceback.format_exc()
            ))

    def _reinitialize_session(self):
        logger.warning("Переинициализация сессии ws_token...")
        self._initialized = False
        self._ensure_session()


    def _parse_json(self, response) -> dict | None:
        try:
            text = response.content.decode("utf-8", errors="ignore")
            return json.loads(text)
        except Exception as e:
            logger.error(t("json_parsing_error", error=str(e)))
            return None

    def _safe_get(self, data, *keys):
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass


    def get_ws_token(self, streamer_name: str) -> str | None:
        self._ensure_session()

        try:
            # Шаг 1: Данные канала
            logger.info(t(
                "getting_channel_data", streamer=streamer_name
            ))

            channel_headers = {
                "Referer": f"https://kick.com/{streamer_name}/",
                "Origin": "https://kick.com",
                "Accept": "application/json, text/plain, */*",
            }

            channel_response = self.session.get(
                f"https://kick.com/api/v2/channels/{streamer_name}",
                headers=channel_headers,
                timeout=15,
            )

            status = channel_response.status_code
            logger.debug(t("channel_api_status", status=status))

            # Обработка 403 с retry
            if status == 403:
                logger.warning(
                    f"403 для {streamer_name} — переинициализация"
                )
                self._reinitialize_session()

                channel_response = self.session.get(
                    f"https://kick.com/api/v2/channels/{streamer_name}",
                    headers=channel_headers,
                    timeout=15,
                )
                status = channel_response.status_code

                if status == 403:
                    logger.error(
                        f"Повторный 403 для {streamer_name}"
                    )
                    return None

            if status != 200:
                logger.error(t(
                    "failed_get_channel_data", status=status
                ))
                return None

            channel_data = self._parse_json(channel_response)
            if not channel_data:
                return None

            # Определяем структуру
            if "data" in channel_data and isinstance(
                channel_data["data"], dict
            ):
                channel_info = channel_data["data"]
            elif "id" in channel_data:
                channel_info = channel_data
            else:
                logger.error(t("unexpected_structure"))
                return None

            channel_id = channel_info.get("id")
            user_id = (
                channel_info.get("user_id")
                or self._safe_get(channel_info, "user", "id")
            )

            if not channel_id:
                logger.error(t("channel_id_not_found"))
                return None

            if not user_id:
                logger.warning(t("user_id_not_found"))
                user_id = channel_id

            logger.info(t(
                "channel_ids_info",
                channel_id=channel_id,
                user_id=user_id,
            ))

            time.sleep(random.uniform(0.5, 1.5))

            # Шаг 2: WS Token
            ws_headers = {
                "Referer": f"https://kick.com/{streamer_name}/",
                "Origin": "https://kick.com",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-Chatroom": str(channel_id),
                "X-User-Id": str(user_id),
            }

            ws_response = self.session.get(
                "https://websockets.kick.com/viewer/v1/token",
                headers=ws_headers,
                timeout=15,
            )

            ws_status = ws_response.status_code
            logger.debug(t(
                "websocket_token_api_status", status=ws_status
            ))

            if ws_status == 403:
                logger.error(
                    f"403 при WS-токене для {streamer_name}"
                )
                return None

            if ws_status != 200:
                logger.error(t(
                    "failed_get_websocket_token", status=ws_status
                ))
                return None

            ws_data = self._parse_json(ws_response)
            if not ws_data:
                return None

            # Извлекаем токен из разных форматов
            ws_token = (
                self._safe_get(ws_data, "data", "token")
                or self._safe_get(ws_data, "data", "websocket_token")
                or self._safe_get(ws_data, "token")
                or self._safe_get(ws_data, "websocket_token")
            )

            if ws_token:
                logger.success(t(
                    "websocket_success",
                    token=ws_token[:20] + "...",
                ))
                return ws_token

            logger.error(t("websocket_not_found"))
            return None

        except Exception as e:
            logger.error(t("critical_error", error=str(e)))
            logger.debug(t(
                "critical_traceback",
                traceback=traceback.format_exc(),
            ))
            return None