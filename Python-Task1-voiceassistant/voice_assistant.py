import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import requests
import smtplib
import threading
import json
import os
import re

# ============================================================
# CONFIGURATION
# ============================================================

WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
DEFAULT_CITY = "Kolkata"

# Use a dedicated test email account.
EMAIL_ADDRESS = "your_test_email@gmail.com"
EMAIL_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

CUSTOM_COMMANDS_FILE = "custom_commands.json"

# ============================================================
# TEXT TO SPEECH
# ============================================================

engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)


def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()


# ============================================================
# SPEECH RECOGNITION
# ============================================================

recognizer = sr.Recognizer()


def listen():
    """Listen to microphone and convert speech into text."""
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )
        except sr.WaitTimeoutError:
            speak("I did not hear anything. Please try again.")
            return ""

    try:
        print("Recognizing...")
        command = recognizer.recognize_google(
            audio,
            language="en-IN"
        )
        command = command.lower()
        print("You:", command)
        return command

    except sr.UnknownValueError:
        speak("Sorry, I could not understand you. Please repeat.")
        return ""
    except sr.RequestError:
        speak("Speech recognition service is unavailable.")
        return ""


# ============================================================
# TIME AND DATE
# ============================================================

def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}.")


def tell_date():
    current_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    speak(f"Today is {current_date}.")


# ============================================================
# WEB SEARCH
# ============================================================

def web_search(query):
    if not query:
        speak("Please tell me what you want to search.")
        return

    speak(f"Searching the web for {query}.")
    url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    webbrowser.open(url)


# ============================================================
# WEATHER
# ============================================================

def get_weather(city):
    if WEATHER_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
        speak("Please add your OpenWeatherMap API key inside the Python file.")
        return

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            speak("I could not find weather information for that city.")
            return

        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]

        speak(
            f"The weather in {city} is {description}. "
            f"The temperature is {temperature} degrees Celsius. "
            f"It feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent."
        )

    except requests.RequestException:
        speak("I could not connect to the weather service.")


# ============================================================
# REMINDER
# ============================================================

def reminder_alert(message):
    speak(f"Reminder: {message}")


def set_reminder(seconds, message):
    speak(f"Okay. I will remind you in {seconds} seconds.")

    timer = threading.Timer(
        seconds,
        reminder_alert,
        args=[message]
    )
    timer.daemon = True
    timer.start()


def extract_number(text):
    numbers = re.findall(r"\d+", text)
    return int(numbers[0]) if numbers else None


# ============================================================
# EMAIL
# ============================================================

def send_email(recipient, subject, message):
    if (
        EMAIL_ADDRESS == "your_test_email@gmail.com"
        or EMAIL_PASSWORD == "YOUR_GMAIL_APP_PASSWORD"
    ):
        speak("Please configure your test email credentials in the Python file.")
        return

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        email_text = f"Subject: {subject}\n\n{message}"

        server.sendmail(
            EMAIL_ADDRESS,
            recipient,
            email_text
        )
        server.quit()

        speak("Your email has been sent successfully.")

    except Exception as error:
        print("Email error:", error)
        speak("I could not send the email.")


def email_by_voice():
    speak("Who should receive the email?")
    recipient = listen()

    if not recipient:
        return

    speak("What should be the subject?")
    subject = listen()

    if not subject:
        subject = "Voice Assistant Email"

    speak("What message should I send?")
    message = listen()

    if not message:
        return

    recipient = recipient.replace(" ", "")
    send_email(recipient, subject, message)


# ============================================================
# GENERAL KNOWLEDGE
# ============================================================

