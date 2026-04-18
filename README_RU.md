# 🟢 Kick Channel Points Miner

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> [🇬🇧 **Read in English**](README.md)

Мощный асинхронный бот для автоматического фарма поинтов каналов на **Kick.com**. Поддержка мультиаккаунтов, система приоритетов, SOCKS5 прокси, современный Web Dashboard и управление через Telegram.

---

## ✨ Возможности

*   **👥 Мультиаккаунт:** Фарм поинтов с 10+ аккаунтов одновременно, у каждого свой список стримеров и лимиты.
*   **🎯 Система приоритетов:** Стримеры приоритизируются по позиции в конфиге. При выходе в онлайн стримера с высоким приоритетом – он автоматически вытесняет стримера с низким.
*   **🔒 Лимиты одновременного просмотра:** Настройка `max_concurrent` на каждый аккаунт – предотвращает 403 ошибки.
*   **🌐 SOCKS5/HTTP прокси:** Глобальный или индивидуальный прокси для каждого аккаунта.
*   **🛡️ Обход Cloudflare:** Встроенная система на `curl_cffi` с авто-ретраем при 403.
*   **🖥️ Web Dashboard:** Красивая панель мониторинга с отображением всех аккаунтов, приоритетов, поинтов и ссылками на стримы.
*   **📱 Telegram бот:**
    *   **Система Owner/Guest:** Владелец имеет полный контроль, гости могут только просматривать статус.
    *   **Мультиаккаунт-отображение:** Команды `/status`, `/balance`, `/accounts` показывают данные по аккаунтам.
    *   **Уведомления:** Обновления о начисленных поинтах и ошибках.
    *   **Удалённое управление:** Перезапуск майнера через Telegram.
*   **🌐 Мультиязычность:** Английский и Русский.
*   **📉 Умное логирование:** Чистый вывод с опциональным Debug-режимом.
*   **♻️ Без утечек памяти:** Сессии переиспользуются и корректно закрываются.

---

## 🚀 Установка

1.  **Клонируйте** репозиторий:
    ```bash
    git clone https://github.com/Baillora/Kick_Channel_Points_Miner.git
    cd Kick_Channel_Points_Miner
    ```

2.  **Установите зависимости**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Настройте**: Переименуйте `config.example.json` в `config.json` и заполните (см. ниже).

---

## ⚙️ Конфигурация (`config.json`)

### Мультиаккаунт (рекомендуется)

```json
{
  "Language": "en",
  "Debug": false,

  "WebDashboard": {
    "enabled": true,
    "port": 5000
  },

  "Telegram": {
    "enabled": false,
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_USER_ID",
    "allowed_users": [123456789]
  },

  "Discord": {
    "enabled": false,
    "webhook_url": "https://discord.com/api/webhooks/XXXX/YYYY",
    "username": "Baillora KickMiner",
    "avatar_url": "",
    "notify_points": true,
    "notify_status_change": true,
    "notify_errors": true,
    "notify_startup": true,
    "min_points_gain": 10,
    "color_success": 3461464,
    "color_info": 5793266,
    "color_warning": 16763904,
    "color_error": 15746887
  },
  
  "Proxy": {
    "enabled": false,
    "url": "socks5://user:password@host:port"
  },

  "Accounts": [
    {
      "alias": "Main Account",
      "token": "YOUR_KICK_TOKEN_1",
      "proxy": null,
      "streamers": ["streamer1", "streamer2", "streamer3"],
      "max_concurrent": 2
    },
    {
      "alias": "Second Account",
      "token": "YOUR_KICK_TOKEN_2",
      "proxy": "socks5://user:pass@proxy2:1080",
      "streamers": ["streamer2", "streamer3", "streamer4"],
      "max_concurrent": 1
    }
  ],

  "Check_interval": 120,
  "Reconnect_cooldown": 600,
  "Connection_stagger_min": 3,
  "Connection_stagger_max": 8
}
```

### Старый формат (совместимость сохранена)
Старый формат для одной учетной записи автоматически преобразуется:

```json
{
  "Language": "en",
  "Debug": false,
  "WebDashboard": { "enabled": true, "port": 5000 },
  "Telegram": { "enabled": false, "bot_token": "", "chat_id": "", "allowed_users": [] },
  "Private": { "token": "YOUR_KICK_TOKEN" },
  "Streamers": ["stream1", "stream2", "stream3"],
  "Max_active_channels": 5
}
```

---

### Parameters description:

*   **`Language`**:  `"en"` или `"ru"`.
*   **`Debug`**: Установить `"true"` для дополнительных логов, `"false"` для чистого вывода.
*   **`WebDashboard`**:
    *   `enabled`: установите значение `true` чтобы включить веб-панель.
    *   `port`: порт для доступа к статистике (по умолчанию: `http://localhost:5000`).
*   **`Telegram`**:
    *   `bot_token`: Получите это от @BotFather.
    *   `chat_id`: Ваш личный идентификатор в Telegram (вы будете **Владельцем**).
    *   `allowed_users`: Список идентификаторов пользователей, которые могут просматривать статус/баланс (гости).
