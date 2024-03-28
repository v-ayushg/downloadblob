from flask import Flask, request, render_template
from azure.storage.blob import BlobServiceClient
 
app = Flask(__name__)
 
# Replace these with your Azure Storage account credentials
account_name = 'agstorage2'
account_key = 'KCufE/vbkNoL+6PqaFXM4z7JBSm6KV7do2LX35QVoXsxHrHCnnd0L1jBnPmzR0L9KGdyQszf6Dqb+ASt10jRGw=='
container_name = 'uploadblob'
 
# Create a BlobServiceClient
blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
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
    
    return 'File uploaded successfully'


# Function to get all file names from Azure Blob Storage
def get_blob_names():
    blob_names = []
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        blob_names.append(blob.name)
    return blob_names

# Route to display file names
@app.route('/list')
def list():
    blob_names = get_blob_names()
    return render_template('list.html', blob_names=blob_names)
 
if __name__ == '__main__':
    app.run(debug=True)