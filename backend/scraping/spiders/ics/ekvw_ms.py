import re
from datetime import timedelta

from scraping.spiders.ics import ICalendarSpider

# Veranstalter IDs of the Protestant congregations in the city of Münster
VERANSTALTER_IDS = "508,215,2380,480,2142,2283,2204,2194,2434,337,2420,2408,553,2407,551,548,2346,2203,2395"

# The descriptions start with the full address of the venue, e.g.
# "Ort: Trinitatiskirche\nStraßburger Weg  15\n48151 Münster"
ADDRESS = re.compile(r"^Ort: (.+)\n(.+)\n(\d{5} .+)$", re.MULTILINE)
CANCELLED = re.compile(r"fällt aus|entfällt|abgesagt", re.IGNORECASE)
# UIDs start with the start time, e.g.
# "20261213T180000-1324241@evangelische-termine.de"
UID_START = re.compile(r"^\d{8}T\d{6}-")


class EkvwMsSpider(ICalendarSpider):
    name = "ekvw_ms"

    defaults = {
        "source": "Evangelische Kirche von Westfalen",
        "source_license": None,
    }

    ics_url = f"https://www.veranstaltungen-ekvw.de/Veranstalter/iCal.php?vid={VERANSTALTER_IDS}&enc=utf8&note=long"
    # The feed ends events without an end after one hour
    placeholder_duration = timedelta(hours=1)

    def parse(self, response):
        for event in super().parse(response):
            description = event["description"] or ""
            if event["name"].startswith("TEST") or ("Testeintrag" in description):
                continue
            # Keep the ID when an event is moved
            event["source_event_id"] = UID_START.sub("", event["source_event_id"])
            event["visible"] = not CANCELLED.search(event["name"])
            # LOCATION only has the name, e.g. "Münster: Trinitatiskirche"
            address = ADDRESS.search(description)
            if address:
                event["location"] = ", ".join(" ".join(part.split()) for part in address.groups())
            yield event
