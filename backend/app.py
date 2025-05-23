import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
import os
import requests
import logging
import uuid


from dotenv import load_dotenv

load_dotenv()

# Flask setup
app = Flask(__name__, static_folder="uploaded_files")
CORS(app)

log_file_path = os.path.join(os.path.dirname(__file__), "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()  # Optional: also logs to console
    ]
)

# Azure Storage setup
UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Environment variables for Azure
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
BACKEND_URL=os.getenv("BACKEND_URL")

# Initialize Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def parse_connection_string(conn_str):
    parts = dict(x.split('=', 1) for x in conn_str.split(';') if x)
    print(parts)
    return parts['AccountName'], parts['AccountKey']
# Function to generate SAS URL
account_name, account_key = parse_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def generate_sas_url(blob_name):
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=AZURE_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
        content_disposition='inline'  # Ensures browser tries to open, not download
    )

    return f"https://{account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files['file']
    original_filename = file.filename.rsplit('.', 1)[0]
    unique_id = str(uuid.uuid4())
    new_filename = f"{original_filename}_{unique_id}.docx"
    logging.info("Initiated")
    if not file.filename.endswith('.docx'):
        return jsonify({"error": "Invalid file"}), 400
    container_client = blob_service_client.get_container_client(os.getenv("AZURE_CONTAINER_NAME"))
    blob_client = container_client.get_blob_client(new_filename)
    logging.info(blob_client)

    # Save with correct content-type
    blob_client.upload_blob(
        file,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    )

    # Generate SAS URL (assuming you already have the logic for that)
    sas_url = generate_sas_url(new_filename)
    logging.info(sas_url)

    return jsonify({
        "filename": new_filename,
        "file_url": sas_url
    })

@app.route("/files/<filename>")
def serve_file(filename):
    # Serve the file from the local upload directory (you might need to adapt this part based on your requirement)
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/onlyoffice-config", methods=["POST"])
def onlyoffice_config():
    data = request.json
    filename = data['filename']
    file_url = data['file_url'] # SAS for viewing/editing

    config = {
        "document": {
            "fileType": "docx",
            "key": filename,  # Can add timestamp or hash if needed
            "title": filename,
            "url": file_url,
        },
        "documentType": "word",
        "editorConfig": {
            "user": { "id": "u1", "name": "Test User" },
            "callbackUrl": f"{BACKEND_URL}/save/{filename}",
            "customization": {
                "autosave": True,
                "logo": {
                    "image": "https://i.ibb.co/4ncgp8Q6/image.png",
                    "imageDark": "https://i.ibb.co/4ncgp8Q6/image.png",
                    "imageLight": "https://i.ibb.co/4ncgp8Q6/image.png",
                    "url": "http://20.109.20.242:4000/dashboard",
                    "visible": True,
                },
                "forcesave": True
            }
        }
    }
    return jsonify(config)


@app.route("/save/<filename>", methods=["POST"])
def save_file(filename):
    data = request.json
    logging.info("Callback data:\n" + json.dumps(data, indent=2))
    print("Callback data:\n" + json.dumps(data, indent=2))

    status = data.get("status")
    download_uri = data.get("url")

    if not download_uri:
        logging.error("No URL provided in the callback data.")
        return jsonify({"error": 1})

    if status == 2:
        logging.info(f"Autosave triggered for {filename}. Proceeding with file download and upload.")
        try:
            r = requests.get(download_uri)
            r.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to download file: {e}")
            return jsonify({"error": 1})

        file_bytes = r.content

        try:
            container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(
                file_bytes,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            )
        except Exception as e:
            logging.error(f"Error uploading to blob: {e}")
            return jsonify({"error": 1})

        return jsonify({"error": 0})

    elif status == 6:
        logging.info(f"Manual save triggered for {filename}. Proceeding with file download and upload.")
        try:
            r = requests.get(download_uri)
            r.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to download file: {e}")
            return jsonify({"error": 1})

        file_bytes = r.content

        try:
            container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(
                file_bytes,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            )
        except Exception as e:
            logging.error(f"Error uploading to blob: {e}")
            return jsonify({"error": 1})

        return jsonify({"error": 0})

    # Gracefully handle other statuses like 1, 3, 4, etc.
    logging.info(f"Received status {status}, no action required.")
    return jsonify({"error": 0})

if __name__ == '__main__':
    print("bkc")
    app.run(host="0.0.0.0", port=6006)
