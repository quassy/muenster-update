from scraping.spiders.ics import ICalendarSpider


class SeniorenvertretungMsSpider(ICalendarSpider):
    name = "seniorenvertretung_ms"

    defaults = {
        "source": "Kommunale Seniorenvertretung Münster",
        "source_license": None,
    }

    ics_url = "https://seniorenvertretung-muenster.de/?post_type=tribe_events&ical=1&eventDisplay=list"
