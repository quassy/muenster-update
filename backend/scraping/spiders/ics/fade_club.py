from scraping.spiders.ics import ICalendarSpider


class FadeClubSpider(ICalendarSpider):
    name = "fade_club"

    defaults = {
        "source": "Fade Club",
        "source_license": None,
    }

    ics_url = "https://www.fade-club.de/events/?ical=1"
    default_location = "Am Hawerkamp 31, 48155 Münster"
