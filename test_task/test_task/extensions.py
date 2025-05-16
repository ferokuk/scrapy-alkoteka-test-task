from scrapy import signals
from tqdm import tqdm

class ProgressBarExtension:
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.stats)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.item_scraped,  signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_closed,  signal=signals.spider_closed)
        return ext

    def __init__(self, stats):
        self.stats = stats
        self.pbar  = None

    def spider_opened(self, spider):
        # Берём total из stats, который ранее установили в parse_category
        total = self.stats.get_value('total')
        self.pbar = tqdm(total=total,
                         desc="Scraping",
                         unit="it",
                         leave=True)  # если total=None, tqdm покажет базовый бар без ETA
        # При total=None прогресс‑бар всё равно обновляется, но без прогноза

    def item_scraped(self, item, spider):
        self.pbar.update(1)

    def spider_closed(self, spider, reason):
        self.pbar.close()
