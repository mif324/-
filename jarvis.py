import datetime
import os
import random
import subprocess
import urllib.parse
import webbrowser

import requests
import speech_recognition as sr
import pyttsx3

from config import Config


class Jarvis:
    def __init__(self):
        # --- Инициализация распознавания ---
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        self.voice_mode = True
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"⚠️  Микрофон недоступен: {e}")
            print("👉 Переключаюсь в текстовый режим.\n")
            self.voice_mode = False
            self.microphone = None

        # --- Инициализация TTS ---
        self.engine = pyttsx3.init()
        self._setup_tts()

        self.is_running = True

    # ------------------------------------------------------------------
    #  СИНТЕЗ И РАСПОЗНАВАНИЕ РЕЧИ
    # ------------------------------------------------------------------
    def _setup_tts(self):
        self.engine.setProperty("rate", Config.VOICE_RATE)
        self.engine.setProperty("volume", Config.VOICE_VOLUME)
        for voice in self.engine.getProperty("voices"):
            vid = voice.id.lower()
            vname = voice.name.lower()
            if "ru" in vid or "russian" in vname or "irina" in vname:
                self.engine.setProperty("voice", voice.id)
                break

    def speak(self, text: str):
        print(f"🤖 JARVIS: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except RuntimeError:
            # переинициализация на случай «залипания» движка
            self.engine = pyttsx3.init()
            self._setup_tts()
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")

    def listen(self):
        # Текстовый режим (fallback)
        if not self.voice_mode:
            try:
                text = input("👤 Вы (текст): ").strip().lower()
                return text or None
            except (EOFError, KeyboardInterrupt):
                return None

        # Голосовой режим
        with self.microphone as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(
                    source, timeout=5, phrase_time_limit=10
                )
                text = self.recognizer.recognize_google(
                    audio, language=Config.LANGUAGE
                )
                print(f"👤 Вы: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"⚠️  Ошибка сервиса распознавания: {e}")
                return None
            except Exception as e:
                print(f"⚠️  Ошибка микрофона: {e}")
                return None

    # ------------------------------------------------------------------
    #  СКИЛЛЫ
    # ------------------------------------------------------------------
    def get_time(self):
        now = datetime.datetime.now()
        return f"Сейчас {now.hour} часов {now.minute} минут"

    def get_date(self):
        now = datetime.datetime.now()
        months = ["января", "февраля", "марта", "апреля", "мая", "июня",
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        days = ["понедельник", "вторник", "среда", "четверг",
                "пятница", "суббота", "воскресенье"]
        return (f"Сегодня {days[now.weekday()]}, "
                f"{now.day} {months[now.month - 1]} {now.year} года")

    def get_weather(self, city: str = None):
        city = city or Config.DEFAULT_CITY
        query_city = Config.CITY_MAP.get(city.lower(), city)
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": query_city, "count": 1, "language": "ru"},
                timeout=5,
            ).json()

            if not geo.get("results"):
                return f"Не могу найти город «{city}»."

            loc = geo["results"][0]
            weather = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "current_weather": True,
                },
                timeout=5,
            ).json()

            cw = weather["current_weather"]
            cond = {
                0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность",
                3: "пасмурно", 45: "туман", 48: "изморозь",
                51: "лёгкая морось", 53: "морось", 55: "сильная морось",
                61: "лёгкий дождь", 63: "дождь", 65: "сильный дождь",
                71: "лёгкий снег", 73: "снег", 75: "сильный снег",
                95: "гроза",
            }.get(cw["weathercode"], "неизвестно")

            return (f"В городе {loc.get('name', city)} сейчас "
                    f"{cw['temperature']}°C, {cond}, "
                    f"ветер {cw['windspeed']} км/ч.")
        except Exception as e:
            return f"Не удалось получить погоду: {e}"

    def search_wikipedia(self, query: str):
        try:
            import wikipedia as wiki
            wiki.set_lang("ru")
            return wiki.summary(query, sentences=2)
        except Exception:
            return f"Не удалось найти информацию про «{query}»."

    def take_screenshot(self):
        try:
            from PIL import ImageGrab
            os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
            path = os.path.join(
                Config.SCREENSHOT_DIR,
                f"screenshot_{datetime.datetime.now():%Y%m%d_%H%M%S}.png",
            )
            ImageGrab.grab().save(path)
            return f"Скриншот сохранён в {path}"
        except Exception as e:
            return f"Не удалось сделать скриншот: {e}"

    def open_program(self, cmd: str):
        for key, exe in Config.PROGRAMS.items():
            if key in cmd:
                try:
                    subprocess.Popen(exe, shell=True)
                    return f"Открываю {key}."
                except Exception as e:
                    return f"Не удалось открыть {key}: {e}"
        return None

    # ------------------------------------------------------------------
    #  РОУТЕР КОМАНД
    # ------------------------------------------------------------------
    def process_command(self, command: str) -> bool:
        if not command:
            return True

        cmd = command.lower().strip()

        # Выход
        if any(w in cmd for w in ["стоп", "выход", "пока", "завершись",
                                  "спать", "отключись"]):
            self.speak("До свидания, сэр.")
            return False

        # Помощь
        if "помощь" in cmd or "что ты умеешь" in cmd:
            self.speak(
                "Я умею: сообщать время и дату, погоду, искать в Google, "
                "Википедии и YouTube, открывать программы, делать скриншоты, "
                "рассказывать шутки."
            )
            return True

        # Приветствие
        if any(w in cmd for w in ["привет", "здравствуй", "хай", "добрый"]):
            self.speak(random.choice([
                "Приветствую!", "Здравствуйте, сэр.",
                "К вашим услугам.", "Да, сэр?"
            ]))
            return True

        # Время
        if "время" in cmd or "час" in cmd:
            self.speak(self.get_time())
            return True

        # Дата
        if any(w in cmd for w in ["дата", "число", "какой день"]):
            self.speak(self.get_date())
            return True

        # Погода
        if "погод" in cmd:
            city = None
            for prep in [" в ", " во "]:
                if prep in cmd:
                    city = cmd.split(prep)[-1].strip(" ?.")
                    break
            self.speak(self.get_weather(city))
            return True

        # Шутка
        if any(w in cmd for w in ["шутк", "анекдот", "смешн", "пошути"]):
            self.speak(random.choice([
                "Программист — это человек, который решает проблему, о которой "
                "вы не знали, способом, который вы не понимаете.",
                "Почему программисты путают Хэллоуин и Рождество? "
                "Потому что Oct 31 == Dec 25.",
                "Я бы рассказал шутку про рекурсию, но сначала расскажу "
                "шутку про рекурсию.",
            ]))
            return True

        # Скриншот
        if "скриншот" in cmd or "снимок экрана" in cmd:
            self.speak(self.take_screenshot())
            return True

        # YouTube
        if "ютуб" in cmd or "youtube" in cmd:
            self.speak("Открываю YouTube.")
            webbrowser.open("https://youtube.com")
            return True

        # Google
        if "гугл" in cmd or "google" in cmd:
            self.speak("Открываю Google.")
            webbrowser.open("https://google.com")
            return True

        # Музыка (YouTube search)
        if "включи" in cmd and any(w in cmd for w in ["музык", "песн"]):
            self.speak("Включаю музыку на YouTube.")
            webbrowser.open(
                "https://www.youtube.com/results?search_query=music"
            )
            return True

        # Поиск в интернете
        if any(w in cmd for w in ["найди", "поищи", "загугли"]):
            q = cmd
            for w in ["найди", "поищи", "загугли", "в интернете",
                      "в гугле", "в google"]:
                q = q.replace(w, "")
            q = q.strip(" ?.")
            if q:
                self.speak(f"Ищу «{q}».")
                webbrowser.open(
                    f"https://www.google.com/search?q={urllib.parse.quote(q)}"
                )
            return True

        # Wikipedia
        if any(w in cmd for w in ["википеди", "что такое", "кто такой",
                                   "кто такая", "расскажи о", "расскажи про"]):
            q = cmd
            for w in ["википедия", "что такое", "кто такой", "кто такая",
                      "расскажи про", "расскажи о"]:
                q = q.replace(w, "")
            q = q.strip(" ?.")
            if q:
                self.speak(self.search_wikipedia(q))
            return True

        # Программы
        res = self.open_program(cmd)
        if res:
            self.speak(res)
            return True

        # Опасные команды
        if Config.ENABLE_POWER_COMMANDS:
            if "выключи компьютер" in cmd:
                self.speak("Выключаю компьютер.")
                os.system("shutdown /s /t 5")
                return False
            if "перезагрузи" in cmd:
                self.speak("Перезагружаю компьютер.")
                os.system("shutdown /r /t 5")
                return False

        self.speak("Не понял команду. Скажите «помощь», чтобы узнать, "
                   "что я умею.")
        return True

    # ------------------------------------------------------------------
    #  ГЛАВНЫЙ ЦИКЛ
    # ------------------------------------------------------------------
    def run(self):
        self.speak("JARVIS активирован. Слушаю вас.")

        while self.is_running:
            text = self.listen()
            if not text:
                continue

            if Config.USE_WAKE_WORD:
                wake = any(w in text for w in Config.WAKE_WORDS)
                if not wake:
                    continue
                for w in Config.WAKE_WORDS:
                    text = text.replace(w, "").strip(" ,.")
                if not text:
                    self.speak("Да, сэр?")
                    text = self.listen()
                    if not text:
                        continue

            self.is_running = self.process_command(text)


def main():
    try:
        Jarvis().run()
    except KeyboardInterrupt:
        print("\n👋 Завершение работы.")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()