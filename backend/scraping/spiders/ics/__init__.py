from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import scrapy

from icalendar import Calendar
from icalendar.error import IncompleteComponent, InvalidCalendar
from scraping.spiders import EventSpider

TIME_ZONE = ZoneInfo("Europe/Berlin")


def str_or_none(vevent_item, key):

    v = vevent_item.get(key)

    if v is None:
        return v

    return str(v)


def split_date_time(value: date) -> tuple[date, time | None]:
    """Split a DATE-TIME into date and time, a DATE has no time."""
    if isinstance(value, datetime):
        return value.date(), value.time()
    return value, None


def to_local_time(value: date) -> date:
    """Convert a DATE-TIME with a time zone to Europe/Berlin. DATEs and
    floating DATE-TIMEs (without a time zone) are returned unchanged."""
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(TIME_ZONE)
    return value


class ICalendarSpider(EventSpider):
    ics_url: str
    # Location for events without a LOCATION, e.g. the venue of a club
    default_location: str | None = None
    # Convert times with a time zone to Europe/Berlin, for feeds with real
    # UTC times ("...Z"). Otherwise the wall-clock time is stored as is,
    # because sites using The Events Calendar label local times as UTC.
    convert_utc_times = False
    # Some feeds end events without an end after a fixed duration, e.g.
    # DTEND = DTSTART + 1 hour. Ends after this duration are left out.
    placeholder_duration: timedelta | None = None

    async def start(self):
        resp = scrapy.Request(
            self.ics_url,
            errback=self.handle_error,
        )
        yield resp

    def parse(self, response):

        ics_data = Calendar.from_ical(response.text)

        for item in ics_data.events:
            if "UID" not in item or "SUMMARY" not in item:
                self.logger.warning("Skipping event %s without UID or SUMMARY", item.get("UID"))
                continue
            # Also computes the end of events without DTEND as defined in
            # RFC 5545 (one day for all-day events, else the start)
            try:
                start, end = item.start, item.end
            except (IncompleteComponent, InvalidCalendar) as e:
                self.logger.warning(
                    "Skipping event %s with invalid start or end: %s",
                    item.get("UID"),
                    e,
                )
                continue
            if self.convert_utc_times:
                start, end = to_local_time(start), to_local_time(end)

            start_date, start_time = split_date_time(start)
            end_date, end_time = split_date_time(end)
            # The end date of all-day events is exclusive
            if end_time is None and end_date > start_date:
                end_date -= timedelta(days=1)
            if (
                start_time is not None
                and end_time is not None
                and datetime.combine(end_date, end_time) - datetime.combine(start_date, start_time)
                == self.placeholder_duration
            ):
                end_date = end_time = None

            clean_name = str(item["SUMMARY"])
            prefix = f"{start.strftime('%d.%m.%Y')} - "
            if clean_name.startswith(prefix):
                clean_name = clean_name.replace(prefix, "")

            event = {
                "source_event_id": str(item["UID"]),
                "name": clean_name.strip(),
                "description": str_or_none(item, "DESCRIPTION"),
                "url": str_or_none(item, "URL"),
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "location": ((str_or_none(item, "LOCATION") or "").strip() or self.default_location),
                # "mode": event_data["Veranstaltung"],
                "organizer": str_or_none(item, "ORGANIZER"),
            }

            yield event
