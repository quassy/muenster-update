from scraping.spiders.ics import ICalendarSpider


class RepaircafeMsSpider(ICalendarSpider):
    name = "repaircafe_ms"

    defaults = {
        "source": "Repair Café Münster",
        "source_license": None,
    }

    ics_url = "https://repaircafe-muenster.de/events/?ical=1"
