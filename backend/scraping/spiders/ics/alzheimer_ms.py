from scraping.spiders.ics import ICalendarSpider


class AlzheimerMsSpider(ICalendarSpider):
    name = "alzheimer_ms"

    defaults = {
        "source": "Alzheimer Gesellschaft Münster e.V.",
        "source_license": None,
    }

    ics_url = "https://alzheimer-muenster.de/?post_type=tribe_events&ical=1&eventDisplay=list"
