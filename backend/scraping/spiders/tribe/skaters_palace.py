from scraping.spiders.tribe import TribeEventsSpider


class SkatersPalaceSpider(TribeEventsSpider):
    name = "skaters_palace"

    defaults = {
        "source": "Skaters Palace",
        "source_license": None,
    }

    base_url = "https://www.skaters-palace.de"
    # The venue field holds tour names instead of the venue
    ignore_venue = True
    default_location = "Skaters Palace, Dahlweg 126, 48153 Münster"
