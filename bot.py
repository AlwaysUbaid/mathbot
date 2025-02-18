import os
import logging
import random
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
TOKEN = os.getenv('BOT_TOKEN', '8135003383:AAFF2glf_nRnqnBAPt0Yg8R1EUFJSarMXpk')

# Store user states
user_states = {}

class UserState:
    def __init__(self):
        self.current_problem = None
        self.start_time = None
        self.operation = None
        self.level = None
        self.score = 0
        self.streak = 0
        self.high_score = 0

class MathProblem:
    def __init__(self, a, b, answer, symbol):
        self.a = a
        self.b = b
        self.answer = answer
        self.symbol = symbol

def get_number_by_level(level):
    """Generate a random number based on the difficulty level"""
    ranges = {
        1: (1, 9),
        2: (10, 99),
        3: (100, 999),
        4: (1000, 9999)
    }
    min_val, max_val = ranges.get(level, (1, 9))
    return random.randint(min_val, max_val)

def generate_problem(operation, level):
    """Generate a math problem based on operation and level"""
    if operation == 'mix':
        operation = random.choice(['add', 'sub', 'mul', 'div'])
    
    if operation == 'add':
        a = get_number_by_level(level)
        b = get_number_by_level(level)
        return MathProblem(a, b, a + b, '+')
    
    elif operation == 'sub':
        a = get_number_by_level(level)
        b = get_number_by_level(level)
        if b > a:  # Ensure positive result
            a, b = b, a
        return MathProblem(a, b, a - b, '-')
    
    elif operation == 'mul':
        if level > 2:  # Limit multiplication difficulty
            level = 2
        a = get_number_by_level(level)
        b = get_number_by_level(1)  # Second number always single digit for higher levels
        return MathProblem(a, b, a * b, '×')
    
    else:  # division
        if level > 2:  # Limit division difficulty
            level = 2
        b = get_number_by_level(1)  # Divisor is always single digit
        a = b * get_number_by_level(level)  # Ensure clean division
        return MathProblem(a, b, a // b, '÷')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot and show operation selection"""
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
    
    welcome_text = (
        "🧮 Welcome to Math Practice Bot! 🧮\n\n"
        "Train your math skills with:\n"
        "• Different operations\n"
        "• Multiple difficulty levels\n"
        "• Time tracking\n"
        "• Score keeping\n\n"
        "Choose an operation to begin:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    if user_id in user_states:
        state = user_states[user_id]
        stats_text = (
            f"📊 Your Statistics 📊\n\n"
            f"Current Score: {state.score}\n"
            f"Current Streak: {state.streak}\n"
            f"High Score: {state.high_score}\n"
        )
        await update.message.reply_text(stats_text)
    else:
        await update.message.reply_text("No statistics available yet. Start playing with /start")

async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show level selection buttons"""
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
    
    level_text = (
        "Choose difficulty level:\n\n"
        "🟢 Level 1: Single digit numbers\n"
        "🟡 Level 2: Two digit numbers\n"
        "🟠 Level 3: Three digit numbers\n"
        "🔴 Level 4: Four digit numbers"
    )
    
    await update.callback_query.edit_message_text(level_text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data.startswith('level_'):
        level = int(query.data.split('_')[1])
        if user_id not in user_states:
            user_states[user_id] = UserState()
        user_states[user_id].level = level
        
        problem = generate_problem(user_states[user_id].operation, level)
        user_states[user_id].current_problem = problem.answer
        user_states[user_id].start_time = time.time()
        
        await query.edit_message_text(f"What is {problem.a} {problem.symbol} {problem.b}?")
    else:
        user_states[user_id] = UserState()
        user_states[user_id].operation = query.data
        user_states[user_id].score = 0
        user_states[user_id].streak = 0
        await select_level(update, context)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user answers"""
    user_id = update.effective_user.id
    if user_id not in user_states or user_states[user_id].current_problem is None:
        await update.message.reply_text("Please start a new game with /start")
        return

    try:
        user_answer = int(update.message.text)
        elapsed_time = time.time() - user_states[user_id].start_time
        state = user_states[user_id]
        
        if user_answer == state.current_problem:
            state.score += 1
            state.streak += 1
            state.high_score = max(state.score, state.high_score)
            
            feedback = (
                f"✅ Correct!\n"
                f"⏱️ Time: {elapsed_time:.2f} seconds\n"
                f"📈 Score: {state.score}\n"
                f"🔥 Streak: {state.streak}"
            )
            await update.message.reply_text(feedback)
        else:
            state.streak = 0
            feedback = (
                f"❌ Incorrect\n"
                f"✨ Correct answer: {state.current_problem}\n"
                f"⏱️ Time: {elapsed_time:.2f} seconds\n"
                f"📈 Score: {state.score}"
            )
            await update.message.reply_text(feedback)
        
        # Generate new problem
        problem = generate_problem(state.operation, state.level)
        state.current_problem = problem.answer
        state.start_time = time.time()
        
        await update.message.reply_text(f"Next problem: What is {problem.a} {problem.symbol} {problem.b}?")
        
    except ValueError:
        await update.message.reply_text("Please enter a valid number!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "🎮 How to play:\n\n"
        "1. Use /start to begin a new game\n"
        "2. Choose an operation (+, -, ×, ÷ or mixed)\n"
        "3. Select difficulty level (1-4 digits)\n"
        "4. Solve the problems as quickly as you can!\n\n"
        "📝 Commands:\n"
        "/start - Start new game\n"
        "/stats - View your statistics\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    # Get port and webhook URL from environment variables
    port = int(os.getenv('PORT', 8080))
    webhook_url = os.getenv('WEBHOOK_URL', 'https://your-app-name.onrender.com')

    # Start the bot in webhook mode
    application.run_webhook(
        listen='0.0.0.0',
        port=port,
        webhook_url=webhook_url,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
