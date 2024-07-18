from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet




class ActionSetIdea(Action):

    def name(self) -> Text:
        return "action_set_idea"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        if tracker.latest_message['intent']['name'] == 'has_idea':
            idea = True
        elif tracker.latest_message['intent']['name'] == 'doesnt_have_idea':
            idea = False

        dispatcher.utter_message(text="Thats awesome!")

        return [SlotSet("idea",idea)]
    
class ValidateMyForm(Action):

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


class ActionSubmit(Action):

    def name(self) -> Text:
        return "action_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        topic = tracker.get_slot("topic")
        platform = tracker.get_slot("platform")


        dispatcher.utter_message(text="Your topic is {} and your platform is {}".format(topic,platform))
        return []

