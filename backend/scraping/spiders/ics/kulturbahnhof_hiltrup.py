import re
from datetime import timedelta

from scraping.spiders.ics import ICalendarSpider

# The feed has no URL, the description starts with the ticket shop's page
TICKETS = re.compile(r"^Tickets: (\S+)", re.MULTILINE)


class KulturbahnhofHiltrupSpider(ICalendarSpider):
    name = "kulturbahnhof_hiltrup"

    defaults = {
        "source": "Kulturbahnhof Hiltrup e.V.",
        "source_license": None,
    }

    ics_url = "https://ticketshop.kulturbahnhof-hiltrup.de/events/ical/?locale=de"
    # pretix ends events without an end after one hour
    placeholder_duration = timedelta(hours=1)

    def parse(self, response):
        for event in super().parse(response):
            # The ticket shop lists its gift vouchers like an event
            if "geschenkgutschein" in event["source_event_id"]:
                continue
            tickets = TICKETS.search(event["description"] or "")
            if not event["url"] and tickets:
                event["url"] = tickets.group(1)
            yield event
