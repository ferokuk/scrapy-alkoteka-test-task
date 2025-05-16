## Описание

Проект на базе Scrapy предназначен для парсинга данных с сайта "Алкотека". С помощью паука можно собирать информацию о различной продукции в разных городах.

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone <URL_репозитория>
   cd <папка_проекта>
   ```
2. Создайте и активируйте виртуальное окружение:

   ```bash
   python -m venv .venv
   source .venv/bin/activate # Linux/macOS
   .\.venv\Scripts\activate  # Windows
   ```
3. Установите зависимости:

   ```bash
   pip install -r requirements.txt```

## Структура проекта

```text
scrapy-test-task/
├── .venv/               # виртуальное окружение
└── test_task/           # корень Scrapy-проекта
    ├── scrapy.cfg       # конфиг Scrapy
    ├── requirements.txt # зависимости
    ├── .gitignore
    ├── cities.json      # список доступных городов
    └── test_task/       # пакет с исходниками паука
        ├── spiders/      # папка с пауками
        │   └── alkoteka_spider.py
        ├── items.py      # описание структуры элементов
        ├── pipelines.py  # обработка собранных данных
        └── settings.py   # настройки проекта
```

## Использование

В корне проекта выполните команду:

```bash
scrapy crawl spider_name -O result.json
```

### Параметры запуска

* `-O result.json` — сохранить результат в файл `result.json`, перезаписывая его.
* `-a city=<город>` — указать город для фильтрации (по умолчанию `krasnodar`). Список городов находится в файле cities.json. Необходимо указывать поле slug

## Примеры

* Парсинг данных без указания города (используется `krasnodar` по умолчанию):

  ```bash
  scrapy crawl spider_name -O result.json
  ```

* Парсинг для Москвы:

  ```bash
  scrapy crawl spider_name -a city=moskva -O result.json
  ```

* Парсинг для Краснодара:

  ```bash
  scrapy crawl spider_name -a city=krasnodar -O result.json # (по умолчанию)
  ```

## Настройки

При необходимости измените настройки подключения, задержки и других параметров в файле `test_task/settings.py`.<br>
При необходимости измените список proxy в файле `test_task/middlewares.py`, классе `RandomProxyMiddleware`.<br>
При необходимости измените список ссылок на категории в пауке `test_task\spiders\alkoteka_spider.py`.
