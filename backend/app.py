import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
import os
import requests
import logging


from dotenv import load_dotenv

load_dotenv()

# Flask setup
app = Flask(__name__, static_folder="uploaded_files")
CORS(app)

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
    logging.info("Initiated")
    if not file.filename.endswith('.docx'):
        return jsonify({"error": "Invalid file"}), 400
    container_client = blob_service_client.get_container_client(os.getenv("AZURE_CONTAINER_NAME"))
    blob_client = container_client.get_blob_client(file.filename)
    logging.info(blob_client)

    # Save with correct content-type
    blob_client.upload_blob(
        file,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    )

    # Generate SAS URL (assuming you already have the logic for that)
    sas_url = generate_sas_url(file.filename)
    logging.info(sas_url)

    return jsonify({
        "filename": file.filename,
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

    file_url = generate_sas_url(filename)  # SAS for viewing/editing

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
            "callbackUrl": f"{BACKEND_URL}/save/{filename}"
        }
    }
    return jsonify(config)


@app.route("/save/<filename>", methods=["POST"])
def save_file(filename):
    data = request.json
    logging.info("Callback data:\n" + json.dumps(data, indent=2))

    status = data.get("status")

    if status == 2:
        # Proceed with file download and upload as before
        try:
            download_uri = data["url"]
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

    # Gracefully handle other statuses like 1, 3, 4, 6, etc.
    logging.info(f"Received status {status}, no action required.")
    return jsonify({"error": 0})

if __name__ == '__main__':
    print("bkc")
    app.run(host="0.0.0.0", port=6006)
