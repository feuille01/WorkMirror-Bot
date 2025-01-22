import datetime
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from states import (
    ASK_ROLE,
    ASK_COMPANY,
    RESULTS_COMPANY,
    RESULTS_ACCESS,
    RESULTS_FLOW,
    ADD_QUESTIONS_COMPANY,
    ADD_QUESTIONS_ACCESS,
    MANAGE_QUESTIONS_MENU,
    CHOOSE_QUESTION_TYPE,
    ASK_NUMERIC_MIN,
    ASK_NUMERIC_MAX,
    ASK_OPEN_TEXT_LENGTH,
    ADD_QUESTIONS_TEXT,
    ANSWERS_FLOW,
)

from database.db import SessionLocal
from database.models import Company, Question, Answer, AccessCode, AnalysisLog
from services.validators import validate_answer, save_constraints, check_access_code
from services.gpt_service import request_yandex_gpt


from config import MAX_TRIES, YES_NO_VALID, DEFAULT_MAX_LENGTH


def main_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["Ответить на вопросы"],
        ["Результаты"],
        ["Управление вопросами"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start — Начальное меню.
    """
    await update.message.reply_text(
        "Привет! Выберите действие:",
        reply_markup=main_menu_markup()  # вызываем функцию
    )
    return ASK_ROLE


async def handle_role_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["tries"] = 0

    if text == "Ответить на вопросы":
        await update.message.reply_text(
            "Введите код компании:",
            reply_markup=ReplyKeyboardMarkup(
                [["Главное меню"]],
                resize_keyboard=True
            )
        )
        return ASK_COMPANY

    elif text == "Результаты":
        await update.message.reply_text(
            "Введите код компании:",
            reply_markup=ReplyKeyboardMarkup(
                [["Главное меню"]],
                resize_keyboard=True
            )
        )
        return RESULTS_COMPANY

    elif text == "Управление вопросами":
        await update.message.reply_text(
            "Введите код компании для управления вопросами:",
            reply_markup=ReplyKeyboardMarkup(
                [["Главное меню"]],
                resize_keyboard=True
            )
        )
        return ADD_QUESTIONS_COMPANY

    elif text == "Главное меню":
        # На случай, если пользователь напишет "Главное меню"
        await update.message.reply_text("Вы уже в главном меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    else:
        await update.message.reply_text("Неизвестная команда. Пожалуйста, выберите действие.",
                                        reply_markup=main_menu_markup())
        return ASK_ROLE


# 5.1 "Ответить на вопросы"

async def ask_company_for_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    session = SessionLocal()
    company_code = update.message.text.strip()

    # Увеличиваем счётчик
    context.user_data["tries"] = context.user_data.get("tries", 0) + 1

    # Проверяем компанию
    company = session.query(Company).filter_by(company_code=company_code).first()
    if not company:
        if context.user_data["tries"] >= MAX_TRIES:
            # Превысили кол-во попыток, возвращаем в главное меню
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Компания не найдена. Введите код ещё раз:",
                                            reply_markup=ReplyKeyboardMarkup(
                                                [["Главное меню"]], resize_keyboard=True
                                            ))
            session.close()
            return ASK_COMPANY

    # Сохраняем в user_data
    context.user_data["answers_company_code"] = company_code
    context.user_data["question_index"] = 0
    context.user_data["tries"] = 0

    await update.message.reply_text("Код принят! Сейчас мы зададим вам несколько вопросов.")
    session.close()
    # Переходим к первому вопросу
    return await ask_next_question(update, context)


async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выводим следующий вопрос (если есть) и переходим к состоянию ANSWERS_FLOW.
    """
    session = SessionLocal()
    company_code = context.user_data.get("answers_company_code")
    company = session.query(Company).filter_by(company_code=company_code).first()

    # Получаем список вопросов
    questions = session.query(Question).filter_by(company_id=company.id).all()

    if not questions:  # если список пуст, значит вопросов у компании нет
        await update.message.reply_text(
            "У этой компании ещё нет вопросов.",
            reply_markup=main_menu_markup()
        )
        return ASK_ROLE

    session.close()

    q_index = context.user_data.get("question_index", 0)

    if q_index < len(questions):
        question_text = questions[q_index].question_text
        await update.message.reply_text(f"Вопрос {q_index+1}:\n{question_text}")
        return ANSWERS_FLOW
    else:
        await update.message.reply_text(
            "Спасибо, все вопросы пройдены!",
            reply_markup=main_menu_markup()
        )
        return ASK_ROLE

async def receive_answer_and_ask_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение ответа, переход к следующему вопросу.
    """
    text = update.message.text.strip().lower()

    if text == "главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        context.user_data["question_index"] = 0
        return ASK_ROLE
    session = SessionLocal()
    company_code = context.user_data.get("answers_company_code")
    company = session.query(Company).filter_by(company_code=company_code).first()

    questions = session.query(Question).filter_by(company_id=company.id).all()
    q_index = context.user_data.get("question_index", 0)

    # Если индекс в пределах вопросов, сохраняем ответ
    if q_index < len(questions):
        answer_text = update.message.text.strip()
        q = questions[q_index]

        # вызываем validate_answer
        is_valid, err = validate_answer(q, answer_text)
        if not is_valid:
            await update.message.reply_text(err)
            session.close()
            # повторяем тот же вопрос
            return ANSWERS_FLOW

        # Сохранение
        user_id = str(update.message.from_user.id)
        new_answer = Answer(
            company_id=company.id,
            question_id=q.id,
            user_id=user_id,
            answer_text=answer_text
        )
        session.add(new_answer)
        session.commit()

        # Переход к следующему вопросу
        q_index += 1
        context.user_data["question_index"] = q_index
        session.close()

        return await ask_next_question(update, context)
    else:
        session.close()
        await update.message.reply_text("Все вопросы уже были заданы.")
        return ASK_ROLE


# 5.2 "Результаты"

async def ask_company_for_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Пользователь вводит код компании, проверяем, существует ли она.
    Если да — просим ввести код доступа, если нет — завершаем.
    """
    session = SessionLocal()
    company_code = update.message.text.strip()

    if company_code == "Главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    context.user_data["tries"] = context.user_data.get("tries", 0) + 1

    company = session.query(Company).filter_by(company_code=company_code).first()
    if not company:
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Компания не найдена. Введите код ещё раз:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню"]],
                                                                             resize_keyboard=True))
            session.close()
            return RESULTS_COMPANY

    context.user_data["results_company_code"] = company_code
    context.user_data["tries"] = 0
    session.close()

    await update.message.reply_text("Введите код доступа:",
        reply_markup=ReplyKeyboardMarkup([["Главное меню", "Назад"]], resize_keyboard=True)
    )

    return RESULTS_ACCESS


