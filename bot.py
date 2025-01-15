import re
import telegram
import logging
import json
import os
import time
import requests
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from cryptotracker import get_prices
from reminder import isValid, seconds
from fortunes import FORTUNES
import PyPDF2
import docx
import io

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = 'bot_data.json'
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not WEATHER_API_KEY:
    logger.error("WEATHER_API_KEY environment variable is not set!")
    WEATHER_API_KEY = None

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN must be set!")

def save_data():
    """Save the data dictionary to a JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    """Load the data dictionary from JSON file"""
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

# Initialize empty data dictionary
data = {}

def prices(update, context):
    chat_id = update.effective_chat.id
    message = ""

    crypto_data = get_prices()
    for i in crypto_data:
        coin = crypto_data[i]["coin"]
        price = crypto_data[i]["price"]
        change_day = crypto_data[i]["change_day"]
        change_hour = crypto_data[i]["change_hour"]
        message += f"Coin: {coin}\nPrice: ${price:,.2f}\nHour Change: {change_hour:.3f}%\nDay Change: {change_day:.3f}%\n\n"

    context.bot.send_message(chat_id=chat_id, text=message)

def thanks(update, context):
    chat_id = update.effective_chat.id
    message = "You're welcome!"
    context.bot.send_message(chat_id=chat_id, text=message)

def remindme(update, context):
    try:
        user_input = update.message.text
        userid = update.message.from_user
        
        # Check if this is a reply to another message
        reply_to_message = update.message.reply_to_message
        if reply_to_message:
            # If it's a reply, include original sender's username in the message
            original_sender = reply_to_message.from_user.username
            cache_message = f"Message from @{original_sender}: {reply_to_message.text}"
            # Remove the message part from validation since we're using the replied message
            time_input = user_input.split()[1:]
        else:
            # Original behavior for non-reply messages
            time_input = user_input.split()
            cache_message = re.split(' ', user_input, maxsplit=2)[-1]
        
        if isValid(time_input):
            time_set = time_input[:1]
            print(time_set)
            time_in_seconds = seconds(time_set)
            print(time_in_seconds)
            username = (userid["username"])
            userto = f"@{username} - "
            scheduled_time = time.time() + time_in_seconds
            
            # Store both message and scheduled time
            reminder_id = str(int(time.time()))  # Use timestamp as unique ID
            data[reminder_id] = {
                "message": userto + cache_message,
                "scheduled_time": scheduled_time,
                "chat_id": update.effective_chat.id
            }
            
            context.job_queue.run_once(call_back_time, time_in_seconds, context=reminder_id)
            save_data()  # Save data after updating
            context.bot.send_message(chat_id=update.effective_chat.id, text = f"{userto}Reminder set successfully!")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Not a valid time!")
    except (IndexError, ValueError):
        update.message.reply_text("Use /remindme to set when you want to be reminded" +
                                  " in this format: 5w 2d 3h 20m 3s\n" +
                                  "You can either:\n" +
                                  "1. Reply to any message with '/remindme 30m'\n" +
                                  "2. Send '/remindme 30m your message here'")

def call_back_time(context: telegram.ext.CallbackContext):
    reminder_id = context.job.context
    if reminder_id in data:
        reminder = data[reminder_id]
        context.bot.send_message(chat_id=reminder["chat_id"], text=reminder["message"])
        # Clean up completed reminder
        del data[reminder_id]
        save_data()

def restore_reminders(dispatcher):
    """Restore pending reminders from saved data"""
    current_time = time.time()
    to_delete = []
    
    for reminder_id, reminder in data.items():
        remaining_time = reminder["scheduled_time"] - current_time
        if remaining_time > 0:
            dispatcher.job_queue.run_once(
                call_back_time,
                remaining_time,
                context=reminder_id
            )
        else:
            # Mark expired reminders for deletion
            to_delete.append(reminder_id)
    
    # Clean up expired reminders
    for reminder_id in to_delete:
        del data[reminder_id]
    if to_delete:
        save_data()

def weather(update, context):
    try:
        if not WEATHER_API_KEY:
            update.message.reply_text("Weather functionality is not available - API key not configured.")
            return

        if len(context.args) < 1:
            update.message.reply_text("Please provide a zip code. Usage: /weather 12345")
            return

        zip_code = context.args[0]
        
        # Get current weather data
        url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={WEATHER_API_KEY}&units=imperial"
        response = requests.get(url)
        
        if response.status_code != 200:
            update.message.reply_text("Error fetching weather data. Please check the zip code and try again.")
            return
            
        data = response.json()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        city = data['name']
        
        # Format current conditions
        message = f"Weather in {city}:\n\n"
        message += f"🌡️ Temperature: {temp:.1f}°F\n"
        message += f"🌡️ Feels like: {feels_like:.1f}°F\n"
        message += f"💧 Humidity: {humidity}%\n"
        message += f"☁️ Conditions: {description.capitalize()}"
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in weather command: {str(e)}")
        update.message.reply_text("Sorry, there was an error getting the weather data. Please try again later.")

def forecast(update, context):
    try:
        if len(context.args) < 1:
            update.message.reply_text("Please provide a zip code. Usage: /forecast 12345")
            return

        zip_code = context.args[0]
        
        # Use the 5-day forecast API instead of One Call API
        url = f"http://api.openweathermap.org/data/2.5/forecast?zip={zip_code},us&appid={WEATHER_API_KEY}&units=imperial"
        response = requests.get(url)
        
        if response.status_code != 200:
            update.message.reply_text("Error fetching weather data. Please check the zip code and try again.")
            return
            
        data = response.json()
        city = data['city']['name']
        
        # Get one forecast per day (every 24 hours, up to 3 days)
        forecasts = {}
        for item in data['list']:
            # Convert timestamp to date
            date = time.strftime("%A", time.localtime(item['dt']))
            
            # Only take the first forecast for each day
            if date not in forecasts and len(forecasts) < 3:
                forecasts[date] = {
                    'temp_max': item['main']['temp_max'],
                    'temp_min': item['main']['temp_min'],
                    'description': item['weather'][0]['description'],
                    'pop': item['pop'] * 100  # Probability of precipitation
                }
        
        # Format 3-day forecast
        message = f"3-Day Forecast for {city}:\n"
        for date, forecast in forecasts.items():
            message += f"\n{date}:\n"
            message += f"🌡️ High: {forecast['temp_max']:.1f}°F, Low: {forecast['temp_min']:.1f}°F\n"
            message += f"☁️ {forecast['description'].capitalize()}\n"
            message += f"🌧️ Chance of rain: {forecast['pop']:.0f}%\n"
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in forecast command: {str(e)}")
        update.message.reply_text("Sorry, there was an error getting the forecast data. Please try again later.")

def fortune(update, context):
    """Send a random fortune cookie message"""
    chosen_fortune = random.choice(FORTUNES)
    message = f"Your fortune:\n\n{chosen_fortune}"
    update.message.reply_text(message)

def handle_file(update, context):
    """Handle received files"""
    file = update.message.document
    if file:
        file_name = file.file_name
        file_size = file.file_size
        file_id = file.file_id
        
        # You can download the file using:
        # file_path = context.bot.get_file(file_id).download()
        
        message = f"📄 Received file: {file_name}\n"
        message += f"Size: {file_size/1024:.1f} KB\n"
        message += f"File ID: {file_id}"
        
        update.message.reply_text(message)

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def calculate_ats_score(text):
    """Calculate ATS score based on various factors"""
    score = 0
    max_score = 100
    
    # Common keywords that ATS systems look for
    keywords = [
        "experience", "skills", "education", "project", "achievement",
        "leadership", "team", "manage", "develop", "create",
        "improve", "increase", "decrease", "analyze", "implement",
        "responsible", "coordinate", "strategic", "planning", "organize"
    ]
    
    # Check for presence of key sections
    sections = ["experience", "education", "skills", "summary", "objective"]
    for section in sections:
        if section.lower() in text.lower():
            score += 10
    
    # Check for keywords
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
    score += min(keyword_count * 2, 30)  # Up to 30 points for keywords
    
    # Check for contact information
    if re.search(r'[\w\.-]+@[\w\.-]+', text):  # Email
        score += 10
    if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):  # Phone
        score += 10
    
    # Ensure score doesn't exceed 100
    return min(score, max_score)

def resume(update, context):
    """Handle resume analysis command"""
    try:
        # Check if this is a file message with /resume in caption
        if update.message.document and update.message.caption and update.message.caption.startswith('/resume'):
            file = update.message.document
        # Check if this is a /resume command with attached file
        elif update.message.document:
            file = update.message.document
        else:
            update.message.reply_text("Please send a resume file (PDF or DOCX) with the /resume command.")
            return

        file_name = file.file_name.lower()
        
        # Log file details for debugging
        logger.info(f"Received file: {file_name}, Size: {file.file_size} bytes")
        
        # Check file type
        if not (file_name.endswith('.pdf') or file_name.endswith('.docx')):
            update.message.reply_text("Please send only PDF or DOCX files.")
            return
        
        # Send acknowledgment
        update.message.reply_text(f"Processing resume: {file_name}...")
            
        # Download the file
        try:
            file_bytes = context.bot.get_file(file.file_id).download_as_bytearray()
            logger.info(f"Successfully downloaded file: {file_name}")
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise
        
        # Extract text based on file type
        try:
            if file_name.endswith('.pdf'):
                text = extract_text_from_pdf(file_bytes)
                logger.info("Successfully extracted text from PDF")
            else:
                text = extract_text_from_docx(file_bytes)
                logger.info("Successfully extracted text from DOCX")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise
            
        # Calculate ATS score
        try:
            score = calculate_ats_score(text)
            logger.info(f"Calculated ATS score: {score}")
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            raise
        
        # Prepare detailed feedback
        message = f"📄 Resume Analysis for: {file_name}\n\n"
        message += f"ATS Score: {score}/100\n\n"
        
        # Add section-specific feedback
        sections_found = []
        sections_missing = []
        for section in ["experience", "education", "skills", "summary", "objective"]:
            if section.lower() in text.lower():
                sections_found.append(section.capitalize())
            else:
                sections_missing.append(section.capitalize())
        
        message += "✅ Found Sections:\n"
        message += "• " + "\n• ".join(sections_found) + "\n\n"
        
        if sections_missing:
            message += "❌ Missing Sections:\n"
            message += "• " + "\n• ".join(sections_missing) + "\n\n"
        
        if score >= 80:
            message += "🌟 Excellent ATS optimization!"
        elif score >= 60:
            message += "👍 Good ATS score, but room for improvement."
        else:
            message += "⚠️ Consider optimizing your resume for ATS systems."
            
        update.message.reply_text(message)
        logger.info("Successfully sent analysis response")
        
    except Exception as e:
        logger.error(f"Error in resume command: {str(e)}")
        update.message.reply_text("Sorry, there was an error analyzing the resume. Please try again later.")

def info(update, context):
    """Provide information about available commands"""
    message = "🤖 *Available Commands:*\n\n"
    
    message += "*Cryptocurrency:*\n"
    message += "/prices - Get current prices of cryptocurrencies\n\n"
    
    message += "*Weather:*\n"
    message += "/weather <zipcode> - Get current weather conditions\n"
    message += "Example: `/weather 12345`\n"
    message += "/forecast <zipcode> - Get 3-day weather forecast\n"
    message += "Example: `/forecast 12345`\n\n"
    
    message += "*Reminders:*\n"
    message += "/remindme <time> <message> - Set a reminder\n"
    message += "Time format: weeks(w), days(d), hours(h), minutes(m), seconds(s)\n"
    message += "Examples:\n"
    message += "• `/remindme 30m check email`\n"
    message += "• `/remindme 1h30m meeting`\n"
    message += "• Reply to any message with `/remindme 2h` to be reminded about it\n\n"
    
    message += "*Resume Analysis:*\n"
    message += "/resume - Send a resume (PDF/DOCX) to get its ATS score\n\n"
    
    message += "*Files:*\n"
    message += "Send any file to the bot and it will acknowledge receipt\n\n"
    
    message += "*Fun:*\n"
    message += "/fortune - Get a fortune cookie message\n\n"
    
    message += "*Other:*\n"
    message += "/info - Show this help message\n"
    message += "/thanks - Say you're welcome!\n"
    
    update.message.reply_text(message, parse_mode='Markdown')

def main():
    # Load saved data at startup
    load_data()
    
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Restore any pending reminders
    restore_reminders(dispatcher)

    # Add command handlers first (they take precedence)
    dispatcher.add_handler(CommandHandler("prices", prices))
    dispatcher.add_handler(CommandHandler("thanks", thanks))
    dispatcher.add_handler(CommandHandler("remindme", remindme))
    dispatcher.add_handler(CommandHandler("weather", weather))
    dispatcher.add_handler(CommandHandler("forecast", forecast))
    dispatcher.add_handler(CommandHandler("fortune", fortune))
    
    # Add resume handlers
    dispatcher.add_handler(CommandHandler("resume", resume))
    dispatcher.add_handler(MessageHandler(Filters.document & Filters.caption_regex(r'^/resume'), resume))
    
    dispatcher.add_handler(CommandHandler("info", info))
    
    # Add general file handler last
    dispatcher.add_handler(MessageHandler(Filters.document & ~Filters.command & ~Filters.caption_regex(r'^/resume'), handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

