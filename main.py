from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler, MessageHandler, Filters
import requests

BOT_API_KEY = "6935659962:AAGsWQbafh1lPYc2mBl7lqIqixL6PZrRabs"  
OMDB_API_KEY = "5081408a"

user_watchlists = {}

def start(update: Update, context):
    message = "👋 به بات فیلم و سریال IMDB خوش آمدید!\n\n میتونی از منو به ابزار های بات دسترسی پیدا کنی !."
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 جستوجوی فیلم و سریال 🎬", switch_inline_query_current_chat="")],
        ]
    )
    update.message.reply_text(message, reply_markup=keyboard)

def restart(update: Update, context):
    message = "🔄 برای شروع مجدد دستور /start رو دوباره ارسال کن."
    update.message.reply_text(message)

def tools(update: Update, context):
    message = "🔎 یکی از ابزار ها رو انتخاب کن:"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 جستوجوی فیلم و سریال 🎬", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("📋 فیلم های جستجو شده 📋", callback_data="view_watchlist")],
        ]
    )
    update.message.reply_text(message, reply_markup=keyboard)


def handle_callback_query(update: Update, context):
    query = update.callback_query
    data = query.data
    
    if data == "view_watchlist":
        user_id = query.from_user.id

        if user_id not in user_watchlists or not user_watchlists[user_id]:
            query.message.reply_text("🚫 فیلمی به لیست تماشا اضافه نکردی!")
        else:
            keyboard = [
                [
                    InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"movie_in_watchlist:{movie_id}:{title}"),
                    InlineKeyboardButton("🗑️ حذف از لیست تماشا", callback_data=f"delete_from_watchlist:{movie_id}")
                ]
                for i, (movie_id, title) in enumerate(user_watchlists[user_id].items())
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text("👁️ لیست تماشا شما:", reply_markup=reply_markup)
    
    elif data.startswith("delete_from_watchlist:"):
        _, movie_id = data.split(":", 1)
        user_id = query.from_user.id

        if user_id in user_watchlists and movie_id in user_watchlists[user_id]:
            del user_watchlists[user_id][movie_id]
            query.answer("✅ فیلم از لیست تماشا شما حذف شد!")
            query.data = "view_watchlist"
            handle_callback_query(update, context)
        else:
            query.answer("ℹ️ فیلم در لیست تماشا شما پیدا نشد.")
            
    elif data.startswith("movie_in_watchlist:"):
        _, movie_id, title = data.split(":", 2)
        query.answer(f"ℹ️ {title} در لیست تماشا شماست!")
    
    elif data.startswith("add_to_watchlist:"):
        _, movie_id, movie_title = data.split(":", 2)
        user_id = query.from_user.id

        if user_id not in user_watchlists:
            user_watchlists[user_id] = {}

        if movie_id not in user_watchlists[user_id]:
            user_watchlists[user_id][movie_id] = movie_title
            query.answer("✅ فیلم به لیست تماشا شما اضافه شد!")
        else:
            query.answer("ℹ️ فیلم قبلا به لیست تماشا اضافه شده.")


def inline_search_movies(update: Update, context):
    query = update.inline_query.query
    query = query.replace(" ", "+")
    url = f"https://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()

    results = []
    if response["Response"] == "True":
        for movie in response["Search"]:
            results.append(
                InlineQueryResultArticle(
                    id=movie["imdbID"],
                    title=f'{movie["Title"]} {movie["Year"]}',
                    description=f'{movie["Type"]}',
                    thumb_url=movie["Poster"],
                    input_message_content=InputTextMessageContent(movie["imdbID"]),
                )
            )

        update.inline_query.answer(results)


def display_movie_details(update: Update, context):
    movie_id = update.message.text
    message_id = update.message.message_id
    chat_id = update.message.chat_id
    
    url = f"https://www.omdbapi.com/?i={movie_id}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()
    
    details = (
        f"🎬 *Title:* {response['Title']} {response['Year']}\n\n"
        f"⭐ *Rating:* {response['imdbRating']}/10 ({response['imdbVotes']} votes)\n"
        f"🚸 *Rated:* {response['Rated']}"
        f"📅 *Release Date:* {response['Released']}\n"
        f"🌐 *Languages:* {response['Language']}\n"
        f"🌍 *Countries:* {response['Country']}\n\n"
        f"⌛ *Duration:* {response['Runtime']}\n"
        f"🎭 *Genres:* {response['Genre']}\n\n"
        f"🌟 *Stars:* {response['Actors']}\n"
        f"🎥 *Directors:* {response['Director']}\n"
        f"✍ *Writers:* {response['Writer']}\n"
        f"🏆 *Awards:* {response['Awards']}\n\n"
        f"📖 *Story Line:*\n ||{response['Plot']}||\n"
    )

    short_title = response['Title'][:30] + '...' if len(response['Title']) > 30 else response['Title']

    keyboard = [
        [
            InlineKeyboardButton("➕ به لیست تماشام اضافه کن ➕", callback_data=f"add_to_watchlist:{movie_id}:{short_title}"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_photo(photo=response["Poster"], caption=details, reply_markup=reply_markup, parse_mode="Markdown")
    
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def main():
    updater = Updater(BOT_API_KEY)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("tools", tools))
    dispatcher.add_handler(CommandHandler("restart", restart))
    
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
    
    dispatcher.add_handler(InlineQueryHandler(inline_search_movies))
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, display_movie_details))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()