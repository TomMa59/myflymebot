import os
import json
import time
import datetime
import numpy as np
from tqdm import tqdm

from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from msrest.authentication import CognitiveServicesCredentials

SUBSCRIPTION_KEY_ENV_NAME = os.environ.get('LuisAuthKey')

def booking_app(subscription_key):
    """Authoring.
    This will create a LUIS Booking application, train and publish it.
    """
    client = LUISAuthoringClient(
        'https://westeurope.api.cognitive.microsoft.com',
        CognitiveServicesCredentials(subscription_key),
    )

    try:
        # Create a LUIS app
        default_app_name = "MyFlyMeBot-{}".format(datetime.datetime.now())
        version_id = "0.1"

        print("Creating App {}, version {}".format(
            default_app_name, version_id))

        app_id = client.apps.add({
            'name': default_app_name,
            'initial_version_id': version_id,
            'description': "FlyMeBot to book flights - trained on frames.json from Microsoft",
            'culture': 'en-us',
        })
        print("Created app {}".format(app_id))

        # Add information into the model

        print("\nWe'll add the intent 'book' and 5 entities ['or_city', 'dst_city', 'str_date', 'end_date', 'budget']")

        client.model.add_intent(app_id, version_id, 'book')
        print("intent created")

        client.model.add_entity(app_id, version_id, name="or_city")
        client.model.add_entity(app_id, version_id, name="dst_city")
        client.model.add_entity(app_id, version_id, name="str_date")
        client.model.add_entity(app_id, version_id, name="end_date")
        client.model.add_entity(app_id, version_id, name="budget")
        print("entities created")

        print("\nAdding utterances by batch, please wait")

        number_of_files = np.arange(0, 4000, 100)
        for file in tqdm(number_of_files):
            with open('examples/FlyMeData_' + str(file) + '.json', 'r') as f:
                data = json.load(f)
            client.examples.batch(app_id, version_id, data)

        print("\nUtterances added!")

        # Training the model
        print("\nWe'll start training your app...")

        async_training = client.train.train_version(app_id, version_id)
        is_trained = async_training.status == "UpToDate"

        trained_status = ["UpToDate", "Success"]
        while not is_trained:
            time.sleep(1)
            status = client.train.get_status(app_id, version_id)
            is_trained = all(
                m.details.status in trained_status for m in status)

        print("Your app is trained. You can now go to the LUIS portal and test it!")

        # Publish the app
        print("\nWe'll start publishing your app...")

        client.apps.update_settings(app_id, is_public=True)
        publish_result = client.apps.publish(
            app_id, version_id, is_staging=False, region='westeurope')
        endpoint = publish_result.endpoint_url + \
            "?subscription-key=" + subscription_key + "&q="
        print("Your app is published. You can now go to test it!\n{}".format(endpoint))

    except Exception as err:
        print("Encountered exception. {}".format(err))

if __name__ == "__main__":
    booking_app(SUBSCRIPTION_KEY_ENV_NAME)