*   **`Proxy.enabled`**: Включить глобальный прокси-сервер для всех учетных записей.
    *   `Proxy.url`: Глобальный URL-адрес прокси-сервера (`socks5://`, `http://`, `https://`).
*   **`Check_interval`**: Секунды между проверками состояния в режиме онлайн (по умолчанию: `120`).
*   **`Reconnect_cooldown`**: Секунды перед попыткой повторного подключения (по умолчанию: `600`).
*   **`Connection_stagger_min/max`**: Диапазон задержки (в секундах) между подключениями к стримерам.
*   **`👥 Параметры учетной записи`**:
    *   `alias`: Параметры учетной записи.
    *   `token`: токен проверки подлинности Kick (Bearer token).
    *   `proxy`: прокси-сервер для каждой учетной записи (переопределяет глобальный). Установите значение `null` чтобы использовать глобальный.
    *   `streamers`: упорядоченный список имен стримеров. **Позиция = приоритет** (индекс 0 = наивысший).
    *   `max_concurrent`: 	Максимальное количество стримеров для одновременного просмотра

---

## 🎯 Как работает приоритет
```
Конфиг: ["streamer1", "streamer2", "streamer3", "streamer4"]
         Приоритет 0   Приоритет 1   Приоритет 2   Приоритет 3
         (Высший)                                   (Низший)

max_concurrent: 2
```
Время | Событие | Просмотр
| :--- | :--- | :--- |
T0 | streamer2 и streamer3 в онлайне | `[streamer2, streamer3]`
T1 | streamer1 вышел в онлайн (выше приоритет) | `[streamer1, streamer2]` ← streamer3 вытеснен!
T2	| streamer1 ушёл в оффлайн | `[streamer2, streamer3]` ← streamer3 вернулся
T3	| streamer4 вышел в онлайн | `[streamer2, streamer3]` ← streamer4 ждёт (лимит)

---

### 🔑 Как получить токен Kick

1.  Зайдите на **Kick.com** и авторизуйтесь.
2.  Нажмите `F12`, чтобы открыть инструменты разработчика.
3.  Перейдите на вкладку **Network** (Сеть).
4.  Обновите страницу (`F5`).
5.  Нажмите на любой появившийся запрос (например, `auth`).
6.  В правой панели выберите вкладку **Headers** (Заголовки) и найдите раздел **Request Headers**.
7.  Найдите строку `Authorization`.
8.  Скопируйте длинную строку, которая идет **после** слова `Bearer`. Она выглядит вот так `123456789|*************************************`.
9. Вставьте эту строку в `config.json` в поле `"token"`.

---

## 🎮 Использование

Запуск майнера:
```bash
python main.py
```

Бот будет:

1. Загружать все аккаунты из конфига
2. Проверять, кто из стримеров онлайн
3. Подключаться к топ-N (по приоритету) для каждого аккаунта
4. Динамически перебалансировать при изменении статусов стримеров
5. Автоматически перезапускаться при сбоях

### 📱 Команды Telegram

| Команда | Описание | Доступ |
| :--- | :--- | :--- |
| `/start` | Запуск бота и клавиатуры | Все |
| `/status` | Статус стримеров и аптайм | Все |
| `/balance` | Баланс по всем каналам | Все |
| `/accounts` | Обзор аккаунтов | Все |
| `/help` | Список команд | Все |
| `/restart` | **Полный перезапуск майнера** | **Только Владелец** |
| `/language` | Смена языка бота (`ru`/`en`) | **Только Владелец** |

---

### 🟣 Discord Webhook

Уведомления в реальном времени в любой канал Discord через вебхуки – бот не нужен!

**Настройка:**
1. В Discord сервере: **Настройки канала → Интеграции → Вебхуки**
2. Нажмите **Новый вебхук**, скопируйте URL
3. Вставьте в `config.json` → `Discord.webhook_url`

**Конфигурация:**
```json
{
  "Discord": {
    "enabled": true,
    "webhook_url": "https://discord.com/api/webhooks/XXXX/YYYY",
    "username": "Baillora KickMiner",
    "avatar_url": "",
    "notify_points": true,
    "notify_status_change": true,
    "notify_errors": true,
    "notify_startup": true,
    "min_points_gain": 10,
    "color_success": 3461464,
    "color_info": 5793266,
    "color_warning": 16763904,
    "color_error": 15746887
  }
}
```