async def check_access_and_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получаем код доступа, проверяем, если верный — собираем ответы, отправляем в YaGPT на анализ, выводим результат.
    """
    session = SessionLocal()
    access_code = update.message.text.strip()
    company_code = context.user_data.get("results_company_code")

    if access_code == "Главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE
    elif access_code == "Назад":
        # Вернём на RESULTS_ACCESS
        await update.message.reply_text(
            "Введите код компании:",
            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
        )
        return RESULTS_COMPANY

    context.user_data["tries"] = context.user_data.get("tries", 0) + 1

    # Проверка компании
    company = session.query(Company).filter_by(company_code=company_code).first()
    if not company:
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Компания не найдена, введите код ещё раз:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True))
            session.close()
            return RESULTS_COMPANY

    # Проверка хеша
    acc = session.query(AccessCode).filter_by(company_id=company.id).first()
    if not acc or not check_access_code(access_code, acc.access_code):
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Неверный код доступа, введите снова:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True))
            session.close()
            return RESULTS_ACCESS

    context.user_data["tries"] = 0
    await update.message.reply_text("Выполняется анализ, пожалуйста подождите...")

    # Сборка ответов
    answers_query = (
        session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.company_id == company.id)
    )

    all_answers = []
    for ans, q in answers_query:
        all_answers.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "answer_text": ans.answer_text,
            "created_at": ans.created_at.isoformat()
        })

    # проверка на пустоту
    if not all_answers:
        all_answers = [{
            "question_id": 0,
            "question_text": "нет ответов",
            "answer_text": "Пока никто не отвечал",
            "created_at": datetime.datetime.now().isoformat()
        }]

    reviews_str = "\n".join(f"Вопрос: {r['question_text']}\nОтвет: {r['answer_text']}"
                            for r in all_answers)

    user_text = (
            "Анализируй эти отзывы:\n"
            + reviews_str +
            "\nОпредели тональность, основные проблемы и рекомендации."
    )

    # передаём строку в функцию
    gpt_response = request_yandex_gpt(user_text)

    answer_text = gpt_response.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
    if not answer_text:
        answer_text = "Пустой ответ или ошибка анализа."

    await update.message.reply_text(f"Результаты анализа:\n{answer_text}")

    # Сохраняем в analysis_logs
    analysis_log = AnalysisLog(
        company_id=company.id,
        analysis_result=json.dumps(gpt_response, ensure_ascii=False)
    )
    session.add(analysis_log)
    session.commit()
    session.close()

    # Предлагаем выгрузить в документ (inline-кнопки).
    # Обратите внимание, что обработчик колбэка в callbacks.py
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        [InlineKeyboardButton("Выгрузить в документ", callback_data="export_doc")],
        [InlineKeyboardButton("Не выгружать", callback_data="export_no")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    # Сохраним answer_text в user_data, чтобы при выгрузке использовать
    context.user_data["answer_text"] = answer_text

    await update.message.reply_text("Выгрузить результаты?", reply_markup=markup)
    return RESULTS_FLOW


# 5.3 "Управление вопросами"

async def ask_company_for_add_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохраняем код компании для добавления вопросов. Просим ввести код доступа.
    """
    company_code = update.message.text.strip()

    if company_code == "Главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    context.user_data["tries"] = context.user_data.get("tries", 0) + 1
    session = SessionLocal()
    company = session.query(Company).filter_by(company_code=company_code).first()

    if not company:
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Компания не найдена. Введите код ещё раз:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True))
            session.close()
            return ADD_QUESTIONS_COMPANY

    context.user_data["temp_company_code_for_questions"] = company_code
    context.user_data["tries"] = 0
    session.close()

    await update.message.reply_text(
        "Введите код доступа для управления вопросами:",
        reply_markup=ReplyKeyboardMarkup([["Главное меню", "Назад"]], resize_keyboard=True)
    )
    return ADD_QUESTIONS_ACCESS


