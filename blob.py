from azure.storage.blob import BlobServiceClient
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# main function to upload all files in directory to blob storage, incl. metadata
async def uploadToBlob(directory: Path):
    # load environment variables from .env
    load_dotenv()
    # get connection string from environment
    connectionString = os.environ['AZURE_STORAGE_CONNECTION_STRING']
    # get container name from environment (default: 'webscraper')
    containerName = os.environ.get('AZURE_CONTAINER_NAME', 'webscraper')
    # connect to blob storage using connection string
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    containerClient = blobServiceClient.get_container_client(containerName)
    # open metadata json
    metadataFile = json.loads(open(directory / 'metadata.json').read())

    # iterate through all files in directory
    for filePath in directory.glob('**/*'):
        if filePath.is_file() and filePath.name != 'metadata.json':
            # get metadata for file
            fileID = filePath.name.split('.')[0]
            metadataDict = getMetadata(metadataFile, fileID)
            # create blob path: session_timestamp/relative_path
            relativePath = filePath.relative_to(directory)
            blobPath = f"{directory.name}/{relativePath}"
            blobClient = containerClient.get_blob_client(blobPath)
            # upload file including metadata
            with open(filePath, 'rb') as data:
                try:
                    blobClient.upload_blob(data, metadata=metadataDict)
                    print(f'Uploaded {filePath.name}')
                except Exception as e:
                    print(f'Error uploading {filePath.name}', e)
    
# get metadata for file
def getMetadata(data, targetID):
    # recursively search list metadata for targetID
    if isinstance(data, list):
        for item in data:
            result = getMetadata(item, targetID)
            if result:
                return result
    # recursively dictionary metadata for targetID
    elif isinstance(data, dict):
        # if ID matches targetID, construct & return metadataDict
        if data.get("ID") == targetID:
            metadataDict = {'ID': data.get('ID'),
                            'TIMESTAMP': str(data.get('TIMESTAMP')),
                            'TYPE': data.get('TYPE'),
                            'URL': data.get('URL'),
                            'TIER': str(data.get('TIER')),
                            'TITLE': cleanMetadataText(data.get('TITLE')),
                            'PARENT': data.get('PARENT') if data.get('PARENT') is not None else 'None'}
            return metadataDict
        # iterate over metadata
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                result = getMetadata(value, targetID)
                if result:
                    return result
    return None

# clean up text to conform with required encoding (ASCII) for blob storage metadata
def cleanMetadataText(text: str):
    # replacements for unicode characters to conform with ASCII encoding
    replacements = {
        '\u2018': "'",  # left single quotation mark
        '\u2019': "'",  # right single quotation mark
        '\u201C': '"',  # left double quotation mark
        '\u201D': '"',  # right double quotation mark
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u2026': '...',  # ellipsis
        '\u00A9': '(c)',  # copyright sign
        '\u00AE': '(r)',  # registered trademark sign
        '\u2122': '(tm)',  # trademark sign
    }
    # if text can be encoded in ASCII, return text
    try: 
        text.encode('ascii')
        return text
    # if encoding in ASCII fails, unicode characters are replaced
    except UnicodeEncodeError:
        return ''.join(replacements.get(char, '_') if char.encode('ascii', 'ignore') == b'' else char for char in text)