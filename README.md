# WorkMirror-Bot
Сервис, помогающий компаниям анализировать отзывы сотрудников, выявлять проблемные области и находить пути для улучшения рабочих процессов и корпоративной культуры.

WorkMirror Bot — это Telegram-бот для опросов и анализа отзывов сотрудников. Он позволяет:
1.	Добавлять вопросы (в т.ч. разных типов: да/нет, числовые, открытый текст),
2.	Отвечать на них,
3.	Анализировать результаты с помощью Yandex GPT,
4.	Выгружать результаты анализа в PDF/DOCX/TXT.
1. Краткое описание
•	Язык: Python 3.
•	Библиотеки:
    o	python-telegram-bot для работы с Telegram API,
    o	SQLAlchemy для ORM и работы с БД,
    o	ReportLab и python-docx для генерации файлов,
    o	bcrypt для хеширования кодов доступа,
    o	requests для HTTP-запросов к Yandex GPT,
    o	dotenv для подгрузки переменных окружения.
•	База данных: SQLite (файл WorkMirror_bot.db по умолчанию).
________________________________________
2. Требования
•	Python 3.9+ (желательно, но может работать и на 3.7+).
•	Установленные библиотеки из requirements.txt.
Примечание. Версии библиотек указываются в вашем requirements.txt, который вы генерируете с помощью pip freeze > requirements.txt.
________________________________________
3. Установка и запуск
3.1 Клонирование репозитория

git clone https://github.com/ваш_аккаунт/WorkMirror_bot.git
cd WorkMirror_bot

3.2 Создание виртуального окружения (рекомендуется)

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

3.3 Установка зависимостей

pip install -r requirements.txt

3.4 Настройка переменных окружения

В корне проекта должен лежать файл .env со следующими переменными:

TELEGRAM_BOT_TOKEN=<Ваш_телеграм_токен>
YANDEX_OAUTH_TOKEN=<Ваш_Yandex_OAuth_токен>
YANDEX_FOLDER_ID=<Ваш_FolderID_от_Yandex>
•	TELEGRAM_BOT_TOKEN — токен Telegram-бота (можно получить у @BotFather).
•	YANDEX_OAUTH_TOKEN — OAuth-токен, используемый для получения IAM-токена в Яндекс.
•	YANDEX_FOLDER_ID — идентификатор каталога в Яндекс.Cloud.

3.5 Запуск бота

python -m bot.main

Если всё в порядке, бот запустится и начнёт опрашивать Telegram API. В консоли будет отображаться информация о запуске.
________________________________________

4. Структура проекта
Проект разделён на пакеты, чтобы упростить поддержку и масштабирование.
markdown

WorkMirror_bot/
    ├─ bot/
    │   ├─ main.py
    │   ├─ handlers.py
    │   ├─ callbacks.py
    │   ├─ conversation.py
    │   └─ states.py
    ├─ database/
    │   ├─ db.py
    │   └─ models.py
    ├─ services/
    │   ├─ file_generator.py
    │   ├─ gpt_service.py
    │   └─ validators.py
    ├─ config.py
    ├─ .env
    ├─ requirements.txt
    └─ README.md 

4.1 config.py

•	Содержит константы и переменные окружения (читаются через dotenv).
•	Пример:
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_FOLDER_ID   = os.getenv("YANDEX_FOLDER_ID")

DB_PATH = "sqlite:///WorkMirror_bot.db"

MAX_TRIES = 3
YES_NO_VALID = ["да", "нет", "yes", "no"]
DEFAULT_MAX_LENGTH = 9999

YANDEX_GPT_API_ENDPOINT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_GPT_TEMPERATURE = 0.8
YANDEX_GPT_MAX_TOKENS  = 1000

4.2 Папка database/
1.	models.py — объявление моделей SQLAlchemy: Company, AccessCode, Question, Answer, AnalysisLog.
2.	db.py — создание движка (engine), инициализация таблиц, SessionLocal.

