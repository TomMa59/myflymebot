# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.schema import InputHints
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from .cancel_and_help_dialog import CancelAndHelpDialog


class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.init_step,
                self.destination_step,
                self.origin_step,
                self.start_travel_date_step,
                self.return_travel_date_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__

    async def init_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """save initial ask"""
        booking_details = step_context.options
        booking_details.init_text = step_context.context

        return await step_context.next(booking_details.init_text)

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options

        if booking_details.destination is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("To what city would you like to travel?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From what city will you be travelling?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)

    async def start_travel_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for starting travel date."""
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result
        if booking_details.start_travel_date is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("On what date would you like to start your trip?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.start_travel_date)

    async def return_travel_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for starting travel date."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.start_travel_date = step_context.result
        if booking_details.return_travel_date is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("On what date would you like to come back from your trip?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.return_travel_date)

    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for trip budget."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.return_travel_date = step_context.result
        if booking_details.budget is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("What is your budget for the trip?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.budget)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.budget = step_context.result
        msg = (
            f"Please confirm, I have you traveling to: { booking_details.destination }"
            f" from: { booking_details.origin } on: { booking_details.start_travel_date}."
            f" You plan to have a return trip on: { booking_details.return_travel_date }"
            f" and your budget is: { booking_details.budget }"
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction, send data to Azure app insights and end the dialog."""
        
        # Data to be tracked in app insights
        booking_details = step_context.options
        properties = {}
        properties['init_text'] = booking_details.init_text
        properties['destination'] = booking_details.destination
        properties['origin'] = booking_details.origin
        properties['start_travel_date'] = booking_details.start_travel_date
        properties['return_travel_date'] = booking_details.return_travel_date
        properties['budget'] = booking_details.budget
        
        #If positive answer
        if step_context.result:
            self.telemetry_client.track_trace("VALIDATED BOOKING", properties, "INFO")
            return await step_context.end_dialog(booking_details)
        
        else:
            sorry_msg = "I am sorry, I will improve myself in the near future"
            prompt_sorry_msg = MessageFactory.text(sorry_msg, sorry_msg, InputHints.ignoring_input)
            await step_context.context.send_activity(prompt_sorry_msg)
            self.telemetry_client.track_trace("BOOKING PREDICTION ERROR", properties, "ERROR")
        return await step_context.end_dialog()

# DEBUG, INFO, WARNING, ERROR, CRITICAL