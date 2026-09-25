from scraping.spiders.ics import ICalendarSpider


class StLiudgerMsSpider(ICalendarSpider):
    name = "st_liudger_ms"

    defaults = {
        "source": "Pfarrei St. Liudger Münster",
        "source_license": None,
    }

    ics_url = "https://www.kirche-mswest.de/termine/?ical=1"
    default_location = "Münster"
