# Imports
from service.bot import Bot
from config import API_KEY



def main():
    bot = Bot(API_KEY, )
    bot.start_bot()


if __name__ == "__main__":
    main()
    