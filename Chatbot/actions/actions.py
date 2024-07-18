from typing import Any, Text, Dict, List
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet,ReminderScheduled, ReminderCancelled




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
                                 '''{}\n-------------\nWhich topic would you like to choose?'''.format(topic_list))

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
                Your list for the domain {} is :\n{}\n-------------------------\nYour selection : {}\n-------------------------\nDo you like these topics or should I search for something different?'''.format(domain,topic_list,selected_num)

        dispatcher.utter_message(text=text)
        return []

class ActionGeminiAPI(Action):
    
    @staticmethod
    def get_gemini_response(tracker):
        return "Running gemini api"

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

        #----------------------------------------------------------------
        dispatcher.utter_message(text=self.get_gemini_response(tracker))
        #----------------------------------------------------------------
        
        dispatcher.utter_message(text="Do you want me to remind you to post after some specified amount of time?")
        
        return []
    
    
class ActionSetReminder(Action):
    """Schedules a reminder, supplied with the last message's entities."""
    
    @staticmethod
    def get_time(tracker):
        return int(10)

    def name(self) -> Text:
        return "action_set_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        #----------------------------------------------------------------
        time = self.get_time(tracker)
        #----------------------------------------------------------------
        
        
        dispatcher.utter_message("I will remind you in {} seconds.".format(time))

        date = datetime.datetime.now() + datetime.timedelta(seconds=time)
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

        dispatcher.utter_message(f"Remember to post your content!")

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
        dispatcher.utter_message('Thank you for using RasaScribe!')
        
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