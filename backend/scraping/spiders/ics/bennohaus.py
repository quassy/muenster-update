from scraping.spiders.ics import ICalendarSpider


class BennohausSpider(ICalendarSpider):
    name = "bennohaus"

    defaults = {
        "source": "Bennohaus",
        "source_license": None,
    }

    ics_url = "https://bennohaus.de/kurse/?ical=1"
