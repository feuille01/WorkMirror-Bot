import requests
import json
from config import (
    YANDEX_OAUTH_TOKEN,
    YANDEX_GPT_API_ENDPOINT,
    YANDEX_FOLDER_ID,
)


def get_iam_token():
    """
    Получаем IAM-токен на основе OAuth-токена.
    """
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'yandexPassportOauthToken': YANDEX_OAUTH_TOKEN}
    )
    response.raise_for_status()
    return response.json()['iamToken']


def request_yandex_gpt(user_text: str) -> dict:
    # Получение iamToken
    iam_token = get_iam_token()

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt",
        "completionOptions": {
            "temperature": 0.8,
            "maxTokens": 1000
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты помощник, который анализирует отзывы сотрудников."
            },
            {
                "role": "user",
                "text": user_text
            }
        ]
    }

    try:
        response = requests.post(
            YANDEX_GPT_API_ENDPOINT,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        return result
    except requests.RequestException as e:
        print(f"[ERROR] request_yandex_gpt: {e}")
        return {}
