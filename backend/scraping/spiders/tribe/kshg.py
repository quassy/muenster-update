from scraping.spiders.tribe import TribeEventsSpider


class KshgSpider(TribeEventsSpider):
    name = "kshg"

    defaults = {
        "source": "KSHG Münster",
        "source_license": None,
    }

    base_url = "https://www.kshg.de"
    default_location = "KSHG, Frauenstraße 3-6, 48143 Münster"
