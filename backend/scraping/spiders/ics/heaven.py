from scraping.spiders.ics import ICalendarSpider


class HeavenSpider(ICalendarSpider):
    name = "heaven"

    defaults = {
        "source": "heaven Münster",
        "source_license": None,
    }

    ics_url = "https://heaven-muenster.de/events/?ical=1"
    default_location = "Hafenweg 46, 48155 Münster"
