from scraping.spiders.tribe import TribeEventsSpider


class StudierendenwerkMsSpider(TribeEventsSpider):
    name = "studierendenwerk_ms"

    defaults = {
        "source": "Studierendenwerk Münster",
        "source_license": None,
    }

    base_url = "https://www.stw-muenster.de"
