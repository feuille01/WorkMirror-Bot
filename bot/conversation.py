from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# Импортируем состояния
from states import (
    ASK_ROLE,
    ASK_COMPANY,
    ANSWERS_FLOW,
    RESULTS_FLOW,
    ACCESS_FLOW,
    ADD_QUESTIONS_FLOW,
    ADD_QUESTIONS_COMPANY,
    ADD_QUESTIONS_ACCESS,
    ADD_QUESTIONS_TEXT,
    RESULTS_COMPANY,
    RESULTS_ACCESS,
    MANAGE_QUESTIONS_MENU,
    CHOOSE_QUESTION_TYPE,
    ASK_NUMERIC_MIN,
    ASK_NUMERIC_MAX,
    ASK_OPEN_TEXT_LENGTH,
    DELETE_QUESTION
)

from bot.handlers import (
    start_command,
    handle_role_choice,
    ask_company_for_answers,
    ask_next_question,
    receive_answer_and_ask_next,
    ask_company_for_results,
    check_access_and_analyze,
    ask_company_for_add_questions,
    check_access_and_add_questions,
    manage_questions_menu,
    delete_question_state,
    ask_numeric_min,
    ask_numeric_max,
    ask_open_text_length,
    receive_new_question,
)

# Импортируем callback-функции
from callbacks import (
    export_choice_callback,
    export_tg_format_callback,
    manage_questions_menu_callback,
    choose_question_type_callback,
    handle_wrong_text_in_callback
)


def create_conversation_handler():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ASK_ROLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role_choice)
            ],

            # Блок "Ответить на вопросы"
            ASK_COMPANY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_company_for_answers),
            ],
            ANSWERS_FLOW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_and_ask_next),
            ],

            # Блок "Результаты"
            RESULTS_COMPANY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_company_for_results),
            ],
            RESULTS_ACCESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_access_and_analyze),
            ],
            RESULTS_FLOW: [
                CallbackQueryHandler(export_choice_callback,
                                     pattern="^(export_doc|export_no|export_main_menu)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wrong_text_in_callback),
            ],
            "EXPORT_TG_FORMAT": [
                CallbackQueryHandler(export_tg_format_callback, pattern="^(format_pdf|format_docx|format_txt)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wrong_text_in_callback),
            ],

            # Блок "Управление вопросами"
            ADD_QUESTIONS_COMPANY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_company_for_add_questions),
            ],
            ADD_QUESTIONS_ACCESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_access_and_add_questions),
            ],
            MANAGE_QUESTIONS_MENU: [
                CallbackQueryHandler(manage_questions_menu_callback, pattern="^(mng_.*)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wrong_text_in_callback),
            ],
            DELETE_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_question_state),
            ],

            CHOOSE_QUESTION_TYPE: [
                CallbackQueryHandler(choose_question_type_callback,
                                     pattern="^(type_yes_no|type_numeric|type_open_text|type_back|mng_menu_back)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wrong_text_in_callback),
            ],

            # Добавленные состояния для numeric/open_text
            ASK_NUMERIC_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_numeric_min),
            ],
            ASK_NUMERIC_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_numeric_max),
            ],
            ASK_OPEN_TEXT_LENGTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_open_text_length),
            ],
            ADD_QUESTIONS_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_question),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        allow_reentry=True,
    )

    return conv_handler