"""General spider functionality."""

import logging

import bleach
import scrapy
from asgiref.sync import sync_to_async
from geopy import Point
from django.db import transaction
from geopy.adapters import URLLibAdapter
from geopy.exc import GeocoderQueryError, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from scrapy.exceptions import DropItem
from w3lib.html import remove_tags_with_content

from events.models import Event, EventSource, Location, Organizer

logger = logging.getLogger(__name__)


class SpiderDefaultsPipeline:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item):
        for k, v in self.crawler.spider.defaults.items():
            item.setdefault(k, v)
        return item


class SanitizeHTMLPipeline:
    """Removes HTML tags from specified fields and ensures all other fields
    contain no HTML tags."""

    # Event fields to sanitize HTML from - dictionary values are a list of
    # allowed tags. All other fields are expected to be clean of HTML, and
    # items will be rejected if they contain unexpected HTML
    SANITIZE_FIELDS = {
        "description": [],
        "formatted_description": [
            "b",
            "br",
            "em",
            "i",
            "li",
            "p",
            "span",
            "strong",
            "ul",
        ],
    }

    def process_item(self, item):
        if "description" in item:
            if item["description"]:
                # bleach would strip the tags but keep their content, e.g.
                # the JSON data of an embedded calendar widget
                item["description"] = remove_tags_with_content(item["description"], which_ones=("script", "style"))
            item["formatted_description"] = item["description"]
        for field in list(item):
            if not isinstance(item[field], str):
                continue
            cleaned_value = bleach.clean(
                item[field],
                tags=self.SANITIZE_FIELDS.get(field, []),
                strip=True,
            )
            if field in self.SANITIZE_FIELDS:
                item[field] = cleaned_value
            elif item[field] != cleaned_value.replace("&amp;", "&"):
                # The replace may seem quick-and-dirty-ish but it's the same
                # thing bleach does internally when checking HTML attributes
                logger.error(
                    "Item contains unexpected HTML in field '%s': %s",
                    field,
                    item,
                )
                raise DropItem(f"Unexpected HTML in {field}")
        return item


class DatabaseExportPipeline:
    # Nominatim allows at most one request per second. Failed requests are
    # not retried (unlike geopy's default RequestsAdapter, URLLibAdapter does
    # not retry either), so its servers are not overloaded. All spiders of a
    # crawl save their items in the same thread (sync_to_async), so they share
    # the rate limit.
    geocode = RateLimiter(
        Nominatim(
            user_agent="muenster-jetzt",
            timeout=10,
            adapter_factory=URLLibAdapter,
        ).geocode,
        min_delay_seconds=1,
        max_retries=0,
        swallow_exceptions=False,
    )
    # Set once Nominatim fails, e.g. because it is rate limited or down, to
    # not ask it again in the same crawl
    geocoding_stopped = False

    async def process_item(self, item):
        # Scrapy runs an asyncio event loop, in which Django forbids
        # synchronous database access, so save the item in a separate thread
        return await sync_to_async(self.save_item)(item)

    def save_item(self, item):
        if not item.get("location"):
            # Event.location is required, and there is nothing to geocode
            raise DropItem("Event without location")
        with transaction.atomic():
            values = item.copy()
            # Coordinates of the location, if the source has them
            lat, lon = values.pop("lat", None), values.pop("lon", None)

            # check if location is in DB. if not, geocode and add.
            try:
                location_description = item["location"]
                values["location"] = Location.objects.get(description=location_description)
                if values["location"].lat is None and lat is not None:
                    values["location"].lat, values["location"].lon = lat, lon
                    values["location"].geometry_source = item["source"]
                    values["location"].save()
            except Location.DoesNotExist:
                if lat is not None and lon is not None:
                    values["location"], _ = Location.objects.get_or_create(
                        description=location_description,
                        geometry_source=item["source"],
                        lat=lat,
                        lon=lon,
                    )
                else:
                    values["location"] = self.geocode_location(location_description)

            if item["organizer"]:
                values["organizer"], _ = Organizer.objects.get_or_create(name=item["organizer"])
            values["source"], _ = EventSource.objects.get_or_create(name=item["source"])
            try:
                event = Event.objects.get(
                    source=values["source"],
                    source_event_id=values["source_event_id"],
                )
            except Event.DoesNotExist:
                event = Event()
            for k, v in values.items():
                if k not in event.dirty_fields:
                    setattr(event, k, v)
            event.save()
        return item

    def geocode_location(self, description):
        # A location that could not be geocoded is saved without coordinates
        # anyway, so it is not geocoded again in every crawl
        location = None
        if not DatabaseExportPipeline.geocoding_stopped:
            logger.debug(f"Geocoding description {description}...")
            try:
                location = self.geocode(
                    query=description,
                    viewbox=[Point(51.8375, 7.471), Point(52.061, 7.775)],
                )
            except GeocoderQueryError as e:
                # Only this query failed
                logger.warning("Geocoding %s failed: %s", description, e)
            except GeocoderServiceError as e:
                logger.warning(
                    "Geocoding %s failed, stopping geocoding: %s",
                    description,
                    e,
                )
                DatabaseExportPipeline.geocoding_stopped = True
        if location:
            # write location to database
            return Location.objects.get_or_create(
                description=description,
                geometry_source="Nominatim",
                lat=location.latitude,
                lon=location.longitude,
            )[0]
        return Location.objects.get_or_create(description=description)[0]


class EventSpider(scrapy.Spider):
    custom_settings = {
        "ITEM_PIPELINES": {
            "scraping.spiders.SpiderDefaultsPipeline": 100,
            "scraping.spiders.SanitizeHTMLPipeline": 200,
            "scraping.spiders.DatabaseExportPipeline": 900,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
        # Some sources block Scrapy's default user agent (e.g. yesticket.org)
        "USER_AGENT": "muenster-update (+https://muenster-update.de/)",
    }

    defaults = {}

    def handle_error(self, failure):
        raise Exception("Scrapy returned the following error:", failure)
