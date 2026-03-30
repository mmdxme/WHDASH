# WHDASH

Flask-based warehouse and inventory dashboard.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`

## Push to GitHub

Your GitHub repo is:

`https://github.com/Mohammadzangard/WHDASH.git`

Run these commands inside the project folder:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/Mohammadzangard/WHDASH.git
git push -u origin main
```

After the push, refresh the GitHub page and confirm the project files are visible.

Note:

- `warehouse.db` is ignored on purpose and will not be pushed to GitHub
- A fresh deployment can build the base SQLite schema automatically from `sqlite_schema.sql`
- If you want your current local data online, upload your existing `warehouse.db` file to the server manually

## Production environment

The app now supports these environment variables:

- `SECRET_KEY`: Flask session key
- `ADMIN_PASSWORD`: password to set for the `admin` user on startup
- `DATABASE_PATH`: path to the SQLite database file
- `UPLOAD_FOLDER`: path for uploaded files
- `PORT`: server port
- `FLASK_DEBUG`: `1` for debug, `0` for production
- `FLASK_RUN_HOST`: host binding, for example `0.0.0.0`

## Deploy on PythonAnywhere

PythonAnywhere is the easiest choice for this project because it works well with Flask and persistent SQLite files.

1. Create a Python web app.
2. Open a Bash console on PythonAnywhere.
3. Clone your repo:

```bash
git clone https://github.com/Mohammadzangard/WHDASH.git
cd WHDASH
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. In the PythonAnywhere WSGI file, use:

```python
import sys
path = '/home/YOUR_USERNAME/WHDASH'
if path not in sys.path:
    sys.path.append(path)

from wsgi import application
```

5. Set environment variables in PythonAnywhere:

- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `DATABASE_PATH=/home/YOUR_USERNAME/WHDASH/warehouse.db`
- `UPLOAD_FOLDER=/home/YOUR_USERNAME/WHDASH/uploads/avatars`

6. Reload the web app.

If you want the same data you have locally, upload your local `warehouse.db` to that path after cloning the repo.

## Deploy on Render or Railway

This repo includes:

- `requirements.txt`
- `Procfile`
- `wsgi.py`

Use the start command:

```bash
gunicorn wsgi:app
```

Important:

- SQLite needs persistent storage
- Do not use temporary filesystem storage for `warehouse.db`
- For bigger production use, migrate to PostgreSQL later
