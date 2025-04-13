import os
from flask import Flask, request, render_template, redirect, url_for, send_file
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
from io import BytesIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB

# Azure setup
account_name = os.environ.get('AZURE_STORAGE_ACCOUNT')
container_name = os.environ.get('AZURE_CONTAINER_NAME')

try:
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=credential
    )
    container_client = blob_service_client.get_container_client(container_name)
except Exception as e:
    print(f"Azure client init error: {e}")
    container_client = None

@app.route('/')
def index():
    return render_template('index.html', error=None)

@app.route('/upload', methods=['POST'])
def upload():
    if not container_client:
        return render_template("index.html", error="Storage is unavailable")

    if 'file' not in request.files:
        return render_template("index.html", error="No file part in request")

    file = request.files['file']
    if file.filename == '':
        return render_template("index.html", error="No file selected")

    try:
        blob_client = container_client.get_blob_client(file.filename)
        blob_client.upload_blob(file, overwrite=True)
        return redirect(url_for('index'))
    except Exception as e:
        return render_template("index.html", error=f"Upload error: {e}")

@app.route('/get-download-url/<filename>', methods=['GET'])
def get_download_url(filename):
    if not container_client:
        return f"Storage is unavailable", 503

    try:
        blob_client = container_client.get_blob_client(blob=filename)
        downloader = blob_client.download_blob()
        stream = BytesIO()
        downloader.readinto(stream)
        stream.seek(0)
        return send_file(stream, download_name=filename, as_attachment=True)
    except Exception as e:
        return f"Download error: {e}", 500

@app.route('/list')
def list_files():
    try:
        if not container_client:
            return render_template("index.html", error="Storage is unavailable")
        blob_names = [blob.name for blob in container_client.list_blobs()]
        return render_template("index.html", blob_names=blob_names)
    except Exception as e:
        return render_template("index.html", error=f"Listing error: {e}")

@app.route('/delete', methods=['POST'])
def delete_file():
    file_name = request.form.get("file_name")
    if not file_name:
        return render_template("index.html", error="No file name provided")

    try:
        container_client.get_blob_client(blob=file_name).delete_blob()
        return redirect(url_for('index'))
    except Exception as e:
        return render_template("index.html", error=f"Delete error: {e}")

@app.route('/delete-all', methods=['POST'])
def delete_all():
    if not container_client:
        return render_template("index.html", error="Storage is unavailable")

    try:
        for blob in container_client.list_blobs():
            container_client.get_blob_client(blob.name).delete_blob()
        return redirect(url_for('index'))
    except Exception as e:
        return render_template("index.html", error=f"Delete all error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
