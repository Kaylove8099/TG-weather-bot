import asyncio
import aiohttp
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WeatherBot:
    def __init__(self, telegram_token, weather_api_key):
        self.telegram_token = "7003186818:AAHIBpTUJHrMlH0SoipdjcUlu0r4mP9VzII"
        self.weather_api_key = "a30600483ff6fbebd538c55e2e614a48"
        self.weather_base_url = "http://api.openweathermap.org/data/2.5/weather"
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        welcome_message = (
            "🌤️ Welcome to Weather Bot! 🌤️\n\n"
            "I can help you get weather information for any city.\n\n"
            "Commands:\n"
            "/start - Show this welcome message\n"
            "/help - Show help information\n"
            "/weather <city> - Get weather for a specific city\n\n"
            "You can also just send me a city name and I'll get the weather for you!"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = (
            "🆘 Help - Weather Bot\n\n"
            "How to use:\n"
            "• Send /weather followed by city name\n"
            "• Example: /weather London\n"
            "• Or just send: London\n\n"
            "I'll provide:\n"
            "• Current temperature\n"
            "• Weather description\n"
            "• Humidity and pressure\n"
            "• Wind speed\n"
            "• Feels like temperature"
        )
        await update.message.reply_text(help_text)

    async def get_weather_data(self, city_name):
        """Fetch weather data from OpenWeatherMap API."""
        params = {
            'q': city_name,
            'appid': self.weather_api_key,
            'units': 'metric'  # For Celsius
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.weather_base_url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        raise Exception(f"API request failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            raise

    def format_weather_message(self, weather_data):
        """Format weather data into a readable message."""
        city = weather_data['name']
        country = weather_data['sys']['country']
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        pressure = weather_data['main']['pressure']
        description = weather_data['weather'][0]['description'].title()
        wind_speed = weather_data['main'].get('wind', {}).get('speed', 'N/A')
        
        # Weather emoji based on weather condition
        weather_id = weather_data['weather'][0]['id']
        emoji = self.get_weather_emoji(weather_id)
        
        message = (
            f"{emoji} Weather in {city}, {country}\n\n"
            f"🌡️ Temperature: {temp}°C\n"
            f"🤔 Feels like: {feels_like}°C\n"
            f"📝 Description: {description}\n"
            f"💧 Humidity: {humidity}%\n"
            f"📊 Pressure: {pressure} hPa\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )
        
        return message

    def get_weather_emoji(self, weather_id):
        """Return appropriate emoji based on weather condition ID."""
        if weather_id < 300:
            return "⛈️"  # Thunderstorm
        elif weather_id < 400:
            return "🌦️"  # Drizzle
        elif weather_id < 600:
            return "🌧️"  # Rain
        elif weather_id < 700:
            return "❄️"  # Snow
        elif weather_id < 800:
            return "🌫️"  # Atmosphere (fog, etc.)
        elif weather_id == 800:
            return "☀️"  # Clear sky
        else:
            return "☁️"  # Clouds

    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /weather command."""
        if not context.args:
            await update.message.reply_text(
                "Please provide a city name!\n"
                "Example: /weather London"
            )
            return

        city_name = ' '.join(context.args)
        await self.get_weather(update, city_name)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages as city names."""
        city_name = update.message.text.strip()
        
        # Ignore if message starts with '/' (it's a command)
        if city_name.startswith('/'):
            await update.message.reply_text(
                "Unknown command. Type /help for available commands."
            )
            return
            
        await self.get_weather(update, city_name)

    async def get_weather(self, update: Update, city_name: str):
        """Get weather information for a city."""
        # Send "typing" action
        await update.message.reply_chat_action(action="typing")
        
        try:
            weather_data = await self.get_weather_data(city_name)
            
            if weather_data is None:
                await update.message.reply_text(
                    f"❌ Sorry, I couldn't find weather information for '{city_name}'.\n"
                    "Please check the city name and try again."
                )
                return
            
            weather_message = self.format_weather_message(weather_data)
            await update.message.reply_text(weather_message)
            
        except Exception as e:
            logger.error(f"Error getting weather for {city_name}: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error getting the weather information. "
                "Please try again later."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Start the bot."""
        # Create the Application
        application = Application.builder().token(self.telegram_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("weather", self.weather_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add error handler
        application.add_error_handler(self.error_handler)

        # Start the bot
        print("🤖 Weather Bot is starting...")
        print("Press Ctrl+C to stop the bot")
        
        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution
if __name__ == '__main__':
    # Replace these with your actual tokens
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY_HERE"
    
    # Create and run the bot
    bot = WeatherBot(TELEGRAM_BOT_TOKEN, WEATHER_API_KEY)
    bot.run()
