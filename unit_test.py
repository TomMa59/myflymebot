import json
from os import path
from typing import Dict, Tuple, Union
from unittest import mock
from unittest.mock import Mock
from msrest import Deserializer
from requests import Session
from requests.models import Response

from aiounittest.case import AsyncTestCase

from config import DefaultConfig

from botbuilder.ai.luis import LuisApplication, LuisPredictionOptions, LuisRecognizer
from botbuilder.core.adapters import TestAdapter
from botbuilder.core import BotAdapter, RecognizerResult, TurnContext
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount, ConversationAccount


class LuisRecognizerTest(AsyncTestCase):
    CONFIG = DefaultConfig()
    _luisAppId: str = CONFIG.LUIS_APP_ID
    _subscriptionKey: str = CONFIG.LUIS_API_KEY
    _endpoint: str = "https://" + CONFIG.LUIS_API_HOST_NAME


    def test_luis_recognizer_construction(self):
        # Arrange
        endpoint = (
            LuisRecognizerTest._endpoint + "/luis/v2.0/apps/"
            + LuisRecognizerTest._luisAppId + "?verbose=true&timezoneOffset=-360"
            "&subscription-key=" + LuisRecognizerTest._subscriptionKey + "&q="
        )

        # Act
        recognizer = LuisRecognizer(endpoint)

        # Assert
        app = recognizer._application
        self.assertEqual(LuisRecognizerTest._luisAppId, app.application_id)
        self.assertEqual(LuisRecognizerTest._subscriptionKey, app.endpoint_key)
        self.assertEqual("https://westeurope.api.cognitive.microsoft.com", app.endpoint)

    def test_luis_recognizer_none_luis_app_arg(self):
        with self.assertRaises(TypeError):
            LuisRecognizer(application=None)
    
    async def test_multiple_intents_list_entity_with_single_value(self):
        utterance: str = "I need to book a plane from Paris to Toronto on april 12th and return on april 21st. I have a budget of 2100$."
        response_path: str = "MultipleIntents_ListEntityWithSingleValue.json"

        _, result = await LuisRecognizerTest._get_recognizer_result(
            utterance, response_path
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.text)
        self.assertEqual(utterance, result.text)
        self.assertIsNotNone(result.intents)
        self.assertIsNotNone(result.intents["book"])
        self.assertIsNotNone(result.entities)
        self.assertIsNotNone(result.entities["$instance"])
        self.assertIsNotNone(result.entities["$instance"]["budget"])
        self.assertEqual(104, result.entities["$instance"]["budget"][0]["startIndex"])
        self.assertEqual(111, result.entities["$instance"]["budget"][0]["endIndex"])
        self.assertEqual("2100 $ .", result.entities["$instance"]["budget"][0]["text"])
        self.assertIsNotNone(result.entities["$instance"]["dst_city"])
        self.assertEqual(37, result.entities["$instance"]["dst_city"][0]["startIndex"])
        self.assertEqual(45, result.entities["$instance"]["dst_city"][0]["endIndex"])
        self.assertEqual("toronto", result.entities["$instance"]["dst_city"][0]["text"])
        self.assertIsNotNone(result.entities["$instance"]["end_date"])
        self.assertEqual(73, result.entities["$instance"]["end_date"][0]["startIndex"])
        self.assertEqual(85, result.entities["$instance"]["end_date"][0]["endIndex"])
        self.assertEqual("april 21st .", result.entities["$instance"]["end_date"][0]["text"])
        self.assertIsNotNone(result.entities["$instance"]["or_city"])
        self.assertEqual(28, result.entities["$instance"]["or_city"][0]["startIndex"])
        self.assertEqual(34, result.entities["$instance"]["or_city"][0]["endIndex"])
        self.assertEqual("paris", result.entities["$instance"]["or_city"][0]["text"])
        self.assertIsNotNone(result.entities["$instance"]["str_date"])
        self.assertEqual(48, result.entities["$instance"]["str_date"][0]["startIndex"])
        self.assertEqual(59, result.entities["$instance"]["str_date"][0]["endIndex"])
        self.assertEqual("april 12th", result.entities["$instance"]["str_date"][0]["text"])


    @classmethod
    async def _get_recognizer_result(
        cls,
        utterance: str,
        response_json: Union[str, Dict[str, object]],
        bot_adapter: BotAdapter = TestAdapter(),
        options: LuisPredictionOptions = None,
        include_api_results: bool = False,
        telemetry_properties: Dict[str, str] = None,
        telemetry_metrics: Dict[str, float] = None,
        recognizer_class: type = LuisRecognizer,
    ) -> Tuple[LuisRecognizer, RecognizerResult]:
        if isinstance(response_json, str):
            response_json = LuisRecognizerTest._get_json_for_file(
                response_file=response_json
            )

        recognizer = LuisRecognizerTest._get_luis_recognizer(
            recognizer_class, include_api_results=include_api_results, options=options
        )
        context = LuisRecognizerTest._get_context(utterance, bot_adapter)
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {}
        response.reason = ""
        with mock.patch.object(Session, "send", return_value=response):
            with mock.patch.object(
                Deserializer, "_unpack_content", return_value=response_json
            ):
                result = await recognizer.recognize(
                    context, telemetry_properties, telemetry_metrics
                )
                return recognizer, result
    
    @classmethod
    def _get_json_for_file(cls, response_file: str) -> Dict[str, object]:
        curr_dir = path.dirname(path.abspath(__file__))
        response_path = path.join(curr_dir, "test_data", response_file)

        with open(response_path, "r", encoding="utf-8-sig") as file:
            response_str = file.read()
        response_json = json.loads(response_str)
        return response_json
    
    @classmethod
    def _get_luis_recognizer(
        cls,
        recognizer_class: type,
        options: LuisPredictionOptions = None,
        include_api_results: bool = False,
    ) -> LuisRecognizer:
        luis_app = LuisApplication(cls._luisAppId, cls._subscriptionKey, cls._endpoint)
        return recognizer_class(
            luis_app,
            prediction_options=options,
            include_api_results=include_api_results,
        )

    @staticmethod
    def _get_context(utterance: str, bot_adapter: BotAdapter) -> TurnContext:
        activity = Activity(
            type=ActivityTypes.message,
            text=utterance,
            conversation=ConversationAccount(),
            recipient=ChannelAccount(),
            from_property=ChannelAccount(),
        )
        return TurnContext(bot_adapter, activity)