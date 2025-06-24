# Электронный документооборот (Django)

![GitHub](https://img.shields.io/github/license/Felitsius/edodjango?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-5.2%2B-green?style=flat-square)

Cистема электронного документооборота (СЭД) на Django для управления документами, их хранения и согласования внутри организации.

## 🔍 Основные возможности
- 📄 Загрузка, хранение документов
- 🔒 Ролевая модель доступа (администраторы, пользователи)
- 📝 Создание шаблонов документов
- 📝 Создание маршрутизации согласования
- 📌 Система согласования документов
- 📊 Cтатистика документооборота

## ⚙️ Технологии
- **Backend**: Django
- **Frontend**: HTML/CSS, JavaScript, Bootstrap
- **База данных**: SQLite

## 🚀 Установка и запуск
### Предварительные требования
- Python 3.12+
- Установленный `pip` и `virtualenv` (рекомендуется)

### Инструкция по развертыванию
1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/Felitsius/edodjango.git
   cd edodjango

2. Создать и активировать виртуальное окружение:
   ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows

3. Установить зависимости:
   ```bash
   pip install -r requirements/base.txt

4. Применить миграции:
   ```bash
   python manage.py makemigrations
   python manage.py migrate

5. Создать суперпользователя:
   ```bash
    python manage.py createsuperuser

6. Запустить сервер:
   ```bash
    python manage.py runserver

## 📧 Контакты
    Telegram: @tungumeteorite

    Email: tungumeteorite@gmail.com
