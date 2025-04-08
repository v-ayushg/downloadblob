import os
from flask import Flask, flash, request, render_template, redirect, url_for
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB

# Fetch Azure Storage account credentials from environment variables
account_name = os.environ.get('AZURE_STORAGE_ACCOUNT')
account_key = os.environ.get('AZURE_STORAGE_KEY')
container_name = os.environ.get('AZURE_CONTAINER_NAME')

# Create a BlobServiceClient
blob_service_client = BlobServiceClient(
    account_url=f"https://{account_name}.blob.core.windows.net", 
    credential=account_key
)
container_client = blob_service_client.get_container_client(container_name)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    # Upload file to Azure Blob Storage
    blob_client = container_client.get_blob_client(file.filename)
    blob_client.upload_blob(file)

    # flash('File uploaded successfully', 'success')
    return redirect((url_for('index')))
    


# Function to get all file names from Azure Blob Storage
def get_blob_names():
    return [blob.name for blob in container_client.list_blobs()]

# Route to display file names
@app.route('/list')
def list_files():
    blob_names = get_blob_names()
    return render_template('list.html', blob_names=blob_names)

# Function to delete a file from Azure Blob Storage
def delete_blob(blob_name):
    container_client.get_blob_client(blob_name).delete_blob()

# Route to delete a file
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        file_name = request.form['file_name']
        delete_blob(file_name)
        return redirect(url_for('list_files'))
    return render_template('delete.html')

# Route to delete all files
@app.route('/delete-all', methods=['POST'])
def delete_all():
    for blob in container_client.list_blobs():
        delete_blob(blob.name)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
