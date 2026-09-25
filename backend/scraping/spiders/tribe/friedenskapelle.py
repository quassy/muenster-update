from scraping.spiders.tribe import TribeEventsSpider


class FriedenskapelleSpider(TribeEventsSpider):
    name = "friedenskapelle"

    defaults = {
        "source": "Friedenskapelle Münster",
        "source_license": None,
    }

    base_url = "https://www.friedenskapelle.ms"
    # Same as the location of its other events
    default_location = "Friedenskapelle am Friedenspark, Willy-Brandt-Weg 37 b, Münster, 48155, Deutschland"
