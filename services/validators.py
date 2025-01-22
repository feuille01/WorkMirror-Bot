import json
import bcrypt
from config import (
    YES_NO_VALID,
    DEFAULT_MAX_LENGTH
)


def check_access_code(plain_code: str, hashed_code: str) -> bool:
    return bcrypt.checkpw(plain_code.encode('utf-8'), hashed_code.encode('utf-8'))

# Помощник для load/save constraints
def save_constraints(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False)

def load_constraints(s: str) -> dict:
    if not s:
        return {}
    try:
        return json.loads(s)
    except:
        return {}

# Валидация ответа в receive_answer_and_ask_next
def validate_answer(question, answer_text: str) -> (bool, str):
    """
    Возвращает (is_valid, error_message).
    Если is_valid=False, error_message содержит причину.
    """
    q_type = question.question_type
    c_dict = load_constraints(question.constraints)

    if q_type == "yes_no":
        # только да/нет/yes/no
        if answer_text.lower() not in YES_NO_VALID:
            return False, "Пожалуйста, введите Да/Нет."
        return True, ""

    elif q_type == "numeric":
        min_val = c_dict.get("min_value", 0)
        max_val = c_dict.get("max_value", 100)
        try:
            val = int(answer_text)
        except ValueError:
            return False, "Пожалуйста, введите целое число."

        if val < min_val or val > max_val:
            return False, f"Число должно быть между {min_val} и {max_val}."
        return True, ""

    elif q_type == "open_text":
        max_len = c_dict.get("max_length", 9999)
        if len(answer_text) > max_len:
            return False, f"Ваш ответ слишком длинный, введите до {max_len} символов."
        return True, ""

    else:
        return True, ""