async def check_access_and_add_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяем код доступа. Если верный, разрешаем добавление вопроса.
    """
    plain_code = update.message.text.strip()

    if plain_code == "Главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE
    elif plain_code == "Назад":
        await update.message.reply_text(
            "Введите код компании для управления вопросами:",
            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
        )
        return ADD_QUESTIONS_COMPANY

    session = SessionLocal()
    company_code = context.user_data.get("temp_company_code_for_questions")
    context.user_data["tries"] = context.user_data.get("tries", 0) + 1
    company = session.query(Company).filter_by(company_code=company_code).first()

    if not company:
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Компания не найдена, введите снова:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True))
            session.close()
            return ADD_QUESTIONS_COMPANY

    acc = session.query(AccessCode).filter_by(company_id=company.id).first()

    if not acc or not check_access_code(plain_code, acc.access_code):
        if context.user_data["tries"] >= MAX_TRIES:
            await update.message.reply_text("Превышено число попыток. Возврат в главное меню.",
                                            reply_markup=main_menu_markup())
            session.close()
            return ASK_ROLE
        else:
            await update.message.reply_text("Неверный код доступа, введите снова:",
                                            reply_markup=ReplyKeyboardMarkup([["Главное меню", "Назад"]],
                                                                             resize_keyboard=True))
            session.close()
            return ADD_QUESTIONS_ACCESS

    context.user_data["tries"] = 0
    session.close()
    return await manage_questions_menu(update, context)


async def manage_questions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показать inline-кнопки: Добавить вопрос, Удалить вопрос, Список вопросов, Главное меню.
    На нажатия кнопок ответит manage_questions_menu_callback (в callbacks.py).
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [InlineKeyboardButton("Добавить вопрос", callback_data="mng_add_q")],
        [InlineKeyboardButton("Удалить вопрос", callback_data="mng_del_q")],
        [InlineKeyboardButton("Список вопросов", callback_data="mng_list_q")],
        [InlineKeyboardButton("Главное меню", callback_data="mng_go_main")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.message.reply_text("Выберите действие:", reply_markup=markup)
        return "MANAGE_QUESTIONS_MENU"
    else:
        await update.message.reply_text("Выберите действие:", reply_markup=markup)
        return "MANAGE_QUESTIONS_MENU"


# Удалить вопрос
async def delete_question_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Если "Назад" -> вернуться в меню управления
    if text.lower() == "назад":
        return await manage_questions_menu(update, context)

    # Попытка распарсить номер
    try:
        number = int(text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return "DELETE_QUESTION"

    # Удаляем вопрос
    session = SessionLocal()
    code = context.user_data["temp_company_code_for_questions"]
    comp = session.query(Company).filter_by(company_code=code).first()

    if not comp:
        await update.message.reply_text("Компания не найдена.")
        session.close()
        return await manage_questions_menu(update, context)

    # Находим вопрос, index=number
    qs = session.query(Question).filter_by(company_id=comp.id).all()
    if number<1 or number>len(qs):
        await update.message.reply_text("Нет вопроса с таким номером, введите снова или 'Назад'.")
        session.close()
        return "DELETE_QUESTION"

    q = qs[number-1]
    q_text = q.question_text
    session.delete(q)
    session.commit()
    session.close()

    await update.message.reply_text(f"Вопрос: «{number}. {q_text}» удалён.")
    # Возвращаемся в меню управления
    return await manage_questions_menu(update, context)


async def ask_numeric_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Пользователь вводит минимальное значение для numeric-вопроса.
    Если ввёл "Назад" — возвращаемся к выбору типа вопроса.
    """
    text = update.message.text.strip().lower()
    if text == "главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    if text == "назад":
        # Возвращаемся в состояние выбора типа вопроса CHOOSE_QUESTION_TYPE
        from .callbacks import choose_question_type_callback
        # Можно просто попросить пользователя нажать кнопку заново,
        # либо напрямую вызвать manage_questions_menu.
        buttons = [
            [
                InlineKeyboardButton("Да/Нет", callback_data="type_yes_no"),
                InlineKeyboardButton("Оценка(диапазон)", callback_data="type_numeric"),
                InlineKeyboardButton("Открытый вопрос", callback_data="type_open_text")
            ],
            [InlineKeyboardButton("Назад", callback_data="mng_menu_back")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Вы вернулись к выбору типа вопроса:", reply_markup=markup)
        return CHOOSE_QUESTION_TYPE

    # Парсим число
    try:
        min_val = int(text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число или «Назад».")
        return ASK_NUMERIC_MIN

    context.user_data["numeric_min"] = min_val
    await update.message.reply_text(
        "Введите максимальное значение или «Назад»:",
        reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
    )
    return ASK_NUMERIC_MAX


async def ask_numeric_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Пользователь вводит максимальное значение.
    Если всё ок — формируем constraints и просим ввести текст вопроса.
    """
    text = update.message.text.strip().lower()

    if text == "назад":
        # Возврат к вводу минимального значения
        await update.message.reply_text(
            "Введите минимальное значение:",
            reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
        )
        return ASK_NUMERIC_MIN

    if text == "главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    try:
        max_val = int(text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число или 'Назад'.")
        return ASK_NUMERIC_MAX

    context.user_data["numeric_max"] = max_val

    # Формируем constraints и сохраняем в user_data
    c = {
        "min_value": context.user_data.get("numeric_min", 0),
        "max_value": max_val
    }
    context.user_data["constraints"] = save_constraints(c)

    await update.message.reply_text(
        "Теперь введите текст вопроса:",
        reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
    )
    return ADD_QUESTIONS_TEXT


async def ask_open_text_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Пользователь вводит максимальную длину (целое число, 0 или 'нет' — значит DEFAULT_MAX_LENGTH).
    """
    text = update.message.text.strip().lower()
    if text == "главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    if text == "назад":
        # Возвращаемся к выбору типа вопроса
        from .callbacks import choose_question_type_callback
        buttons = [
            [
                InlineKeyboardButton("Да/Нет", callback_data="type_yes_no"),
                InlineKeyboardButton("Оценка(диапазон)", callback_data="type_numeric"),
                InlineKeyboardButton("Открытый вопрос", callback_data="type_open_text")
            ],
            [InlineKeyboardButton("Назад", callback_data="mng_menu_back")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Вы вернулись к выбору типа вопроса:", reply_markup=markup)
        return CHOOSE_QUESTION_TYPE

    if text in ["0", "нет"]:
        max_len = DEFAULT_MAX_LENGTH
    else:
        try:
            max_len = int(text)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите целое число, '0' или 'нет'.")
            return ASK_OPEN_TEXT_LENGTH

    c = {"max_length": max_len}
    context.user_data["constraints"] = save_constraints(c)

    await update.message.reply_text(
        "Теперь введите текст вопроса:",
        reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
    )
    return ADD_QUESTIONS_TEXT


async def receive_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Пользователь вводит текст вопроса. Создаём вопрос в БД, используя
    context.user_data["new_question_type"] и context.user_data["constraints"].
    """
    text = update.message.text.strip()
    if text.lower() == "главное меню":
        await update.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE
    elif text.lower() == "назад":
        # Логика возврата зависит от того, какой у нас тип вопроса.
        q_type = context.user_data.get("new_question_type", "")
        if q_type == "numeric":
            # Возвращаемся к ASK_NUMERIC_MAX
            await update.message.reply_text(
                "Измените максимальное значение:",
                reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
            )
            return ASK_NUMERIC_MAX
        elif q_type == "open_text":
            # Возвращаемся к ASK_OPEN_TEXT_LENGTH
            await update.message.reply_text(
                "Введите максимальную длину (0 или 'нет' — без ограничений):",
                reply_markup=ReplyKeyboardMarkup([["Назад", "Главное меню"]], resize_keyboard=True)
            )
            return ASK_OPEN_TEXT_LENGTH
        else:
            # По умолчанию, если тип не распознан (yes/no), возвращаемся к выбору типа
            from .callbacks import choose_question_type_callback
            buttons = [
                [
                    InlineKeyboardButton("Да/Нет", callback_data="type_yes_no"),
                    InlineKeyboardButton("Оценка(диапазон)", callback_data="type_numeric"),
                    InlineKeyboardButton("Открытый вопрос", callback_data="type_open_text")
                ],
                [InlineKeyboardButton("Назад", callback_data="mng_menu_back")]
            ]
            markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text("Вы вернулись к выбору типа вопроса:", reply_markup=markup)
            return CHOOSE_QUESTION_TYPE

    # Сохраняем вопрос в БД
    session = SessionLocal()
    company_code = context.user_data.get("temp_company_code_for_questions")
    company = session.query(Company).filter_by(company_code=company_code).first()
    if not company:
        await update.message.reply_text("Компания не найдена.", reply_markup=main_menu_markup())
        session.close()
        return ASK_ROLE

    q_type = context.user_data.get("new_question_type", "")
    constraints = context.user_data.get("constraints", "{}")

    new_q = Question(
        company_id=company.id,
        question_text=text,
        question_type=q_type,
        constraints=constraints
    )
    session.add(new_q)
    session.commit()
    session.close()

    await update.message.reply_text("Вопрос успешно добавлен!")

    # Возвращаемся в меню управления вопросами
    return await manage_questions_menu(update, context)