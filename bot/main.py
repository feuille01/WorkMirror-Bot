from telegram.ext import ApplicationBuilder, PicklePersistence
from config import TELEGRAM_BOT_TOKEN
from conversation import create_conversation_handler

def main():

    persistence = PicklePersistence(filepath="bot_data.pkl")
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()