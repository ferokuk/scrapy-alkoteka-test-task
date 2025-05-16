import json
import time

import scrapy

from ..items import ProductItem

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AlkotekaSpider(scrapy.Spider):
    name = "alkoteka"
    allowed_domains = ["alkoteka.com"]
    start_urls = [
        "https://alkoteka.com/catalog/bezalkogolnye-napitki-1",
        "https://alkoteka.com/catalog/krepkiy-alkogol",
        "https://alkoteka.com/catalog/slaboalkogolnye-napitki-2",
        "https://alkoteka.com/catalog/shampanskoe-i-igristoe",
        "https://alkoteka.com/catalog/vino",
    ]
    cities_api_url = "https://alkoteka.com/web-api/v1/city?page={}"
    cities_api_url_page = 1
    category_api_url = (
        "https://alkoteka.com/web-api/v1/product?"
        "city_uuid={city_uuid}&"
        "root_category_slug={category_slug}&"
        "page=1&"
        "per_page=10000"
    )
    product_api_url = "https://alkoteka.com/web-api/v1/product/{slug}?city_uuid={city_uuid}"

    def __init__(self, city=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.city: str = city or "krasnodar"  # значение по умолчанию
        self.seen = set()

    async def start(self):
        # Первый запрос — получаем все города
        yield scrapy.Request(
            url=self.cities_api_url.format(self.cities_api_url_page),
            callback=self.parse_cities,
            dont_filter=True
        )

    def parse_cities(self, response):
        cities = json.loads(response.text)['meta']['accented']
        has_more = json.loads(response.text)['meta']['has_more_pages']
        found = any(city['slug'].lower() == self.city.lower() for city in cities)
        if not found:
            if has_more:
                # ещё есть страницы — идём дальше
                self.cities_api_url_page += 1
                yield scrapy.Request(
                    url=self.cities_api_url.format(self.cities_api_url_page),
                    callback=self.parse_cities,
                    dont_filter=True
                )
                return

        city = [city for city in cities if city['slug'].lower() == self.city.lower()][0]
        cookies = {
            'alkoteka_locality': json.dumps(city),
            'alkoteka_age_confirm': True
        }
        for url in self.start_urls:
            slug = url.split('/')[-1]
            yield scrapy.Request(
                url=self.category_api_url.format(city_uuid=city['uuid'], category_slug=slug),
                cookies=cookies,
                callback=self.parse_category,
                meta={'city_slug': city['slug'], 'city_uuid': city['uuid'], 'category_slug': slug}
            )

    def parse_category(self, response):
        data = json.loads(response.text)
        meta = data.get('meta', {})
        products = data.get('results', [])
        if meta['total'] < 100:
            return
        logger.info("Parsing category %s, items: %d", response.meta.get('category_slug'), meta['total'])
        for prod in products:
            city_uuid = response.meta['city_uuid']
            yield scrapy.Request(
                url=self.product_api_url.format(
                    slug=prod['slug'],
                    city_uuid=city_uuid
                ),
                callback=self.parse_product,
                cb_kwargs={"base": prod, 'url': prod['product_url']},
                dont_filter=True
            )

    def parse_product(self, response, base, url):
        detail = json.loads(response.text).get('results', {})
        logger.info("Parsing item %s", detail['name'])
        # Собираем полное описание
        desc = []
        for blk in detail.get('text_blocks', []):
            title = blk.get('title')
            content = blk.get('content', '').replace('<br>', '\n')
            desc.append(f"{title}: {content}")
        full_desc = "\n".join(desc)

        # Собираем metadata из description_blocks
        metadata = {"__description": full_desc}
        for blk in detail.get('description_blocks', []):
            title = blk.get('title')
            vals = blk.get('values') or blk.get('values', [])
            if isinstance(vals, list) and vals:
                metadata[title] = vals[0].get('name')

        # Формируем Item
        item = ProductItem()
        item['timestamp'] = int(time.time())
        item['RPC'] = str(detail.get('vendor_code') or detail.get('uuid', ''))
        item['url'] = url
        extras = [lbl['title'] for lbl in base['filter_labels']
                  if lbl['filter'] in ('obem', 'cvet')]
        item['title'] = base['name'] + (", " + ", ".join(extras) if extras else "")
        item['marketing_tags'] = base['action_labels']
        item['brand'] = (detail.get('subname') or '').strip()
        # section
        sec = []
        parent = base['category'].get('parent', {})
        if parent: sec.append(parent.get('name'))
        sec.append(base['category'].get('name'))
        item['section'] = sec
        # price_data
        curr = float(detail.get('price') or base['price'] or 0)
        orig = float(detail.get('prev_price') or base['prev_price'] or base['price'] or 0)
        sale = f"Скидка {int((1 - curr / orig) * 100)}%" if orig and curr < orig else ""
        item['price_data'] = {
            "current": curr,
            "original": orig,
            "sale_tag": sale
        }
        # stock
        item['stock'] = {
            "in_stock": bool(detail.get('available')),
            "count": int(detail.get('quantity_total') or base['quantity_total'] or 0)
        }
        # assets
        item['assets'] = {
            "main_image": detail.get('image_url') or base.get('image_url'),
            "set_images": [],
            "view360": [],
            "video": []
        }
        item['metadata'] = metadata
        # variants
        item['variants'] = len(extras)

        yield item
