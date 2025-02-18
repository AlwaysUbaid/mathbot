from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random
import time
from datetime import datetime

# Store user states
user_states = {}

class UserState:
    def __init__(self):
        self.current_problem = None
        self.start_time = None
        self.operation = None
        self.level = None
        self.score = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Addition (+)", callback_data='add'),
            InlineKeyboardButton("Subtraction (-)", callback_data='sub')
        ],
        [
            InlineKeyboardButton("Multiplication (×)", callback_data='mul'),
            InlineKeyboardButton("Division (÷)", callback_data='div')
        ],
        [
            InlineKeyboardButton("Mixed Operations", callback_data='mix')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to Math Practice Bot!\nChoose an operation:",
        reply_markup=reply_markup
    )

def get_number_by_level(level):
    if level == 1:
        return random.randint(1, 9)
    elif level == 2:
        return random.randint(10, 99)
    elif level == 3:
        return random.randint(100, 999)
    else:
        return random.randint(1000, 9999)

def generate_problem(operation, level):
    if operation == 'mix':
        operation = random.choice(['add', 'sub', 'mul', 'div'])
    
    if operation == 'add':
        a = get_number_by_level(level)
        b = get_number_by_level(level)
        return (a, b, a + b, '+')
    elif operation == 'sub':
        a = get_number_by_level(level)
        b = get_number_by_level(level)
        if b > a:  # Ensure positive result
            a, b = b, a
        return (a, b, a - b, '-')
    elif operation == 'mul':
        if level > 2:  # Limit multiplication difficulty
            level = 2
        a = get_number_by_level(level)
        b = get_number_by_level(1)  # Second number always single digit for higher levels
        return (a, b, a * b, '×')
    else:  # division
        if level > 2:  # Limit division difficulty
            level = 2
        b = get_number_by_level(1)  # Divisor is always single digit
        a = b * get_number_by_level(level)  # Ensure clean division
        return (a, b, a // b, '÷')

async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Level 1 (1 digit)", callback_data='level_1'),
            InlineKeyboardButton("Level 2 (2 digits)", callback_data='level_2')
        ],
        [
            InlineKeyboardButton("Level 3 (3 digits)", callback_data='level_3'),
            InlineKeyboardButton("Level 4 (4 digits)", callback_data='level_4')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Choose difficulty level:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data.startswith('level_'):
        level = int(query.data.split('_')[1])
        user_states[user_id].level = level
        
        a, b, answer, symbol = generate_problem(user_states[user_id].operation, level)
        user_states[user_id].current_problem = answer
        user_states[user_id].start_time = time.time()
        
        await query.edit_message_text(f"What is {a} {symbol} {b}?")
    else:
        user_states[user_id] = UserState()
        user_states[user_id].operation = query.data
        user_states[user_id].score = 0
        await select_level(update, context)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states or user_states[user_id].current_problem is None:
        await update.message.reply_text("Please start a new game with /start")
        return

    try:
        user_answer = int(update.message.text)
        elapsed_time = time.time() - user_states[user_id].start_time
        
        if user_answer == user_states[user_id].current_problem:
            user_states[user_id].score += 1
            await update.message.reply_text(
                f"Correct! ✅\nTime: {elapsed_time:.2f} seconds\nScore: {user_states[user_id].score}"
            )
        else:
            await update.message.reply_text(
                f"Incorrect ❌\nCorrect answer: {user_states[user_id].current_problem}\n"
                f"Time: {elapsed_time:.2f} seconds\nScore: {user_states[user_id].score}"
            )
        
        # Generate new problem
        a, b, answer, symbol = generate_problem(
            user_states[user_id].operation,
            user_states[user_id].level
        )
        user_states[user_id].current_problem = answer
        user_states[user_id].start_time = time.time()
        
        await update.message.reply_text(f"Next problem: What is {a} {symbol} {b}?")
        
    except ValueError:
        await update.message.reply_text("Please enter a valid number!")

def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token from BotFather
    application = Application.builder().token('YOUR_BOT_TOKEN').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    application.run_polling()

if __name__ == '__main__':
    main()
