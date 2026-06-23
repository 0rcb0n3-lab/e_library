import json
import math
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def load_books_data():
    with open('meta_data.json', 'r', encoding='utf-8') as file:
        books_data = json.load(file)
    return books_data


def get_pages():
    books = load_books_data()
    books_per_page = 10
    chunks = list(chunked(books, books_per_page))
    total_pages = math.ceil(len(books) / books_per_page)
    pages = []
    for page_num, book_group in enumerate(chunks, start=1):
        prev_page = f"index{page_num-1}.html" if page_num > 1 else None
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
        filename = os.path.join('pages', f"index{page['current_page']}.html")

        pages_numbers = list(range(1, page['total_pages'] + 1))

        rendered_page = template.render(
            books_rows=books_rows,
            current_page=page['current_page'],
            total_pages=page['total_pages'],
            prev_link=page['prev_link'],
            next_link=page['next_link'],
            pages_numbers=pages_numbers,
        )
        with open(filename, 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    os.makedirs('pages', exist_ok=True)

    on_reload()

    server = Server()

    server.watch('template.html', on_reload)
    server.watch('meta_data.json', on_reload)
    server.serve(root='.', default_filename='pages/index1.html')
