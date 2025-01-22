import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import ContextTypes

from bot.handlers import (
    main_menu_markup,
    manage_questions_menu
)
from bot.states import CHOOSE_QUESTION_TYPE
from services.file_generator import generate_file
from database.db import SessionLocal
from database.models import Company, Question
from conversation import (
    # Состояния из conversation.py
    ASK_ROLE,
    RESULTS_FLOW,
    ADD_QUESTIONS_TEXT,
)


# CALLBACKS ДЛЯ "РЕЗУЛЬТАТОВ" (экспорт документа)
async def export_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "export_no":
        await query.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    elif data == "export_doc":
        buttons = [
            [InlineKeyboardButton("PDF", callback_data="format_pdf"),
             InlineKeyboardButton("DOCX", callback_data="format_docx"),
             InlineKeyboardButton("TXT", callback_data="format_txt")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text("Выберите формат, нажав на кнопку:", reply_markup=markup)
        return "EXPORT_TG_FORMAT"

    elif data == "export_main_menu":
        await query.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    else:
        await query.message.reply_text("Пожалуйста нажмите на одну из кнопок.")
        return RESULTS_FLOW


async def export_tg_format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатия «format_pdf|format_docx|format_txt», отправляет документ пользователю.
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    text = context.user_data.get("answer_text", "(пусто)")
    if data == "format_pdf":
        file_path = generate_file(text, "pdf")
    elif data == "format_docx":
        file_path = generate_file(text, "docx")
    elif data == "format_txt":
        file_path = generate_file(text, "txt")
    else:
        await query.message.reply_text("Пожалуйста выберите формат, нажав на кнопку.")
        return "EXPORT_TG_FORMAT"

    await query.message.reply_document(document=open(file_path, 'rb'))
    os.remove(file_path)
    await query.message.reply_text("Файл отправлен.")

    buttons = [
        [InlineKeyboardButton("Выгрузить в документ", callback_data="export_doc")],
        [InlineKeyboardButton("Главное меню", callback_data="export_main_menu")]
    ]
    markup = InlineKeyboardMarkup(buttons)
    await query.message.reply_text("Что дальше?", reply_markup=markup)

    return RESULTS_FLOW


# ===== CALLBACK ДЛЯ "Управление вопросами" (меню с кнопками) =====

async def manage_questions_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатия:
    - mng_add_q (Добавить вопрос)
    - mng_del_q (Удалить вопрос)
    - mng_list_q (Список вопросов)
    - mng_go_main (Главное меню)
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    from bot.handlers import manage_questions_menu  # чтобы вызвать при необходимости

    if data == "mng_go_main":
        await query.message.reply_text("Выход в главное меню.", reply_markup=main_menu_markup())
        return ASK_ROLE

    elif data == "mng_add_q":
        # Выбор типа вопроса
        buttons = [
            [InlineKeyboardButton("Да/Нет", callback_data="type_yes_no"),
            InlineKeyboardButton("Оценка(диапазон)", callback_data="type_numeric"),
            InlineKeyboardButton("Открытый вопрос", callback_data="type_open_text")],
            [InlineKeyboardButton("Назад", callback_data="mng_menu_back")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text("Выберите тип вопроса", reply_markup=markup)
        return "CHOOSE_QUESTION_TYPE"

    elif data == "mng_del_q":
        # Показать список + «Введите номер вопроса»
        session = SessionLocal()
        code = context.user_data["temp_company_code_for_questions"]
        comp = session.query(Company).filter_by(company_code=code).first()
        if not comp:
            await query.message.reply_text("Компания не найдена.")
            session.close()
            return "MANAGE_QUESTIONS_MENU"
        qs = session.query(Question).filter_by(company_id=comp.id).all()
        session.close()
        if not qs:
            await query.message.reply_text("Вопросов нет.", )
            # Возвращаем в меню
            return await manage_questions_menu(update, context)
        else:
            out = []
            for i, q in enumerate(qs, start=1):
                out.append(f"{i}. {q.question_text}")
            text_list = "\n".join(out)
            await query.message.reply_text("Список вопросов:\n" + text_list
                                          + "\n\nВведите номер вопроса, который хотите удалить:",
                                          reply_markup=ReplyKeyboardMarkup(
                                              [["Назад"]], resize_keyboard=True
                                          ))
            return "DELETE_QUESTION"

    elif data == "mng_list_q":
        # Список вопросов -> вернёмся к manage menu
        session = SessionLocal()
        code = context.user_data["temp_company_code_for_questions"]
        comp = session.query(Company).filter_by(company_code=code).first()

        if not comp:
            await query.message.reply_text("Компания не найдена.")
            session.close()
            return await manage_questions_menu(update, context)

        qs = session.query(Question).filter_by(company_id=comp.id).all()
        session.close()

        if not qs:
            await query.message.reply_text("Вопросов нет.")
        else:
            out = []
            for i, q in enumerate(qs, start=1):
                out.append(f"{i}. {q.question_text}")
            text_list = "\n".join(out)
            await query.message.reply_text(text_list)
        return await manage_questions_menu(update, context)

    else:
        await query.message.reply_text("Неизвестное действие. Пожалуйста, нажмите на кнопку.")
        return "MANAGE_QUESTIONS_MENU"


# CALLBACK ДЛЯ выбора типа вопроса (Добавление вопроса)
async def choose_question_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Этот колбэк вызывается, когда пользователь нажал кнопку
    "Да/Нет" (type_yes_no), "Оценка(диапазон)" (type_numeric),
    "Открытый вопрос" (type_open_text) или "Назад" (type_back).
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "type_yes_no":
        # Пользователь выбрал "Да/Нет"
        context.user_data["new_question_type"] = "yes_no"

        # buttons = [[
        #     InlineKeyboardButton("Назад", callback_data="type_back")
        # ]]
        # markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_text(
            "Выбран тип: «Да/Нет».\nВведите текст вопроса"
            " или «Назад»:",
            # reply_markup=InlineKeyboardMarkup([
            #     [InlineKeyboardButton("Назад", callback_data="type_back")]
            # ])
        )
        return ADD_QUESTIONS_TEXT

    elif data == "type_numeric":
        # Пользователь выбрал "Оценка(диапазон)"
        context.user_data["new_question_type"] = "numeric"

        # buttons = [[
        #     InlineKeyboardButton("Назад", callback_data="type_back")
        # ]]
        # markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_text(
            "Выбран тип: «Оценка(диапазон)».\nВведите минимальное значение"
            " или «Назад»:",
            # reply_markup=markup
        )
        return "ASK_NUMERIC_MIN"

    elif data == "type_open_text":
        # Пользователь выбрал "Открытый вопрос"
        context.user_data["new_question_type"] = "open_text"

        # buttons = [[
        #     InlineKeyboardButton("Назад", callback_data="type_back")
        # ]]
        # markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_text(
            "Выбран тип: «Открытый вопрос».\nУкажите максимальную длину (0 или "
            "«нет», чтобы было без ограничений) или «Назад»:",
            # reply_markup=markup
        )
        return "ASK_OPEN_TEXT_LENGTH"

    elif data == "type_back":
        buttons = [
            [
                InlineKeyboardButton("Да/Нет", callback_data="type_yes_no"),
                InlineKeyboardButton("Оценка(диапазон)", callback_data="type_numeric"),
                InlineKeyboardButton("Открытый вопрос", callback_data="type_open_text")
            ],
            [
                # Предположим, эта "Назад" уходит ещё выше — в меню "Управление вопросами"
                InlineKeyboardButton("Назад", callback_data="mng_menu_back")
            ]
        ]
        markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_text("Вы вернулись к выбору типа вопроса:", reply_markup=markup)
        return "CHOOSE_QUESTION_TYPE"

    elif data == "mng_menu_back":
        return await manage_questions_menu(update, context)

    else:
        await query.message.reply_text("Неизвестный тип вопроса, пожалуйста нажмите кнопку.")
        return "CHOOSE_QUESTION_TYPE"


async def handle_wrong_text_in_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если user вводит текст там, где нужно callback"""
    await update.message.reply_text("Пожалуйста, нажмите одну из кнопок, а не вводите текст.")

