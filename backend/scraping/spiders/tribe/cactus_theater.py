from scraping.spiders.tribe import TribeEventsSpider


class CactusTheaterSpider(TribeEventsSpider):
    name = "cactus_theater"

    defaults = {
        "source": "Cactus Junges Theater",
        "source_license": None,
    }

    base_url = "https://cactus-theater.de"
