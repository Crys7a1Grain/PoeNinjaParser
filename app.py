import tkinter as tk
from tkinter import messagebox
import requests
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import io

image_refs = []


def fetch_data_from_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем успешность запроса
        return response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching data: {e}")
        return None


def fetch_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем успешность запроса
        return Image.open(io.BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching image: {e}")
        return None


def display_page(replica_items, text_area, page_num, total_pages):
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)  # Очистка текстовой области
    start_idx = page_num * 10
    end_idx = start_idx + 10
    items_to_display = replica_items[start_idx:end_idx]

    if items_to_display:
        text_area.insert(tk.END, f"Page {page_num + 1} of {total_pages}\n\n")
        for item in items_to_display:
            icon_url = item['icon']
            icon_image = fetch_image_from_url(icon_url)
            if icon_image:
                icon_image.thumbnail((50, 50))
                icon = ImageTk.PhotoImage(icon_image)
                text_area.image_create(tk.END, image=icon)
                text_area.insert(tk.END, "\n")  # Новый ряд для текста
                text_area.insert(tk.END, f"Item: {item['name']}\n")
                text_area.insert(
                    tk.END, f"  Chaos Value: {item['chaosValue']}\n")
                text_area.insert(
                    tk.END, f"  Divine Value: {item['divineValue']}\n\n")
                text_area.image_ref = icon  # Ссылка на изображение, чтобы не собиралось GC
                image_refs.append(icon)
            else:
                text_area.insert(tk.END, "Item wasn't loaded.")
    else:
        text_area.insert(tk.END, "No Replica items found.")

    text_area.config(state=tk.DISABLED)


def filter_and_display_replica_items(items, text_area, page_size, page_var, total_pages_var, page_buttons_frame, nav_buttons_frame):
    global replica_items  # Чтобы использовать в go_to_page

    if 'lines' in items:
        replica_items = [item for item in items['lines']
                         if item['name'].startswith("Replica")]

        total_pages = (len(replica_items) + page_size - 1) // page_size
        total_pages_var.set(total_pages)

        current_page = page_var.get()
        if current_page >= total_pages:
            current_page = total_pages - 1
            page_var.set(current_page)

        display_page(replica_items, text_area, current_page, total_pages)

        # Обновляем кнопки пагинации после фильтрации данных
        update_page_buttons(replica_items, page_var, text_area,
                            total_pages_var, page_buttons_frame)

        # Обновляем навигационные кнопки после фильтрации данных
        update_nav_buttons(page_var, total_pages_var,
                           nav_buttons_frame, text_area)

        return replica_items
    else:
        messagebox.showerror(
            "Error", "Unexpected data format received from API.")
        return []


def update_page_buttons(replica_items, page_var, text_area, total_pages_var, page_buttons_frame):
    for widget in page_buttons_frame.winfo_children():
        widget.destroy()

    total_pages = total_pages_var.get()
    current_page = page_var.get()

    if total_pages > 1:
        for i in range(total_pages):
            button = tb.Button(page_buttons_frame, text=f"{i + 1}",
                               command=lambda i=i: go_to_page(
                                   i, page_var, text_area, replica_items, total_pages_var),
                               bootstyle="info-outline")
            button.grid(row=0, column=i, padx=2)


def update_nav_buttons(page_var, total_pages_var, nav_buttons_frame, text_area):
    for widget in nav_buttons_frame.winfo_children():
        widget.destroy()

    prev_button = tb.Button(nav_buttons_frame, text="Previous",
                            command=lambda: go_to_page(
                                max(page_var.get() - 1, 0), page_var, text_area, replica_items, total_pages_var),
                            bootstyle="primary")
    prev_button.grid(row=0, column=0, padx=5)

    next_button = tb.Button(nav_buttons_frame, text="Next",
                            command=lambda: go_to_page(min(page_var.get(
                            ) + 1, total_pages_var.get() - 1), page_var, text_area, replica_items, total_pages_var),
                            bootstyle="primary")
    next_button.grid(row=0, column=1, padx=5)


def on_fetch_click(text_area, page_size, page_var, total_pages_var, page_buttons_frame, nav_buttons_frame):
    # Замените на реальный URL API
    api_url = "https://poe.ninja/api/data/itemoverview?league=Necropolis&type=UniqueWeapon"
    data = fetch_data_from_api(api_url)
    if data:
        return filter_and_display_replica_items(data, text_area, page_size, page_var, total_pages_var, page_buttons_frame, nav_buttons_frame)
    else:
        return []


def go_to_page(page_num, page_var, text_area, replica_items, total_pages_var):
    page_var.set(page_num)
    display_page(replica_items, text_area, page_num, total_pages_var.get())


def draw_window():
    # Создание главного окна с использованием ttkbootstrap
    root = tb.Window(themename="superhero")  # Используем тему 'darkly'
    root.title("POE Ninja Replica Fetcher")
    root.geometry("800x600")

    page_var = tk.IntVar(value=0)
    page_size = 10
    total_pages_var = tk.IntVar(value=1)

    # Создание фрейма ввода
    frame = tb.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Создание текстовой области для отображения данных
    text_area = tb.Text(frame, wrap=tk.WORD, width=90,
                        height=25, font=("Arial", 10))
    text_area.grid(row=1, column=0, columnspan=3,
                   sticky=(tk.W, tk.E, tk.N, tk.S))

    # Создание прокрутки
    scrollbar = tb.Scrollbar(frame, orient=tk.VERTICAL,
                             command=text_area.yview)
    scrollbar.grid(row=1, column=3, sticky=(tk.N, tk.S))

    # Привязка прокрутки к текстовой области
    text_area.config(yscrollcommand=scrollbar.set)

    # Добавление кнопки
    fetch_button = tb.Button(frame, text="Fetch Data",
                             command=lambda: on_fetch_click(
                                 text_area, page_size, page_var, total_pages_var, page_buttons_frame, nav_buttons_frame),
                             bootstyle="success")
    fetch_button.grid(row=0, column=0, pady=10)

    # Создание фрейма для кнопок страниц
    page_buttons_frame = tb.Frame(frame)
    page_buttons_frame.grid(row=2, column=2, pady=10, sticky=(tk.W, tk.E))

    # Создание фрейма для навигационных кнопок
    nav_buttons_frame = tb.Frame(frame)
    nav_buttons_frame.grid(row=2, column=0, pady=10,
                           columnspan=2, sticky=(tk.W, tk.E))

    # Запуск главного цикла обработки событий
    root.mainloop()


def main():
    draw_window()


# Пример использования
if __name__ == "__main__":
    main()
