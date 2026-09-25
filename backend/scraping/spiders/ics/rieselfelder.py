from scraping.spiders.ics import ICalendarSpider


class RieselfelderSpider(ICalendarSpider):
    name = "rieselfelder"

    defaults = {
        "source": "Biologische Station Rieselfelder Münster",
        "source_license": None,
    }

    ics_url = "https://rieselfelder-muenster.de/?post_type=tribe_events&ical=1&eventDisplay=list"
