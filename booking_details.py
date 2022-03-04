# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        start_travel_date: str = None,
        return_travel_date: str = None,
        budget: str = None,
        unsupported_city=None,
    ):
        if unsupported_city is None:
            unsupported_city = []
        self.destination = destination
        self.origin = origin
        self.start_travel_date = start_travel_date
        self.return_travel_date = return_travel_date
        self.budget = budget
        self.unsupported_city = unsupported_city
