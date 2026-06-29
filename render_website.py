import json
import math
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def load_books_data():
    """Загружает данные о книгах из JSON файла."""
    with open('meta_data.json', 'r', encoding='utf-8') as file:
        books_data = json.load(file)
    return books_data


def get_pages():
    """Формирует структуру страниц и правильные относительные ссылки."""
    books = load_books_data()
    for book in books:
        book['genres_list'] = [
            genre.strip()
            for genre in book['genres'].replace('.', ',').split(',')
            if genre.strip()
        ]

    books_per_page = 10
    chunks = list(chunked(books, books_per_page))
    total_pages = math.ceil(len(books) / books_per_page)

    pages = []
    for page_num, book_group in enumerate(chunks, start=1):
        # Относительные ссылки для работы без сервера (оффлайн и GitHub Pages)
        if page_num == 1:
            prev_page = None
            next_page = "pages/index2.html" if total_pages > 1 else None
        else:
            prev_page = "../index.html" if page_num == 2 else f"index{page_num-1}.html"
            next_page = f"index{page_num+1}.html" if page_num < total_pages else None

        pages.append({
            'books': book_group,
            'current_page': page_num,
            'total_pages': total_pages,
            'prev_link': prev_page,
            'next_link': next_page
        })
    return pages


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')
    pages = get_pages()

    for page in pages:
        books_rows = list(chunked(page['books'], 2))
        page_num = page['current_page']
        total_pages = page['total_pages']

        # Вычисляем префикс для выхода из папки pages/ на уровень корня
        if page_num == 1:
            filename = "index.html"
            static_prefix = ""  # Главная страница в корне
            page_urls = ["index.html"] + [f"pages/index{i}.html" for i in range(2, total_pages + 1)]
        else:
            filename = os.path.join('pages', f"index{page_num}.html")
            static_prefix = "../"  # Страницы каталога внутри папки pages/
            page_urls = ["../index.html"] + [f"index{i}.html" for i in range(2, total_pages + 1)]

        rendered_page = template.render(
            books_rows=books_rows,
            current_page=page_num,
            total_pages=total_pages,
            prev_link=page['prev_link'],
            next_link=page['next_link'],
            page_urls=page_urls,
            static_prefix=static_prefix  # Относительный путь до корня сайта
        )

        with open(filename, 'w', encoding="utf8") as file:
            file.write(rendered_page)


def main():
    """Основная точка входа в программу."""
    os.makedirs('pages', exist_ok=True)

    # Генерация статического сайта
    on_reload()

    # Запуск локального сервера разработки
    server = Server()
    server.watch('template.html', on_reload)
    server.watch('meta_data.json', on_reload)
    server.serve(root='.', default_filename='index.html')


if __name__ == '__main__':
    main()
