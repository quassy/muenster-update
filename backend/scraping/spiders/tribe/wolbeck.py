from scraping.spiders.tribe import TribeEventsSpider


class WolbeckSpider(TribeEventsSpider):
    name = "wolbeck"

    defaults = {
        "source": "Münster-Wolbeck in Südost",
        "source_license": None,
    }

    base_url = "https://www.wolbeck-muenster.de"
    default_location = "Münster-Wolbeck"
