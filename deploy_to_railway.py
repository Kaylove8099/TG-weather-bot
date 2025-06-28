import os

def create_requirements_txt():
    """Create requirements.txt file."""
    requirements_content = """python-telegram-bot==20.7
aiohttp==3.9.1
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    print("✅ Created requirements.txt")

def create_procfile():
    """Create Procfile for Railway."""
    procfile_content = "web: python weather_bot_cloud.py"
    
    with open('Procfile', 'w') as f:
        f.write(procfile_content)
    print("✅ Created Procfile")

def create_railway_json():
    """Create railway.json configuration."""
    railway_config = """{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python weather_bot_cloud.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}"""
    
    with open('railway.json', 'w') as f:
        f.write(railway_config)
    print("✅ Created railway.json")

def create_cloud_ready_bot():
    """Create cloud-ready version of the bot."""
    
    bot_code = '''import asyncio
import aiohttp
import logging
import os
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
        self.telegram_token = telegram_token
        self.weather_api_key = weather_api_key
        self.weather_base_url = "http://api.openweathermap.org/data/2.5/weather"
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        welcome_message = (
            "🌤️ Welcome to Weather Bot! 🌤️\\n\\n"
            "I can help you get weather information for any city.\\n\\n"
            "Commands:\\n"
            "/start - Show this welcome message\\n"
            "/help - Show help information\\n"
            "/weather <city> - Get weather for a specific city\\n\\n"
            "You can also just send me a city name and I'll get the weather for you!"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = (
            "🆘 Help - Weather Bot\\n\\n"
            "How to use:\\n"
            "• Send /weather followed by city name\\n"
            "• Example: /weather London\\n"
            "• Or just send: London\\n\\n"
            "I'll provide:\\n"
            "• Current temperature\\n"
            "• Weather description\\n"
            "• Humidity and pressure\\n"
            "• Wind speed\\n"
            "• Feels like temperature"
        )
        await update.message.reply_text(help_text)

    async def get_weather_data(self, city_name):
        """Fetch weather data from OpenWeatherMap API."""
        params = {
            'q': city_name,
            'appid': self.weather_api_key,
            'units': 'metric'
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
        wind_speed = weather_data.get('wind', {}).get('speed', 'N/A')
        
        weather_id = weather_data['weather'][0]['id']
        emoji = self.get_weather_emoji(weather_id)
        
        message = (
            f"{emoji} Weather in {city}, {country}\\n\\n"
            f"🌡️ Temperature: {temp}°C\\n"
            f"🤔 Feels like: {feels_like}°C\\n"
            f"📝 Description: {description}\\n"
            f"💧 Humidity: {humidity}%\\n"
            f"📊 Pressure: {pressure} hPa\\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )
        
        return message

    def get_weather_emoji(self, weather_id):
        """Return appropriate emoji based on weather condition ID."""
        if weather_id < 300:
            return "⛈️"
        elif weather_id < 400:
            return "🌦️"
        elif weather_id < 600:
            return "🌧️"
        elif weather_id < 700:
            return "❄️"
        elif weather_id < 800:
            return "🌫️"
        elif weather_id == 800:
            return "☀️"
        else:
            return "☁️"

    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /weather command."""
        if not context.args:
            await update.message.reply_text(
                "Please provide a city name!\\n"
                "Example: /weather London"
            )
            return

        city_name = ' '.join(context.args)
        await self.get_weather(update, city_name)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages as city names."""
        city_name = update.message.text.strip()
        
        if city_name.startswith('/'):
            await update.message.reply_text(
                "Unknown command. Type /help for available commands."
            )
            return
            
        await self.get_weather(update, city_name)

    async def get_weather(self, update: Update, city_name: str):
        """Get weather information for a city."""
        await update.message.reply_chat_action(action="typing")
        
        try:
            weather_data = await self.get_weather_data(city_name)
            
            if weather_data is None:
                await update.message.reply_text(
                    f"❌ Sorry, I couldn't find weather information for '{city_name}'.\\n"
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
        application = Application.builder().token(self.telegram_token).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("weather", self.weather_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        application.add_error_handler(self.error_handler)

        print("🤖 Weather Bot is starting...")
        print("Bot is now running 24/7 on the cloud!")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution - reads from environment variables
if __name__ == '__main__':
    # Get tokens from environment variables (for cloud deployment)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        exit(1)
        
    if not WEATHER_API_KEY:
        print("❌ WEATHER_API_KEY environment variable not set!")
        exit(1)
    
    # Create and run the bot
    bot = WeatherBot(TELEGRAM_BOT_TOKEN, WEATHER_API_KEY)
    bot.run()
'''
    
    with open('weather_bot_cloud.py', 'w', encoding='utf-8') as f:
        f.write(bot_code)
    print("✅ Created weather_bot_cloud.py (cloud-ready version)")

def main():
    """Create all deployment files."""
    print("🚀 CREATING DEPLOYMENT FILES...")
    print("=" * 40)
    
    create_requirements_txt()
    create_procfile()
    create_railway_json()
    create_cloud_ready_bot()
    
    print("\n✅ ALL FILES CREATED SUCCESSFULLY!")
    print("\nFiles created:")
    print("• requirements.txt")
    print("• Procfile")
    print("• railway.json")
    print("• weather_bot_cloud.py")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Create GitHub repository")
    print("2. Upload all these files to GitHub")
    print("3. Deploy to Railway")
    print("4. Add environment variables")
    print("5. Your bot goes live!")

if __name__ == "__main__":
    main()
