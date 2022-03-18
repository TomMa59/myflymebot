# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails


class Intent(Enum):
    BOOK_FLIGHT = "book"
    CANCEL = "Cancel"
    NONE_INTENT = "None"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            if intent == Intent.BOOK_FLIGHT.value:
                result = BookingDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                
                result.init_text = recognizer_result.text
                
                to_entities = recognizer_result.entities.get("$instance", {}).get(
                    "dst_city", []
                )
                if len(to_entities) > 0:
                    if recognizer_result.entities.get("dst_city", [{"$instance": {}}])[0]:
                        result.destination = to_entities[0]["text"].capitalize()
                    else:
                        result.unsupported_city.append(
                            to_entities[0]["text"].capitalize()
                        )

                from_entities = recognizer_result.entities.get("$instance", {}).get(
                    "or_city", []
                )
                if len(from_entities) > 0:
                    if recognizer_result.entities.get("or_city", [{"$instance": {}}])[0]:
                        result.origin = from_entities[0]["text"].capitalize()
                    else:
                        result.unsupported_city.append(
                            from_entities[0]["text"].capitalize()
                        )

                start_date_entities = recognizer_result.entities.get("$instance", {}).get(
                    "str_date", []
                )
                if len(start_date_entities) > 0:
                    if recognizer_result.entities.get("str_date", [{"$instance": {}}])[0]:
                        result.start_travel_date = start_date_entities[0]["text"]
                        
                return_date_entities = recognizer_result.entities.get("$instance", {}).get(
                    "end_date", []
                )
                if len(return_date_entities) > 0:
                    if recognizer_result.entities.get("end_date", [{"$instance": {}}])[0]:
                        result.return_travel_date = return_date_entities[0]["text"]                

                budget_entities = recognizer_result.entities.get("$instance", {}).get(
                    "budget", []
                )
                if len(budget_entities) > 0:
                    if recognizer_result.entities.get("budget", [{"$instance": {}}])[0]:
                        result.budget = budget_entities[0]["text"]  

        except Exception as exception:
            print(exception)

        return intent, result
