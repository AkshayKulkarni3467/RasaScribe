from typing import Any, Text, Dict, List
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet,ReminderScheduled, ReminderCancelled
import os
import google.generativeai as genai
import json
from datetime import date
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import mysql.connector
import time






class ActionSetIdea(Action):

    def name(self) -> Text:
        return "action_set_idea"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        if tracker.latest_message['intent']['name'] == 'has_idea':
            dispatcher.utter_message(text="Thats awesome!")
            idea = True
        elif tracker.latest_message['intent']['name'] == 'doesnt_have_idea':
            idea = False


        return [SlotSet("idea",idea)]
    

class ActionResetSlots(Action):

    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        


        return [SlotSet("domain",None),SlotSet("topic_list",None),SlotSet("selected_num",None)]
    
    

    
class ValidateMyInputForm(Action):

    def name(self) -> Text:
        return "input_form"


    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        required_slots = ["topic","platform"]

        for slot_name in required_slots:
            if tracker.slots.get(slot_name) is None:
                return [SlotSet('requested_slot', slot_name)]

        return [SlotSet('requested_slot', None)]


class ActionInputFormSubmit(Action):

    def name(self) -> Text:
        return "action_input_form_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        topic = tracker.get_slot("topic")
        platform = tracker.get_slot("platform")
        
        return []

class AskSelectedNum(Action):
    

    def name(self) -> Text:
        return "action_ask_selected_num"
    
    @staticmethod
    def youtube_search(q,maxResults):
        YOUTUBE_API_SERVICE_NAME = 'youtube'
        YOUTUBE_API_VERSION = 'v3'
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=os.getenv('YOUTUBE_API_KEY'))

        # Call the search.list method to retrieve results matching the specified
        # query term.
        search_response = youtube.search().list(
          q=q,
          part='id,snippet',
          maxResults=maxResults,
          type='videos'
        ).execute()

        return search_response
    
    @staticmethod
    def check_publication(date,no_of_years=3):
        time = date.split('-')
        published_time = datetime.date(int(time[0]),int(time[1]),int(time[2]))
        check_time = datetime.datetime.now() - datetime.timedelta(days=365*no_of_years)
        return check_time.date() < published_time
    
    @staticmethod
    def get_script(list_video_ids):
        script_1 = ''
        for i in list_video_ids:
          try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(i)
            script_obj = transcript_list.find_transcript(['en'])
            script = script_obj.translate('en').fetch()
          except:
            continue
          for j in script:
            script_1 += j['text']
        return script_1

    @staticmethod
    def get_domain(sentence):
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"},
            )
        
        prompt =f'''
            you extract the domain mentioned in the give sentence {sentence}
            Return this domain in the json schema
            Content = {{"domain" : str}}
            Return a Content object'''
        
        response = model.generate_content(prompt)
        
        object = json.loads(response.text)
        return object['domain']

    
    def get_yt_video_ids(self,response,no_of_years):
        youtube_id_list = [i['id']['videoId'] for i in response['items'] if self.check_publication(i['snippet']['publishedAt'].split('T')[0],no_of_years) and 'videoId' in i['id'].keys()]

#---------------------------------------------------------------- Change the index slicing to generate a much longer transcript

        return youtube_id_list[:5]
    
#----------------------------------------------------------------
        
    def get_topic_list(self,domain,dispatcher):
        
        query_string = 'trending in {}'.format(domain)

#----------------------------------------------------------------- Change max results to retrive more context for the script

        response = self.youtube_search(query_string,maxResults=25)
        
#-----------------------------------------------------------------        

    
#---------------------------------------------------------------- Change the number of years for the script to include past events 
    
        response = self.get_yt_video_ids(response,no_of_years=3)
    
#----------------------------------------------------------------
        script = self.get_script(response)
        
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"},
            )
        
        chat = model.start_chat(history=[])
        
        prompt = f'''You are a summarizer.
            You will be given a script and you have to summarize it
            and generate five important topic from it. Add jargons related to those topics.
            Make sure that the length of each topic is at least 10 words and atmost 20 words.
            Make sure that the topics are related to the domain {domain}.
            Your script is {script}
            You will return the five topics in the json schema
            Content = {{"topic 1" : str, "topic 2" : str, "topic 3" : str, ...}}
            Return a Content object
            '''
            
        response = chat.send_message(prompt)
        
        output = json.loads(response.text)
        
        for i,j in enumerate(output.keys()):
            dispatcher.utter_message('''Topic {} : \n{}'''.format(i+1,output.get(j)))
            time.sleep(2)
        
        return chat,response.text
    
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        domain = tracker.get_slot('domain')
        
        extracted_domain = self.get_domain(domain)
        
        chat,response = self.get_topic_list(domain=extracted_domain,dispatcher=dispatcher)
        
        dispatcher.utter_message(text='''Which topic would you like to choose? 🤔💭''')

        return [SlotSet('topic_list',response),SlotSet('domain',extracted_domain)]


