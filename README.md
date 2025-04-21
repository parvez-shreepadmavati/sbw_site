# 🚀 My Django Project
```
A web application built with **Django 5.1.7** and **Python 3.12.3**.  
Supports real-time data exchange via **Socket.IO**, API integrations, and secure CSRF configurations.
```
---

## 📑 Features
```
- Django 5.1.7 based backend
- Real-time data handling via Socket.IO (without `django-socketio`)
- CSRF protection and trusted origins management via `.env`
- API endpoints for external applications
- Dynamic settings management via environment variables
```
---

## 📦 Project Structure

```
my_django_project/
├── manage.py
├── my_django_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── ...
├── apps/
│   └── your_apps/
├── templates/
├── static/
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/your-django-project.git
cd your-django-project
```

### 2️⃣ Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Setup environment variables

Create a `.env` file in your project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://your-ngrok-url.ngrok-free.app
DATABASE_URL=sqlite:///db.sqlite3
```

> ⚠️ Replace `CSRF_TRUSTED_ORIGINS` value with your actual public URL if using ngrok.

---

## 🚀 Running the project

```bash
python manage.py migrate
python manage.py runserver
```

To run with **Socket.IO** via `daphne` or `uvicorn` (if using ASGI setup):

```bash
daphne -b 0.0.0.0 -p 8000 my_django_project.asgi:application
```

or

```bash
uvicorn my_django_project.asgi:application --host 0.0.0.0 --port 8000
```

---

## 📡 Real-time Socket.IO (if implemented)
```
- ASGI integration ready
- Socket.IO endpoints available at `/ws/`
```
---

## 📌 Environment Variables (via `.env`)
```
| Key                     | Description                          | Example                               |
|:------------------------|:--------------------------------------|:--------------------------------------|
| `DEBUG`                 | Run server in debug mode              | `True`                                |
| `SECRET_KEY`            | Django secret key                     | `random-string`                       |
| `ALLOWED_HOSTS`         | Allowed hosts for deployment          | `127.0.0.1,localhost`                 |
| `CSRF_TRUSTED_ORIGINS`  | Comma-separated list of trusted URLs  | `https://xxxx.ngrok-free.app`         |
| `DATABASE_URL`          | Database connection string            | `sqlite:///db.sqlite3`                |
```
---

## 📖 License
```
This project is licensed under the MIT License.
```
---

## ✨ Author

[Parvez Khan Pathan](https://github.com/iamParvezKhan25)

---

## 📬 Feedback

Found a bug or have a feature request? Feel free to [open an issue](https://github.com/yourusername/your-django-project/issues).