4.3 Папка services/
•	gpt_service.py — функции для работы с Яндекс GPT (get_iam_token, request_yandex_gpt).
•	file_generator.py — генерация файлов PDF/DOCX/TXT (generate_file).
•	validators.py — функции валидации ответов, проверки кода доступа, JSON-констрейнтов.

4.4 Папка bot/
•	main.py — точка входа, где создаётся Application, регистрируется ConversationHandler и вызывается run_polling().
•	conversation.py — конфигурация ConversationHandler, привязка состояний к хендлерам.
•	handlers.py — функции обработки текстовых сообщений (например, /start, ввод кода компании, вопросы и т.д.).
•	callbacks.py — обработка inline-кнопок (CallbackQueryHandler).
•	states.py — набор констант состояний, чтобы избежать циклических импортов.
________________________________________

5. Основные сущности (ORM-модели)
5.1 Company
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    company_code = Column(String, unique=True, nullable=False)
    company_name = Column(String, nullable=True)

    questions = relationship("Question", back_populates="company")
    access_codes = relationship("AccessCode", back_populates="company")
•	company_code — уникальный код компании, вводимый пользователем.
•	company_name — название компании (необязательно).
5.2 AccessCode
class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    access_code = Column(String, nullable=False)  # хранится в хешированном виде
•	access_code — код доступа, захешированный через bcrypt.
5.3 Question
class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=True)
    constraints   = Column(Text, nullable=True)  # JSON

    company = relationship("Company", back_populates="questions")
5.4 Answer
class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(String, nullable=True)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
5.5 AnalysisLog
class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    analysis_result = Column(Text, nullable=True)  # JSON-ответ от YandexGPT
________________________________________
6. Основные процессы
6.1 Сценарий «Ответить на вопросы»
1.	Пользователь выбирает «Ответить на вопросы».
2.	Бот запрашивает код компании (company_code).
3.	Если компания найдена в БД — бот начинает задавать вопросы, сохраняет ответы (Answer).
6.2 Сценарий «Результаты»
1.	Пользователь выбирает «Результаты».
2.	Бот просит ввести код компании, затем код доступа.
3.	Если проверка прошла, бот собирает все ответы из БД, формирует строку отзывов и отправляет в request_yandex_gpt.
4.	Отображается результат анализа, предлагается выгрузка в документ (PDF/DOCX/TXT).
6.3 Сценарий «Управление вопросами»
1.	Пользователь выбирает «Управление вопросами».
2.	Вводит код компании, код доступа (хеш в AccessCode).
3.	Меню добавления/удаления/списка вопросов.
•	Добавить вопрос: бот спрашивает тип вопроса (да/нет, numeric, открытый текст), констрейнты (min/max, длину), текст вопроса.
•	Удалить: бот выводит список, пользователь выбирает номер вопроса, идёт удаление.
________________________________________
7. Взаимодействие с Yandex GPT
1.	Получение IAM-токена (get_iam_token):
def get_iam_token():
    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        json={"yandexPassportOauthToken": YANDEX_OAUTH_TOKEN}
    )
    response.raise_for_status()
    return response.json()["iamToken"]
2.	Отправка запроса (request_yandex_gpt):
def request_yandex_gpt(user_text: str) -> dict:
    token = get_iam_token()
    headers = {"Authorization": f"Bearer {token}", ...}
    data = {...}  # Формируем payload
    response = requests.post(YANDEX_GPT_API_ENDPOINT, headers=headers, json=data)
    return response.json()
3.	Интеграция: при вводе «Результаты» бот формирует общий текст отзывов, отправляет их в Я.GPT и получает «анализ», который выводит пользователю.
________________________________________
8. Генерация файлов PDF/DOCX/TXT
Модуль file_generator.py обеспечивает функцию generate_file(text, fmt):
•	При fmt="pdf":
•	Использует ReportLab (reportlab.pdfbase, SimpleDocTemplate и т.д.).
•	Важно наличие шрифта (например, DejaVuSans.ttf) и правильный путь к нему.
•	При fmt="docx":
•	Использует python-docx.
•	При fmt="txt":
•	Создаёт обычный текстовый файл.
После генерации бот отправляет полученный файл пользователю.
________________________________________
9. Настройка шрифта для PDF
ReportLab требует наличия шрифта, например, DejaVuSans.ttf. Поместите его в папку services/ или другую директорию и укажите верный путь:
font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

