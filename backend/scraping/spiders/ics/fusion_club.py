from scraping.spiders.ics import ICalendarSpider


class FusionClubSpider(ICalendarSpider):
    name = "fusion_club"

    defaults = {
        "source": "Fusion Club",
        "source_license": None,
    }

    ics_url = "https://www.fusion-club.de/events/?ical=1"
    default_location = "Hafenweg 46, 48155 Münster"
