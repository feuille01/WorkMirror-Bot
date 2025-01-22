import os
from dotenv import load_dotenv

load_dotenv()  # Считываем переменные из .env

# Токен телеграм-бота (из .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройки для YandexGPT
YANDEX_GPT_API_ENDPOINT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_FOLDER_ID   = os.getenv("YANDEX_FOLDER_ID")

# Путь к базе данных SQLite
DB_PATH = "sqlite:///WorkMirror_bot.db"

# Количество попыток, допустимые ответы и т.д.
MAX_TRIES   = 3
YES_NO_VALID = ["да", "нет", "yes", "no"]

# Если нужна «большая длина» для открытых текстов (убираем «магическое» 9999)
DEFAULT_MAX_LENGTH = 9999

# Дополнительные параметры для запроса к Yandex GPT (если хотите вынести и их)
YANDEX_GPT_TEMPERATURE = 0.8
YANDEX_GPT_MAX_TOKENS  = 1000