import google.generativeai as genai
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, InlineQueryHandler, filters, ContextTypes

# Конфигурация API ключей (ЗАМЕНИТЕ НА СВОИ ИЛИ ИСПОЛЬЗУЙТЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ)
TELEGRAM_TOKEN = "7768573149:AAGz39ynjIe51BqsQ313yqZ8rIswmeu2DCw"
GEMINI_API_KEY = "AIzaSyATgxkicZ7--4_udTHPzJjkeRM6u0PP3AA"
MAX_MESSAGE_LENGTH = 4096

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

async def split_text(text: str, max_len: int) -> list:
    """Разбивает текст на части по max_len символов"""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

async def send_long_message(update: Update, text: str):
    """Отправляет длинные сообщения частями"""
    chunks = await split_text(text, MAX_MESSAGE_LENGTH)
    for chunk in chunks:
        await update.message.reply_text(chunk)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет {user.first_name}! Я бот с искусственным интеллектом Gemini.\n"
        "Задайте мне любой вопрос, и я постараюсь на него ответить!\n\n"
        "Также вы можете использовать меня в инлайн-режиме в любом чате, "
        "написав @{context.bot.username} и ваш вопрос."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        user_message = update.message.text
        
        # Получаем ответ от Gemini
        response = model.generate_content(user_message)
        
        # Проверяем наличие текста в ответе
        if not response.text:
            raise ValueError("Пустой ответ от API")
            
        # Отправляем ответ
        if len(response.text) > MAX_MESSAGE_LENGTH:
            await send_long_message(update, response.text)
        else:
            await update.message.reply_text(response.text)
        
    except Exception as e:
        error_message = f"⚠️ Ошибка: {str(e)}"
        print(error_message)
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик инлайн-запросов"""
    query = update.inline_query.query
    if not query:
        # Показываем подсказку при пустом запросе
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id="help",
                title="Как использовать?",
                input_message_content=InputTextMessageContent(
                    "Введите ваш вопрос после @username_бота\n"
                    "Пример: @MyGeminiBot Как работает ИИ?"
                ),
                description="Начните вводить вопрос после @имя_бота"
            )
        ])
        return
    
    try:
        # Получаем ответ от Gemini
        response = model.generate_content(query)
        content = response.text[:500]  # Обрезаем для превью
        
        results = [
            InlineQueryResultArticle(
                id=str(update.inline_query.id),
                title=f"Ответ на: {query[:30]}...",
                input_message_content=InputTextMessageContent(
                    f"🔍 Запрос: {query}\n\n"
                    f"💡 Ответ:\n{response.text}"
                ),
                description=content[:100],
                thumb_url="https://i.ibb.co/7QF7kYh/gemini-icon.png"
            )
        ]
        
        await update.inline_query.answer(results, cache_time=10)
        
    except Exception as e:
        error_result = [
            InlineQueryResultArticle(
                id="error",
                title="Ошибка",
                input_message_content=InputTextMessageContent(
                    f"⚠️ Ошибка обработки запроса: {str(e)}"
                ),
                thumb_url="https://i.ibb.co/7W2c4sT/error-icon.png"
            )
        ]
        await update.inline_query.answer(error_result)

def main():
    """Запуск бота с инлайн-режимом"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(InlineQueryHandler(inline_query))  # Инлайн-обработчик
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()