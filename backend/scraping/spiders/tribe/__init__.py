"""Spiders for WordPress sites using the plugin The Events Calendar."""

from datetime import date, datetime, time, timedelta, timezone
from html import unescape
from urllib.parse import urlencode, urlsplit

import scrapy

from scraping.spiders import EventSpider

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def uid_timestamp(value: datetime) -> int:
    """Timestamp as in the UIDs of the plugin's ICS export, which interprets
    the local time as UTC."""
    return int(value.replace(tzinfo=timezone.utc).timestamp())


class TribeEventsSpider(EventSpider):
    """Reads the REST API of The Events Calendar. Unlike the plugin's ICS
    export, which is limited to 30 events, it is paginated."""

    # Home URL of the WordPress site, e.g. "https://hafenkaeserei.de"
    base_url: str
    # Location for events without a venue, e.g. the address of a club
    default_location: str | None = None
    # Use default_location for all events, e.g. if the site misuses venues
    ignore_venue = False
    days_ahead = 365

    async def start(self):
        today = date.today()
        query = urlencode(
            {
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(self.days_ahead)).isoformat(),
                "per_page": 50,
            }
        )
        yield scrapy.Request(
            f"{self.base_url}/wp-json/tribe/events/v1/events?{query}",
            errback=self.handle_error,
        )

    def parse(self, response):
        data = response.json()
        for event in data["events"]:
            if not event["hide_from_listings"]:
                yield self.parse_event(event)
        if data.get("next_rest_url"):
            yield response.follow(data["next_rest_url"], errback=self.handle_error)

    def parse_event(self, event):
        start = datetime.strptime(event["start_date"], DATE_TIME_FORMAT)
        end = datetime.strptime(event["end_date"], DATE_TIME_FORMAT)
        # Same as the UID in the ICS export, so events keep their ID when a
        # spider switches from the ICS export to the API. The export uses
        # different IDs for some events, though.
        uid = f"{event['id']}-{uid_timestamp(start)}-{uid_timestamp(end)}@{urlsplit(self.base_url).netloc}"
        if event["all_day"]:
            # All-day events end just before the site's "end of day cutoff"
            # (the time of their start, e.g. 04:00) on the day after
            end -= start - datetime.combine(start.date(), time())
        elif end < start:
            # Events ending after midnight are sometimes saved with the date
            # of their start
            end += timedelta(days=1)
        # The API returns an empty list for events without a venue
        venue = {} if self.ignore_venue else event["venue"] or {}
        organizers = event["organizer"]
        return {
            "source_event_id": uid,
            "name": unescape(event["title"]).strip(),
            "description": event["description"] or None,
            "url": event["url"],
            "start_date": start.date(),
            "start_time": None if event["all_day"] else start.time(),
            "end_date": end.date() if end >= start else None,
            "end_time": (None if event["all_day"] or end < start else end.time()),
            "location": self.location(venue),
            "lat": venue.get("geo_lat"),
            "lon": venue.get("geo_lng"),
            "organizer": (unescape(organizers[0]["organizer"]) if organizers else None),
        }

    def location(self, venue) -> str | None:
        """Location as in the ICS export of the plugin."""
        parts = (
            unescape(venue.get(key) or "").strip()
            for key in (
                "venue",
                "address",
                "city",
                "stateprovince",
                "zip",
                "country",
            )
        )
        return ", ".join(part for part in parts if part) or (self.default_location)
