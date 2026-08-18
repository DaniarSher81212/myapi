from flask import Flask, request, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

API_KEY = os.getenv("MYAPI_API_KEY")

def auth():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Forbidden"}), 403
    return None

# ============================================================
# Базовые папки проекта
# ============================================================

BASE_DIR = "/home/ubuntu/filehub/data"

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")

# Создаём папки, если их нет
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


# ============================================================
# Проверка работы API
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "filehub"
    })


# ============================================================
# Главная страница
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return """
    <h2>FileHub API is working</h2>
    <ul>
        <li><a href="/health">/health</a></li>
        <li><a href="/files">/files</a></li>
    </ul>
    """


# ============================================================
# Загрузка файла на сервер
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():
    e = auth()
    if e: return e

    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file field in request"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "status": "error",
            "message": "Empty filename"
        }), 400

    safe_name = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, safe_name)

    file.save(save_path)

    return jsonify({
        "status": "uploaded",
        "filename": safe_name,
        "path": save_path
    })


# ============================================================
# Список файлов
# ============================================================

@app.route("/files", methods=["GET"])
def files():
    e = auth()
    if e: return e

    return jsonify({
        "uploads": os.listdir(UPLOAD_DIR),
        "output": os.listdir(OUTPUT_DIR),
        "temp": os.listdir(TEMP_DIR),
        "archive": os.listdir(ARCHIVE_DIR)
    })

# ============================================================
# Скачать файл из выбранной серверной папки
# Разрешены только безопасные папки FileHub
# ============================================================

@app.route("/download/<folder>/<filename>", methods=["GET"])
def download_from_folder(folder, filename):
    e = auth()
    if e: return e

    allowed_dirs = {
        "uploads": UPLOAD_DIR,
        "output": OUTPUT_DIR,
        "temp": TEMP_DIR,
        "archive": ARCHIVE_DIR
    }

    if folder not in allowed_dirs:
        return jsonify({
            "status": "error",
            "message": "Folder is not allowed",
            "folder": folder
        }), 400

    safe_name = secure_filename(filename)
    target_dir = allowed_dirs[folder]

    file_path = os.path.join(target_dir, safe_name)

    if not os.path.exists(file_path):
        return jsonify({
            "status": "error",
            "message": "File not found",
            "folder": folder,
            "filename": safe_name
        }), 404

    return send_from_directory(
        target_dir,
        safe_name,
        as_attachment=True
    )


# ============================================================
# Тестовая обработка файла
# uploads -> output
# ============================================================

@app.route("/process/<filename>", methods=["POST", "GET"])
def process_file(filename):
    e = auth()
    if e: return e

    safe_name = secure_filename(filename)

    src = os.path.join(UPLOAD_DIR, safe_name)
    dst = os.path.join(OUTPUT_DIR, "processed_" + safe_name)

    if not os.path.exists(src):
        return jsonify({
            "status": "error",
            "message": "File not found in uploads",
            "filename": safe_name
        }), 404

    with open(src, "rb") as f_in:
        data = f_in.read()

    with open(dst, "wb") as f_out:
        f_out.write(data)

    return jsonify({
        "status": "processed",
        "input": safe_name,
        "output": "processed_" + safe_name
    })


# ============================================================
# Запуск Flask
# ============================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
