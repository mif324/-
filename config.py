import os

class Config:
    # Язык распознавания
    LANGUAGE = "ru-RU"

    # Активационное слово (можно выключить: USE_WAKE_WORD = False)
    USE_WAKE_WORD = True
    WAKE_WORDS = ["джарвис", "jarvis", "жарвис"]

    # Голос
    VOICE_RATE = 180
    VOICE_VOLUME = 1.0

    # Погода
    DEFAULT_CITY = "Москва"
    CITY_MAP = {
        "москва": "Moscow",
        "питер": "Saint Petersburg",
        "санкт-петербург": "Saint Petersburg",
        "новосибирск": "Novosibirsk",
        "екатеринбург": "Yekaterinburg",
        "казань": "Kazan",
        "сочи": "Sochi",
        "минск": "Minsk",
        "киев": "Kyiv",
        "алматы": "Almaty",
    }

    # Программы (Windows). На Linux/macOS замените на свои команды
    PROGRAMS = {
        "блокнот": "notepad.exe",
        "калькулятор": "calc.exe",
        "paint": "mspaint.exe",
        "проводник": "explorer.exe",
    }

    # Опасные команды (по умолчанию отключены)
    ENABLE_POWER_COMMANDS = False

    # Папка для скриншотов
    SCREENSHOT_DIR = os.path.expanduser("~/Pictures")