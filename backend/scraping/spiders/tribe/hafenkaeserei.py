from scraping.spiders.tribe import TribeEventsSpider


class HafenkaesereiSpider(TribeEventsSpider):
    name = "hafenkaeserei"

    defaults = {
        "source": "Genusshafen Münster GmbH",
        "source_license": None,
    }

    base_url = "https://hafenkaeserei.de"