________________________________________
10. Стартовые данные и добавление компаний
•	Чтобы бот нашёл код компании, в таблице companies должна быть соответствующая запись.
•	Если в базе нет записей, добавьте тестовую компанию вручную или через скрипт:
from database.db import SessionLocal
from database.models import Company

session = SessionLocal()
new_company = Company(company_code="test123", company_name="Test Company")
session.add(new_company)
session.commit()
session.close()
Также добавьте AccessCode, предварительно захешируйте код c помощью: 

import bcrypt
plain_code = "123"
hashed = bcrypt.hashpw(plain_code.encode('utf-8'), bcrypt.gensalt())
hashed_str = hashed.decode('utf-8')
print(hashed_str)bcrypt.hashpw).

________________________________________
11. Запуск и использование
    1)	Запустить бота: python -m bot.main.
    2)	В Telegram открыть ваш бот по @username и отправить /start.
    3)	Выбрать одно из меню:
    •	 «Ответить на вопросы» — ввод кода компании -> отвечаем на вопросы.
    •	«Результаты» — ввод кода компании -> ввод access code -> анализ от Я.GPT.
    •	«Управление вопросами» — код компании -> access code -> меню добавления/удаления.
________________________________________
12. Тестирование и отладка
    •	Логи: основной вывод происходит в консоль. Если бот молчит, проверьте, нет ли ошибок при запуске.
    •	Дублирование кодов: если company_code уже есть в БД и поле unique=True, при попытке добавить новую компанию с тем же кодом выбросится ошибка.
    •	Установка логгера: для более детальной отладки можно настроить logging в Python (например, logging.basicConfig(level=logging.INFO)).
________________________________________
13. Часто встречающиеся проблемы
    1)	Компания не найдена
    •	Убедитесь, что компания есть в БД.
    •	Проверьте ввод пользователя: лишние пробелы, регистр символов.
    •	По возможности используйте func.lower(Company.company_code) == company_code.lower().
    2)	Неверный код доступа
    •	Проверяйте, что в access_codes хранится захешированное значение.
    •	При проверке используйте bcrypt.checkpw.
    3)	Не генерируется PDF
    •	Убедитесь, что у вас есть файл шрифта.
    •	Проверьте путь (os.path.exists(font_path)).
    •	При необходимости используйте системный путь (например, C:/Windows/Fonts/DejaVuSans.ttf).
    4)	Ошибка при анализе (Yandex GPT)
    •	Проверьте валидность YANDEX_OAUTH_TOKEN.
    •	Убедитесь, что проект Яндекс.Cloud активен и YANDEX_FOLDER_ID верен.
    •	Убедитесь, что в запросе modelUri корректен: f"gpt://{YANDEX_FOLDER_ID}/yandexgpt".
________________________________________
14. Расширение и кастомизация
    •	Дополнительные типы вопросов: вы можете расширить функцию validate_answer или добавить новые поля в Question.
    •	Дополнительная логика анализа: например, обрабатывать результаты Yandex GPT, выделять ключевые слова и т.д.
    •	Поддержка нескольких ботов: добавьте дополнительные переменные окружения или конфигурации.
________________________________________
15. Заключение
WorkMirror Bot упрощает сбор и анализ отзывов. Архитектура бота (с разделением на модули bot/, services/, database/, config.py) облегчает сопровождение и дальнейшее развитие. При возникновении вопросов или проблем смотрите логи, проверяйте корректность БД и путей к шрифтам.
Если у вас есть идеи по улучшению, обращайтесь по контактным данным.
________________________________________
Контакты
•	Основной разработчик: Цепелев Кирилл (Telegram: @feuillenoire)
•	Разработчик: Головко Александр (Telegram: @g0_al3)
•	Разработчик: Непеин Артемий (Telegram: @pofack06)
Спасибо за использование WorkMirror Bot!

