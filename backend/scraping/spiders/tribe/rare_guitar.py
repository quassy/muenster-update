from scraping.spiders.tribe import TribeEventsSpider


class RareGuitarSpider(TribeEventsSpider):
    name = "rare_guitar"

    defaults = {
        "source": "Rare Guitar",
        "source_license": None,
    }

    base_url = "https://bar.rareguitar.de"
