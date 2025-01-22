(
    ASK_ROLE,               # Меню выбора: "Ответить на вопросы" / "Результаты" / "Добавить вопросы"
    ASK_COMPANY,            # Ввод company_code (для "Ответить на вопросы")
    ANSWERS_FLOW,           # Цепочка вопросов-ответов
    RESULTS_FLOW,           # Ввод company_code -> ввод access code -> анализ
    ACCESS_FLOW,            # "Добавить вопросы" -> ввод company_code -> ввод access code
    ADD_QUESTIONS_FLOW,     # Добавление вопроса
    ADD_QUESTIONS_COMPANY,  # Ввод company_code для добавления вопросов
    ADD_QUESTIONS_ACCESS,   # Проверка кода доступа для добавления вопросов
    ADD_QUESTIONS_TEXT,     # Ввод текста нового вопроса
    RESULTS_COMPANY,        # Ввод company_code для анализа
    RESULTS_ACCESS,         # Ввод access_code для анализа
) = range(11)

MANAGE_QUESTIONS_MENU = "MANAGE_QUESTIONS_MENU"
CHOOSE_QUESTION_TYPE = "CHOOSE_QUESTION_TYPE"
ASK_NUMERIC_MIN = "ASK_NUMERIC_MIN"
ASK_NUMERIC_MAX = "ASK_NUMERIC_MAX"
ASK_OPEN_TEXT_LENGTH = "ASK_OPEN_TEXT_LENGTH"
DELETE_QUESTION = "DELETE_QUESTION"