class ValidateMyRequestForm(Action):
    

    def name(self) -> Text:
        return "request_form"


    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        required_slots = ["domain","selected_num"]

        for slot_name in required_slots:
            if tracker.slots.get(slot_name) is None:
                return [SlotSet('requested_slot', slot_name)]

        return [SlotSet('requested_slot', None)]


class ActionRequestFormSubmit(Action):

    def name(self) -> Text:
        return "action_request_form_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        domain = tracker.get_slot("domain")
        topic_list = tracker.get_slot("topic_list")
        selected_num = tracker.get_slot("selected_num")
        
        text = '''Just a min, working on your selected topic... 🔎\nShould I keep the selected topic or choose a different domain?'''

        dispatcher.utter_message(text=text)
        return []

class ActionGeminiAPI(Action):
    
    @staticmethod
    def get_gemini_response(tracker):
        if tracker.get_slot('idea') == True:
            api_key = os.getenv("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"},
            )
            topic = tracker.get_slot('topic')
            platform = tracker.get_slot('platform')
            
            prompt =f'''
                You are a freelance script writer for social media.You generate scripts, captions and hashtags. 
                You are currently making a post on {topic} 
                which is going to be posted on {platform}
                Remember to start every post with a question!
                Use numbers as points, not *, keep only one space distance between a point and next letter.
                Dont use ** to bold the texts, since not every platform converts them to bold
                You should not include any visual, voiceover or variable elements in the script, captions and hashtags! You are a script writer and you should output the entire post completed!
                If the platform is linkedin, twitter, etc, make the content formal and use formal emojis.
                For linkedin posts generate a post with some jargons and technical details based on the topic.
                For twitter posts, make sure that the post length is less than 60 words.
                For script:
                If the platform is youtube generate a script which can hold upto 5 minutes of video and dont divide the script into points.
                If the platform is instagram, tiktok or shorts generate a script which can hold upto 30 seconds video, divide the script into points and keep the scripts informal and try to develop engaging content and use more emojis than formal content.
                For instagram, tiktok and shorts, generate a catchy response.
                Make the script size depending on the platform.
                For caption:
                Dont generate hashtags in captions!
                For hashtags:
                Generate atleast 10 hashtags related to the topic
                Remember to not seperate the text and just output them on new lines
                Using this JSON schema:
                Content = {{"script": str, "caption": str, "hashtags": str}}
                Return a Content object'''

            response = model.generate_content(prompt)
            
            output = json.loads(response.text)
        
        elif tracker.get_slot('idea') == False:
            topic_list = tracker.get_slot('topic_list')
            required_topic_num = tracker.get_slot('selected_num')
            
            prompt = f'''You return the object requested from a given list.
                This is a list of topics {topic_list}
                Return the topic specified in the request : {required_topic_num}.
                Return it into the json schema:
                Content : {{"selected_topic" : str}}
                Return the content object'''
            api_key = os.getenv("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)
            output = json.loads(response.text)
            
            topic = output['selected_topic']
            platform = tracker.get_slot('platform')
            
            prompt =f'''
                You are a freelance script writer for social media.You generate scripts, captions and hashtags. 
                You are currently making a post on {topic} 
                which is going to be posted on {platform}
                Remember to start every post with a question!
                Use numbers as points, not *, keep only one space distance between a point and next letter.
                Dont use ** to bold the texts, since not every platform converts them to bold
                You should not include any visual, voiceover or variable elements in the script, captions and hashtags! You are a script writer and you should output the entire post completed!
                If the platform is linkedin, twitter, etc, make the content formal and use formal emojis.
                For linkedin posts generate a post with some jargons and technical details based on the topic.
                For twitter posts, make sure that the post length is less than 60 words.
                For script:
                If the platform is youtube generate a script which can hold upto 5 minutes of video and dont divide the script into points.
                If the platform is instagram, tiktok or shorts generate a script which can hold upto 30 seconds video, divide the script into points and keep the scripts informal and try to develop engaging content and use more emojis than formal content.
                For instagram, tiktok and shorts, generate a catchy response.
                Make the script size depending on the platform.
                For caption:
                Dont generate hashtags in captions!
                For hashtags:
                Generate atleast 10 hashtags related to the topic
                Remember to not seperate the text and just output them on new lines
                Using this JSON schema:
                Content = {{"script": str, "caption": str, "hashtags": str}}
                Return a Content object'''
                
            response = model.generate_content(prompt)
            
            output = json.loads(response.text)
            
        return output

    def name(self) -> Text:
        return "action_gemini_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        flag = tracker.get_slot('idea')
        
        if flag == True:
            text = '''Your topic is : {}\n-------------------------\nYour platform is : {}'''.format(tracker.get_slot('topic'),tracker.get_slot('platform'))
        if flag == False:
            text = '''Your domain is {}\n-------------------------\nYour platform is : {}'''.format(tracker.get_slot('domain'),tracker.get_slot('platform'))
            
        dispatcher.utter_message(text=text)
        
        output = self.get_gemini_response(tracker)
        
        output_script = output['script']
        output_caption = output['caption']
        output_hashtags = output['hashtags']
        
        output_text = '''Script: \n{}\n-------------------------\nCaptions: \n{}\n-------------------------\nHashtags: \n{}'''.format(output_script,output_caption,output_hashtags)

        dispatcher.utter_message(text=output_text)
        
        dispatcher.utter_message(text="Do you want me to remind you to post after some specified amount of time? ⏰")
        
        return []
    
    
class ActionSetReminder(Action):
    """Schedules a reminder, supplied with the last message's entities."""
    
    @staticmethod
    def get_time(tracker):
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"},
            )
        time = tracker.latest_message['text']
        
        prompt = f'''
            You measure any give time in hours, minutes and seconds.
            Remove the time provided in this {time} string and convert it into hours, minutes and seconds.
            If no time is provided in the string, return 1 minute
            write the time in the following json schema
            Content = {{"hours": str, "minutes": str, "seconds":str}}
            Return a Content object'''
            
        response = model.generate_content(prompt)
        
        output = json.loads(response.text)
        
        hours = output['hours']
        minutes = output['minutes']
        seconds = output['seconds']
        
        time_in_sec = (int(hours)*60*60)+(int(minutes)*60)+(int(seconds))
        
        return hours,minutes,seconds,time_in_sec

    def name(self) -> Text:
        return "action_set_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        hours,minutes,seconds,time_in_sec = self.get_time(tracker=tracker)        
        
        dispatcher.utter_message("Timer set for: {} hrs {} mins {} sec".format(hours,minutes,seconds))

        date = datetime.datetime.now() + datetime.timedelta(seconds=time_in_sec)
        entities = tracker.latest_message.get("entities")

        reminder = ReminderScheduled(
            "EXTERNAL_reminder",
            trigger_date_time=date,
            entities=entities,
            name="my_reminder",
            kill_on_user_message=False,
        )

        return [reminder]


