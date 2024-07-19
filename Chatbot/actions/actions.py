from typing import Any, Text, Dict, List
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet,ReminderScheduled, ReminderCancelled
import os
import google.generativeai as genai
import json




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
    def get_topic_list(domain):
        return "Your topic list is : 1,2,3,4,5"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        domain = tracker.get_slot('domain')
        
        #----------------------------------------------------------------
        topic_list = self.get_topic_list(domain=domain)
        #----------------------------------------------------------------
        
        dispatcher.utter_message(text=
                                 '''{}\n-------------\nWhich topic would you like to choose? 🤔💭'''.format(topic_list))

        return [SlotSet('topic_list',topic_list)]


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
        
        text = '''
                Your list for the domain {} is :\n{}\n-------------------------\nYour selection : {}\n-------------------------\nContinue with the selected domain and topic or do you want to choose another domain? 🔎'''.format(domain,topic_list,selected_num)

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
            output = 'running gemini api'
            
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

        #----------------------------------------------------------------
        dispatcher.utter_message(text=output_text)
        #----------------------------------------------------------------
        
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
        
class ActionCleanMemory(Action):
    """Flush out all the slots."""
    
    def name(self) -> Text:
        return "action_clean_memory"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        return [SlotSet('domain',None),SlotSet('topic_list',None),SlotSet('idea',None),SlotSet('selected_num',None),SlotSet('platform',None),SlotSet('topic',None)]