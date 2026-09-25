import re

from scraping.spiders.ics import ICalendarSpider

# UIDs start with the start and end time, e.g.
# "20261004T140000Z-20261004T160000Z-439@f24-kultur.de"
UID_TIMES = re.compile(r"^\d{8}T\d{6}Z-\d{8}T\d{6}Z-")


class F24KulturSpider(ICalendarSpider):
    name = "f24_kultur"

    defaults = {
        "source": "F24 Kulturkneipe",
        "source_license": None,
    }

    ics_url = "https://f24-kultur.de/?eme_ical=public"
    # Events Made Easy exports real UTC times ("...Z")
    convert_utc_times = True

    def parse(self, response):
        for event in super().parse(response):
            # Also imported by the peng_impro spider
            if event["name"].startswith("Peng!"):
                continue
            # Keep the ID when an event is moved
            event["source_event_id"] = UID_TIMES.sub("", event["source_event_id"])
            yield event