class ActionReactToReminder(Action):
    """Reminds the user to call someone."""

    def name(self) -> Text:
        return "action_react_to_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(f"🚨 Remember to post your content! 🚨")

        return []
    
class ForgetReminders(Action):
    """Cancels all reminders."""

    def name(self) -> Text:
        return "action_forget_reminders"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("Okay, I'll cancel all your reminders.")

        # Cancel all reminders
        return [ReminderCancelled()]
    
class ActionThank(Action):
    """Appereciate the user for using the bot."""
    
    def name(self) -> Text:
        return "action_thank"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message('Thank you for using RasaScribe! 🌟✍️')
        
        conn = mysql.connector.connect(host='localhost', password=os.getenv('SQL_PW'),user='root')
        cursor = conn.cursor()
        cursor.execute('use rasascribe;')
        
        create_table = '''CREATE TABLE if not exists User (
              id INT PRIMARY KEY auto_increment,
              has_idea varchar(10),
              topic varchar(255),
              platform varchar(100),
              domain varchar(100),
              topic_list varchar(3000),
              text_of_selected_num varchar(500)
            );'''
        cursor.execute(create_table)
        
        insert_into_table = '''INSERT INTO User (has_idea, topic, platform, domain,topic_list,text_of_selected_num)
            values (%s, %s, %s, %s, %s, %s)'''
        values = [str(tracker.get_slot('idea')),tracker.get_slot('topic'),tracker.get_slot('platform'),tracker.get_slot('domain'),tracker.get_slot('topic_list'),tracker.get_slot('selected_num')]
        cursor.execute(insert_into_table,values)
        conn.commit()
        conn.close()
        
        return []
        
