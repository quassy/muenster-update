import json
import re
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import scrapy

from scraping.spiders import EventSpider

TIME_ZONE = ZoneInfo("Europe/Berlin")

# Organizers and venues with their own spider, whose dates would be imported
# twice otherwise
OWN_SPIDERS = (
    r"Biologische Station Rieselfelder|Friedenskapelle|Hot Jazz Club"
    r"|Peng! Impro|Skaters Palace|StattReisen Münster"
)
OWN_ORGANIZERS = re.compile(rf"^({OWN_SPIDERS})\b")
# The Kulturbahnhof's ticket shop only has the events at the venue with
# tickets, e.g. not its exhibitions without a location
OWN_VENUES = re.compile(rf"^({OWN_SPIDERS}|Kulturbahnhof Hiltrup)\b")

# Based on the queries of the calendar's web app at
# https://events-calendar.stadt-muenster.de/build/app/app.js
QUERY = """
query EventDateList(
    $page: Int
    $first: Int!
    $where: QueryEventDatesWhereWhereConditions
    $orderBy: [QueryEventDatesOrderByOrderByClause!]
) {
    eventDates(page: $page, first: $first, where: $where, orderBy: $orderBy) {
        data {
            id
            start
            end
            eventDateRemarks {
                type
            }
            eventInfo {
                id
                title
                subtitle
                description
                eventOrganizer {
                    name
                }
                eventTags {
                    label
                    category
                }
            }
            eventSchedule {
                full_day
                eventLocation {
                    name
                    street
                    house_no
                    postal_code
                    city
                    latitude
                    longitude
                }
            }
        }
        paginatorInfo {
            hasMorePages
        }
    }
}
"""


def utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def join(separator: str, *parts: str | None) -> str:
    return separator.join(part.strip() for part in parts if part and part.strip())


class StadtMuensterKalenderSpider(EventSpider):
    name = "stadt_muenster_kalender"

    defaults = {
        "source": "Stadt Münster",
        "source_license": None,
    }

    api_url = "https://events-calendar.stadt-muenster.de/graphql"
    # Recurring events are listed for years, only crawl the next weeks
    days_ahead = 30
    page_size = 200

    async def start(self):
        today = datetime.combine(datetime.now(TIME_ZONE).date(), time(), TIME_ZONE)
        until = today + timedelta(days=self.days_ahead)
        where = {
            "AND": [
                # Like the calendar's web app, include dates that already
                # started, e.g. of exhibitions
                {
                    "OR": [
                        {
                            "column": column,
                            "operator": "GTE",
                            "value": utc_iso(today),
                        }
                        for column in ("START", "END")
                    ]
                },
                {"column": "START", "operator": "LT", "value": utc_iso(until)},
            ]
        }
        yield self.request(1, where)

    def request(self, page, where):
        variables = {
            "page": page,
            "first": self.page_size,
            "where": where,
            "orderBy": [{"column": "START", "order": "ASC"}],
        }
        return scrapy.Request(
            self.api_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"query": QUERY, "variables": variables}),
            cb_kwargs={"page": page, "where": where},
            errback=self.handle_error,
        )

    def parse(self, response, page, where):
        data = response.json()
        if "errors" in data:
            raise ValueError(f"GraphQL query failed: {data['errors']}")
        event_dates = data["data"]["eventDates"]
        for event_date in event_dates["data"]:
            organizer = event_date["eventInfo"]["eventOrganizer"] or {}
            location = (event_date["eventSchedule"] or {}).get("eventLocation") or {}
            if OWN_ORGANIZERS.match(organizer.get("name") or "") or OWN_VENUES.match(location.get("name") or ""):
                continue
            yield self.parse_event_date(event_date)
        if event_dates["paginatorInfo"]["hasMorePages"]:
            yield self.request(page + 1, where)

    def parse_event_date(self, event_date):
        info = event_date["eventInfo"]
        schedule = event_date["eventSchedule"] or {}
        full_day = schedule.get("full_day")
        start = datetime.fromisoformat(event_date["start"]).astimezone(TIME_ZONE)
        end = event_date["end"] and datetime.fromisoformat(event_date["end"]).astimezone(TIME_ZONE)
        # Some multi-day events end before they start
        if end and end < start:
            end = None
        location = schedule.get("eventLocation") or {}
        types = [tag["label"] for tag in info["eventTags"] if tag["category"] == "TYPE"]
        item = {
            "source_event_id": event_date["id"],
            "name": info["title"].strip(),
            "description": (join("\n\n", info["subtitle"], info["description"]) or None),
            "url": (f"https://www.stadt-muenster.de/veranstaltungskalender#/detail/{info['id']}/{event_date['id']}"),
            "start_date": start.date(),
            "start_time": None if full_day else start.time(),
            "end_date": end.date() if end else None,
            "end_time": end.time() if end and not full_day else None,
            "location": join(
                ", ",
                location.get("name"),
                join(" ", location.get("street"), location.get("house_no")),
                join(" ", location.get("postal_code"), location.get("city")),
            )
            # Events without a location take place somewhere in the city
            or "Münster",
            "lat": location.get("latitude") or None,
            "lon": location.get("longitude") or None,
            "mode": types[0] if types else None,
            "organizer": (info["eventOrganizer"] or {}).get("name") or None,
        }
        remarks = {remark["type"] for remark in event_date["eventDateRemarks"]}
        item["visible"] = not remarks & {"CANCELLED", "RESCHEDULED"}
        return item