knowledge_base = {
    "python": (
        "Python is a popular high level programming language "
        "used for web development, automation, data science, "
        "artificial intelligence and many other applications."
    ),
    "html": (
        "HTML stands for HyperText Markup Language. "
        "It is used to structure web pages."
    ),
    "css": (
        "CSS stands for Cascading Style Sheets. "
        "It is used to style and design web pages."
    ),
    "javascript": (
        "JavaScript is a programming language commonly used "
        "to make websites interactive."
    ),
    "ai": (
        "Artificial intelligence is the field of creating "
        "computer systems that can perform tasks that normally "
        "require human intelligence."
    )
}


def answer_question(question):
    for keyword, answer in knowledge_base.items():
        if keyword in question:
            speak(answer)
            return True
    return False


# ============================================================
# CUSTOM COMMANDS
# ============================================================

def load_custom_commands():
    if not os.path.exists(CUSTOM_COMMANDS_FILE):
        return {}

    try:
        with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_custom_command(command, response):
    commands = load_custom_commands()
    commands[command] = response

    with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as file:
        json.dump(commands, file, indent=4)

    speak(f"I added the custom command {command}.")


def check_custom_commands(command):
    commands = load_custom_commands()

    for custom_command, response in commands.items():
        if custom_command in command:
            speak(response)
            return True

    return False


# ============================================================
# NATURAL LANGUAGE INTENT DETECTION
# ============================================================

def process_command(command):
    if not command:
        return

    # Custom commands
    if check_custom_commands(command):
        return

    # Greeting
    if any(word in command for word in [
        "hello", "hi", "hey", "good morning", "good afternoon"
    ]):
        speak("Hello! How can I help you today?")
        return

    # Exit
    if any(phrase in command for phrase in [
        "exit", "quit", "goodbye", "stop assistant", "close assistant"
    ]):
        speak("Goodbye! Have a great day.")
        return "exit"

    # Time
    if "time" in command or "what time" in command:
        tell_time()
        return

    # Date
    if "date" in command or "today" in command or "what day" in command:
        tell_date()
        return

    # Weather
    if "weather" in command or "temperature" in command:
        city = DEFAULT_CITY

        match = re.search(r"(?:in|at|for)\s+(.+)", command)
        if match:
            city = match.group(1).strip()

        get_weather(city)
        return

    # Web search
    if "search for" in command or "search" in command or "google" in command:
        query = command

        for phrase in ["search for", "search", "google"]:
            query = query.replace(phrase, "")

        web_search(query.strip())
        return

    # Websites
    if "open youtube" in command:
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")
        return

    if "open google" in command:
        speak("Opening Google.")
        webbrowser.open("https://www.google.com")
        return

    if "open github" in command:
        speak("Opening GitHub.")
        webbrowser.open("https://github.com")
        return

    # Reminder
    if "remind me" in command or "set a reminder" in command:
        number = extract_number(command)

        if number is None:
            speak("Please specify the number of seconds.")
            return

        message = re.sub(
            r"\d+\s*(seconds?|minutes?|hours?)",
            "",
            command
        )
        message = message.replace("remind me", "")
        message = message.replace("set a reminder", "")
        message = message.strip()

        if "minute" in command:
            number *= 60
        elif "hour" in command:
            number *= 3600

        if not message:
            message = "check your reminder."

        set_reminder(number, message)
        return

    # Email
    if (
        "send an email" in command
        or "send email" in command
        or "email someone" in command
    ):
        email_by_voice()
        return

    # Add custom command
    if (
        "add custom command" in command
        or "create custom command" in command
    ):
        speak("Tell me the command phrase.")
        custom_command = listen()

        if not custom_command:
            return

        speak("What should I say when that command is used?")
        response = listen()

        if response:
            save_custom_command(custom_command, response)

        return

    # Knowledge base
    if answer_question(command):
        return

    # Unknown command
    speak(
        "I am not sure how to help with that. "
        "You can ask me for the time, date, weather, "
        "a web search, a reminder, or an email."
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    speak("Voice assistant started. How can I help you?")

    while True:
        command = listen()

        if command:
            result = process_command(command)

            if result == "exit":
                break


if __name__ == "__main__":
    main()
