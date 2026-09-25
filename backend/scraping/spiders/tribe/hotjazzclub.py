import re

from scraping.spiders.tribe import TribeEventsSpider

# Cancelled or moved concerts stay listed, e.g. "Joy Bogat – Konzertabsage"
# or "Elise FRANK & Band verschoben auf 13.05.2027"
CANCELLED = re.compile(
    r"Konzertabsage|Konzertverschiebung|abgesagt|verschoben auf",
    re.IGNORECASE,
)


class HotJazzClubSpider(TribeEventsSpider):
    name = "hotjazzclub"

    defaults = {
        "source": "Hot Jazz Club",
        "source_license": None,
    }

    base_url = "https://www.hotjazzclub.de"
    default_location = "Hafenweg 26b, 48155 Münster"

    def parse_event(self, event):
        item = super().parse_event(event)
        item["visible"] = not CANCELLED.search(item["name"])
        return item
