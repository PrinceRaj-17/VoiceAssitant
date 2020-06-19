from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz
import subprocess

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december']
DAYS   = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
DAY_EXTENTIONS = ['rd','th','st','nd']

def speak(text):
	engine = pyttsx3.init()
	engine.say(text)
	engine.runAndWait()



def get_audio():	
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio)
			print(said)
		except Exception as e:
			print("Exception: " + str(e))
	return said.lower()		



def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service


def get_events(day, service):
    # Call the Calendar API
	date = datetime.datetime.combine(day, datetime.datetime.min.time())
	end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
	utc = pytz.UTC
	date = date.astimezone(utc)
	end_date = end_date.astimezone(utc)

	events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
	events = events_result.get('items', [])

	if not events:
		speak('No upcoming events found.')
	else:
		speak(f"You have {len(events)} on this day.")
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			print(start, event['summary'])
			start_time = str(start.split("T")[1].split("-")[0])

			if int(start_time.split(":")[0]) > 12:
				start_time = start_time + "am"
			else:
				start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
				start_time = start_time + "pm"

			speak(event["summary"] + " at " + start_time)		


def get_date(text):
	text = text.lower()
	today = datetime.date.today()

	if text.count('today') > 0:
		return today

	day = -1
	day_of_week = -1
	month = -1
	year = today.year

	for word in text.split():
		if word in MONTHS:
			month = MONTHS.index(word) + 1
		elif word in DAYS:
			day_of_week = DAYS.index(word)
		elif word.isdigit():
			day = int(word)
		else:
			for ext in DAY_EXTENTIONS:
				found = word.find(ext)
				if found > 0:
					try:
						day = int(word[:found])
					except:
						pass
	if month < today.month and month != -1:
		year = year + 1 

	if day < today.day and month == -1 and day != -1:
		month = month + 1

	if month == -1 and day == -1 and day_of_week != -1:
		current_day_of_weak = today.weekday()
		diff = day_of_week - current_day_of_weak

		if diff < 0:
			diff += 7
			if text.count("next") >= 1:
				diff += 7

		return today + datetime.timedelta(diff)	

	if month == -1 or day == -1:
		return None
	return datetime.date(day= day, month= month, year= year)

def note(text):
	date = datetime.datetime.now()
	file_name = str(date).replace(":", "-") + "-note.txt"

	with open(file_name, "w") as f:
		f.write(text)

	subprocess.Popen(["notepad.exe", file_name])


WAKE = "hi tony"
SERVICE = authenticate_google()
print("Started")

while True:
	print("Listening")
	text = get_audio()

	if text.count(WAKE) > 0:
		speak("I am Ready")
		text = get_audio()

		CALENDAR_STRINGS = ["what do i have", "do i have plans", "am i busy", "do i have anything"]
		for phrase in CALENDAR_STRINGS:
			if phrase in text:
				date = get_date(text)
				if date:
					get_events(date, SERVICE)
				else:
					speak("Sorry! I didn't catch that.")	

		NOTE_STRINGS = ["make a note", "write this down", "write this", "create a note", "remember this"]
		for phrase in NOTE_STRINGS:
			if phrase in text:
					speak("What would you want me to write down?")
					note_text = get_audio()
					note(note_text)
					speak("I've made a note of this for you.")

	if text == "stop":
		exit()
	