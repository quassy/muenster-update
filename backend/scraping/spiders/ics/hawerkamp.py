from scraping.spiders.ics import ICalendarSpider


class HawerkampSpider(ICalendarSpider):
    name = "hawerkamp"

    defaults = {
        "source": "Hawerkamp 31 e.V.",
        "source_license": None,
    }

    ics_url = "https://am-hawerkamp.de/events/?ical=1"
