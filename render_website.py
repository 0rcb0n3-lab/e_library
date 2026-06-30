import argparse
import json
import math
import os

from functools import partial
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked
from urllib.parse import quote


def quote_url_path(path):
    return quote(str(path), safe='/')


def load_books_data(metadata_path):
    """Загружает данные о книгах из JSON файла."""
    with open(metadata_path, 'r', encoding='utf-8') as file:
        books_data = json.load(file)
    return books_data


def parse_genres(genres_string):
    """Преобразует строку с жанрами в очищенный список."""
    return [
        genre.strip()
        for genre in genres_string.replace('.', ',').split(',')
        if genre.strip()
    ]


def get_page_links(page_num, total_pages):
    """Вычисляет относительные ссылки на предыдущую и следующую страницы."""
    if page_num == 1:
        prev_link = None
        next_link = 'pages/index2.html' if total_pages > 1 else None
    else:
        prev_link = '../index.html' if page_num == 2 else f'index{page_num-1}.html'
        next_link = f'index{page_num+1}.html' if page_num < total_pages else None
    return prev_link, next_link


def get_page_routing(page_num, total_pages):
    """Возвращает имя целевого HTML-файла, статический префикс и карту всех URL."""
    if page_num == 1:
        filename = 'index.html'
        static_prefix = ''
        page_urls = ['index.html'] + [f'pages/index{i}.html' for i in range(2, total_pages + 1)]
    else:
        filename = os.path.join('pages', f'index{page_num}.html')
        static_prefix = '../'
        page_urls = ['../index.html'] + [f'index{i}.html' for i in range(2, total_pages + 1)]
    return filename, static_prefix, page_urls


def get_pages(metadata_path, books_per_page):
    """Формирует структуру страниц и правильные относительные ссылки."""
    books = load_books_data(metadata_path)
    for book in books:
        book['genres_list'] = parse_genres(book['genres'])

    chunks = list(chunked(books, books_per_page))
    total_pages = math.ceil(len(books) / books_per_page)

    pages = []
    for page_num, book_group in enumerate(chunks, start=1):
        prev_link, next_link = get_page_links(page_num, total_pages)
        pages.append({
            'books': book_group,
            'current_page': page_num,
            'total_pages': total_pages,
            'prev_link': prev_link,
            'next_link': next_link
        })
    return pages


def create_jinja_env():
    """Создает и настраивает окружение Jinja2 для рендеринга шаблонов."""
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml']),
    )
    env.filters['urlquote'] = quote_url_path
    return env


def on_reload(metadata_path, books_per_page):
    """Рендерит HTML-страницы на основе шаблона Jinja2."""
    env = create_jinja_env()
    template = env.get_template('template.html')
    pages = get_pages(metadata_path, books_per_page)

    for page in pages:
        page_num = page['current_page']
        total_pages = page['total_pages']
        filename, static_prefix, page_urls = get_page_routing(page_num, total_pages)

        rendered_page = template.render(
            books_rows=list(chunked(page['books'], 2)),
            current_page=page_num,
            total_pages=total_pages,
            prev_link=page['prev_link'],
            next_link=page['next_link'],
            page_urls=page_urls,
            static_prefix=static_prefix
        )

        with open(filename, 'w', encoding='utf8') as file:
            file.write(rendered_page)


def parse_cli_arguments():
    """Конфигурирует парсер и возвращает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description='Генератор статического сайта книжной библиотеки.'
    )
    parser.add_argument(
        '-db', '--data_base',
        type=str,
        default='meta_data.json',
        help='Путь к JSON-файлу с базой книг (по умолчанию: meta_data.json)'
    )
    parser.add_argument(
        '-bp', '--books_on_page',
        type=int,
        default=10,
        help='Количество книг на одной странице (по умолчанию: 10)'
    )
    return parser.parse_args()


def main():
    """Основная точка входа в программу."""
    args = parse_cli_arguments()
    os.makedirs('pages', exist_ok=True)

    reload_callback = partial(on_reload, args.data_base, args.books_on_page)
    reload_callback()

    server = Server()
    server.watch('template.html', reload_callback)
    server.watch(args.data_base, reload_callback)
    server.serve(root='.', default_filename='index.html')


if __name__ == '__main__':
    main()
