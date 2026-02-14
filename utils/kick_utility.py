from curl_cffi import requests
import json
from loguru import logger
import time
import random
import traceback
from localization import t


class KickUtility:
    def __init__(self, username: str, proxy: str = None):
        self.username = username
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
            "Referer": f"https://kick.com/{username}/",
            "Sec-Ch-Ua": (
                '"Chromium";v="120", "Google Chrome";v="120", '
                '"Not?A_Brand";v="99"'
            ),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Connection": "keep-alive",
        })

        self._initialized = False

    def _ensure_session(self):
        if self._initialized:
            return
        try:
            logger.info(t("initializing_utility_session"))
            resp = self.session.get("https://kick.com", timeout=15)

            if resp.status_code == 200:
                logger.success(t("utility_bypass_success"))
            elif resp.status_code == 403:
                logger.error(t(
                    "utility_403_init",
                    username=self.username
                ))
            else:
                logger.error(t(
                    "failed_bypass", status=resp.status_code
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

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def _parse_response(self, response) -> dict | None:
        try:
            raw = response.content.decode("utf-8", errors="ignore")
            if not raw or raw.strip() in ("", "null", "None"):
                return None
            return json.loads(raw)
        except Exception as e:
            logger.error(t("json_parsing_error", error=str(e)))
            return None

    def _safe_get(self, data, *keys):
        """
        Безопасное извлечение вложенных ключей из dict.
        _safe_get(data, "data", "id") → data["data"]["id"] или None
        Не падает на None, int, str, list.
        """
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    def get_stream_id(self, token: str) -> int | None:

        self._ensure_session()
        self.session.headers["Authorization"] = f"Bearer {token}"

        stream_id = None

        try:
            resp = self.session.get(
                f"https://kick.com/api/v2/channels/"
                f"{self.username}/livestream",
                timeout=15,
            )

            if resp.status_code == 403:
                logger.warning(t(
                    "livestream_403",
                    username=self.username
                ))
                # Не возвращаем None сразу — пробуем endpoint 2
            elif resp.status_code == 200:
                data = self._parse_response(resp)
                if data is not None:
                    stream_id = (
                        self._safe_get(data, "data", "id")
                        or self._safe_get(data, "id")
                    )
                    if stream_id:
                        logger.info(t(
                            "livestream_found_primary",
                            username=self.username,
                            stream_id=stream_id
                        ))
                        return stream_id
                    else:
                        logger.debug(t(
                            "livestream_no_id_primary",
                            username=self.username
                        ))
                else:
                    logger.debug(t(
                        "livestream_null_response",
                        username=self.username
                    ))
            else:
                logger.debug(t(
                    "livestream_non_200",
                    username=self.username,
                    status=resp.status_code
                ))

        except Exception as e:
            logger.error(t(
                "error_getting_livestream", error=str(e)
            ))

        stream_id = self._get_stream_id_from_channel(token)
        if stream_id:
            logger.info(t(
                "livestream_found_fallback",
                username=self.username,
                stream_id=stream_id
            ))
        return stream_id

    def _get_stream_id_from_channel(self, token: str) -> int | None:
        """Альтернативный метод через основной channel API"""
        self.session.headers["Authorization"] = f"Bearer {token}"

        try:
            resp = self.session.get(
                f"https://kick.com/api/v2/channels/{self.username}",
                timeout=15,
            )

            if resp.status_code == 403:
                logger.warning(t(
                    "channel_403",
                    username=self.username
                ))
                return None

            if resp.status_code != 200:
                logger.debug(t(
                    "channel_non_200",
                    username=self.username,
                    status=resp.status_code
                ))
                return None

            data = self._parse_response(resp)
            if data is None:
                return None

            # Пробуем все известные пути
            stream_id = (
                self._safe_get(data, "data", "livestream", "id")
                or self._safe_get(data, "livestream", "id")
                or self._safe_get(
                    data, "data", "livestream", "data", "id"
                )
            )

            return stream_id

        except Exception as e:
            logger.error(t(
                "error_getting_stream_from_channel",
                error=str(e)
            ))
            return None

    def get_channel_id(self, token: str) -> int | None:
        self._ensure_session()
        self.session.headers["Authorization"] = f"Bearer {token}"

        try:
            resp = self.session.get(
                f"https://kick.com/api/v2/channels/{self.username}",
                timeout=15,
            )

            if resp.status_code != 200:
                logger.error(t(
                    "channel_id_api_failed",
                    username=self.username,
                    status=resp.status_code
                ))
                return None

            data = self._parse_response(resp)
            if data is None:
                return None

            channel_id = (
                self._safe_get(data, "data", "id")
                or self._safe_get(data, "id")
            )

            if channel_id:
                logger.info(t(
                    "channel_id_success",
                    channel_id=channel_id
                ))

            return channel_id

        except Exception as e:
            logger.error(t(
                "error_getting_channel_id", error=str(e)
            ))
            return None