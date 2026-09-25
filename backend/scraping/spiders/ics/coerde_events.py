from scraping.spiders.ics import ICalendarSpider


class CoerdeEventsSpider(ICalendarSpider):
    name = "coerde_events"

    defaults = {
        "source": "Coerde Events",
        "source_license": "CC BY 4.0",
    }

    ics_url = "https://raw.githubusercontent.com/Coerdeevents/coerde-events/main/data/events.ics"

    def parse(self, response):
        for event in super().parse(response):
            # Also imported by the stadt_muenster_kalender spider
            if (event["url"] or "").startswith("https://www.stadt-muenster.de/"):
                continue
            yield event