| Parameter | Description |
| :--- | :--- | 
| `webhook_url` | URL вебхука Discord |
| `username` | Имя бота в Discord |
| `avatar_url` | 	URL аватара (опционально) |
| `notify_points` | Уведомления о начислении поинтов |
| `notify_status_change` | Уведомления об изменении статуса стримеров |
| `notify_errors` | Уведомления об ошибках |
| `notify_startup` | Сводка при запуске |
| `min_points_gain` | Минимальное начисление для уведомления |
| `color_*` | 	Преобразуйте цвета в десятичную форму (используйте [color converter](https://www.mathsisfun.com/hexadecimal-decimal-colors.html)) |

Notifications include:

* 🚀 Сводка при запуске со всеми аккаунтами
* 💰 Начисление поинтов (со ссылкой на стример)
* ▶️ Начало просмотра / ⏹ Вытеснение по приоритету
* 🟢 Стример онлайн / 🔴 Стример оффлайн
* ❌ Отчёты об ошибках
* 🔄 Уведомления о перезапуске

---

## 🖥️ Веб-дашборд

Если включено в конфиге, откройте **`http://localhost:5000`** в браузере.
Вы увидите таблицу в реальном времени:
*   📊 Все аккаунты с лимитами и активными стримерами
*   🎯 Бейджи приоритетов
*   👁 Статусы в реальном времени (watching/online/offline)
*   💰 Баланс поинтов по каждому стримеру
*   🔗 Кнопки «Watch» для перехода на стрим на Kick.com
*   🔒 Статус прокси
*   ⚠️ Счётчики ошибок

---

## 🌐  Proxy Support

| Тип | Формат | Пример |
| :--- | :--- | :--- |
| SOCKS5 | `socks5://user:pass@host:port` | `socks5://admin:123@proxy.com:1080` |
| SOCKS5 (no auth) | `socks5://host:port` | `socks5://proxy.com:1080` |
| HTTP | `http://user:pass@host:port` | `http://admin:123@proxy.com:8080` |
| HTTPS | `https://host:port` | `https://proxy.com:8080` |

Глобальный прокси применяется ко всем аккаунтам. Прокси аккаунта переопределяет глобальный.

---
## 📁 Структура проекта

```
Kick_Channel_Points_Miner/
├── main.py                    # Точка входа
├── account_manager.py         # Мультиаккаунт-оркестратор с приоритетами
├── config.json                # Конфигурация
├── web_server.py              # Flask Web Dashboard
├── localization.py            # Загрузчик локализации
├── requirements.txt           # Зависимости
├── _websockets/
│   ├── ws_connect.py          # WebSocket клиент с поддержкой прокси
│   └── ws_token.py            # Получение WS-токена
├── utils/
│   ├── kick_utility.py        # Получение Channel/Stream ID
│   └── get_points_amount.py   # Проверка баланса поинтов
├── tg_bot/
│   ├── bot.py                 # Telegram бот с мультиаккаунтом
│   └── lang/
│       ├── en.lang            # Английские строки
│       └── ru.lang            # Русские строки
└── lang/
    ├── en.lang                # Английские сообщения логов
    └── ru.lang                # Русские сообщения логов
```
---

## 🐳 Развертывание через Docker & Portainer

Это рекомендуемый способ запуска майнера в фоновом режиме (headless) – отлично подходит для домашних серверов, NAS-устройств или любых машин с установленным **Portainer**.

### Предварительные условия
* Установленный [Docker](https://docs.docker.com/get-docker/) (Desktop или Engine).
* Настроенный и рабочий `config.json` (скопируйте `config.example.json` и отредактируйте его перед запуском).

---

### Вариант 1 – Docker CLI (быстрый способ)

```bash
# 1. Соберите образ (запускать из корня проекта)
docker build -t kick-channel-points-miner .

# 2. Запустите контейнер
docker run -d \
  --name kick-miner \
  --restart unless-stopped \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  -p 5000:5000 \
  kick-channel-points-miner
```

Панель управления → **http://localhost:5000**

---

### Вариант 2 – Docker Compose

```bash
# Убедитесь, что config.json находится в той же папке, что и docker-compose.yml
docker compose up -d
```

Остановить: `docker compose down`  
Посмотреть логи: `docker compose logs -f`

---

### Вариант 3 – Portainer (GUI, beginner-friendly)

https://github.com/Baillora/Kick_Channel_Points_Miner/issues/4#issuecomment-3944659440

> **Совет:** Portainer автоматически перезапустит контейнер при сбое или перезагрузке сервера благодаря `restart: unless-stopped`.

---

### Структура проекта (с файлами Docker)

```
Kick_Channel_Points_Miner/
├── Dockerfile             # Инструкции по сборке контейнера
├── docker-compose.yml     # Compose файл для Docker / Portainer
├── .dockerignore          # Исключает config.json и dev-файлы из образа
├── config.json            # ← Создается вами (bind-mounted, не встраивается в образ)
└── ...
```

> **Примечание по безопасности:** `config.json` **никогда не встраивается в образ**. Он всегда монтируется во время выполнения, поэтому ваши токены остаются только на вашем хосте.


## ⚠️ Отказ от ответственности

Это программное обеспечение создано исключительно в образовательных целях. Используйте его на свой страх и риск. Разработчик не несет ответственности за возможные блокировки аккаунтов на Kick.com.

---

## 📜 Лицензия

Этот проект распространяется под лицензией MIT. Подробности смотрите в файле [LICENSE](LICENSE).
