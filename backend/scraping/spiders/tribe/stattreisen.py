from scraping.spiders.tribe import TribeEventsSpider


class StattreisenSpider(TribeEventsSpider):
    name = "stattreisen"

    defaults = {
        "source": "StattReisen Münster",
        "source_license": None,
    }

    base_url = "https://www.stattreisen-muenster.de"
