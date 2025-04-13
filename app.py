import os
from flask import Flask, request, render_template, redirect, url_for
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import AzureError
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB

# Fetch Storage Account & Container Name from environment
account_name = os.environ.get('AZURE_STORAGE_ACCOUNT')
container_name = os.environ.get('AZURE_CONTAINER_NAME')

# Use Managed Identity to authenticate
try:
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=credential
    )
    container_client = blob_service_client.get_container_client(container_name)
except AzureError as e:
    print(f"Error initializing Azure Blob client: {e}")
    container_client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if not container_client:
        return "Storage is currently unavailable", 503

    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    try:
        blob_client = container_client.get_blob_client(file.filename)
        blob_client.upload_blob(file, overwrite=True)
        return redirect(url_for('index'))
    except AzureError as e:
        print(f"Upload failed: {e}")
        return "File upload failed due to storage error", 500

def get_blob_names():
    if not container_client:
        return []
    return [blob.name for blob in container_client.list_blobs()]

@app.route('/list')
def list_files():
    try:
        blob_names = get_blob_names()
        return render_template('list.html', blob_names=blob_names)
    except AzureError as e:
        print(f"List failed: {e}")
        return "Failed to list blobs", 500

def delete_blob(blob_name):
    if container_client:
        container_client.get_blob_client(blob_name).delete_blob()

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        file_name = request.form['file_name']
        try:
            delete_blob(file_name)
        except AzureError as e:
            print(f"Delete failed: {e}")
            return "Delete operation failed", 500
        return redirect(url_for('list_files'))
    return render_template('delete.html')

@app.route('/delete-all', methods=['POST'])
def delete_all():
    if not container_client:
        return "Storage is currently unavailable", 503

    try:
        for blob in container_client.list_blobs():
            delete_blob(blob.name)
        return redirect(url_for('index'))
    except AzureError as e:
        print(f"Delete all failed: {e}")
        return "Failed to delete all blobs", 500

@app.route('/get-download-url/<filename>')
def get_download_url(filename):
    if not container_client:
        return
