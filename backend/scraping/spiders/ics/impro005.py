from scraping.spiders.ics import ICalendarSpider


class Impro005Spider(ICalendarSpider):
    name = "impro005"

    defaults = {
        "source": "IMPRO 005",
        "source_license": None,
    }

    ics_url = "https://impro005.de/?post_type=tribe_events&ical=1&eventDisplay=list"
