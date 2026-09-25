from django.core.management.base import BaseCommand, CommandError
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


class Command(BaseCommand):
    help = "Crawl events and populate database"

    def add_arguments(self, parser):
        parser.add_argument(
            "spider",
            nargs="*",
            help=(
                "Name(s) of spider(s) to run. Will run all spiders if missing."
            ),
        )

    def handle(self, *args, **options):
        settings = Settings(
            {
                "SPIDER_MODULES": ["scraping.spiders"],
                # Would start servers allowing code execution in the crawl
                # process, which is not needed
                "REMOTE_CONTROL_ENABLED": False,
                "TELNETCONSOLE_ENABLED": False,
            }
        )
        # CrawlerProcess installs the reactor configured by Scrapy, so do not
        # import twisted.internet.reactor before it
        process = CrawlerProcess(settings)
        # Run all spiders if none specified
        spiders = options["spider"] or process.spider_loader.list()
        for spider_name in spiders:
            process.crawl(spider_name)
        process.start()
        if process.bootstrap_failed:
            raise CommandError("At least one spider failed to start")
