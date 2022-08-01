import os
import argparse
import json
import requests


# step 1: register a project to google cloud and get the following information
os.environ['CLIENT_ID'] = '602199020484-0j3lsgjcpug42qbu7cklt40n6mhpdrcn.apps.googleusercontent.com'
os.environ['CLIENT_SECRET'] = 'SRkzogXA_uvtDUZJLPKtbCnu'
# step 2: register the machine where the files are locataed to be loaded to google drive
# curl -d "client_id=<CLIENT_ID>&scope=https://www.googleapis.com/auth/drive.file" https://oauth2.googleapis.com/device/code
# which returns
# {
#   "device_code": "",
#   "user_code": "",
#   "expires_in": 1800,
#   "interval": 5,
#   "verification_url": "https://www.google.com/device"
# }
# go to verification_url and insert the user_code to complete registering the machine
# step 3: get the authentication code using the device code from step 2
# curl -d client_id=<CLIENT_ID> -d client_secret=<CLIENT_SECRET> -d device_code=<DEVICE_CODE> -d grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code https://accounts.google.com/o/oauth2/token
# which returns
# {
#   "access_token": "",
#   "expires_in": 3599,
#   "refresh_token": "",
#   "scope": "https://www.googleapis.com/auth/drive.file",
#   "token_type": "Bearer"
# }
# access_token expires in an hour, however refresh_token can be used to obtain access token before each upload
# refresh_token can be used up to 200 days, at which point another access token has to be obtained
os.environ['REFRESH_TOKEN'] = '1//0dWx3QYOVuSNUCgYIARAAGA0SNwF-L9IrCD67bTAw6Odql8kZOwg59z6MBv-9qfZO1McJorVHSo_WAbUlYZ0EoaDbK1cN33Sen90'
# step 4: create a folder where the uploaded file should go to, get the id
os.environ['FOLDER_ID'] = '1H0yADQXKCJr0ZvFfPMo7_bv_IvZVCQIw'

def upload_file(filename):
    """

    :param filename: csv filename
    :return:
    """
    # get access token
    try:
        payload = {
            "client_id": os.environ['CLIENT_ID'],
            "client_secret": os.environ['CLIENT_SECRET'],
            "refresh_token": os.environ['REFRESH_TOKEN'],
            "grant_type": "refresh_token"
        }
        headers = { 'grant_type': 'authorization_code', 'Content-Type': 'application/json'}
        response = requests.request("POST", "https://www.googleapis.com/oauth2/v4/token", headers=headers, data=json.dumps(payload))
        access_token = json.loads(response.text.encode('utf8'))['access_token']
    except:
        print('Unable to get access token! File not uploaded.')
        return

    # upload the file to docmatch_QA
    param = {
        "name": os.path.basename(filename),
        "parents": [os.environ['FOLDER_ID']],
        "mimeType": "application/vnd.google-apps.spreadsheet"
    }
    files = {
        'data': ('metadata', json.dumps(param), 'application/json; charset=UTF-8'),
        'file': open(filename, "rb")
    }
    headers = {"Authorization": "Bearer %s"%access_token, "contentType": "application/vnd.ms-excel"}
    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    response = requests.post(url, headers=headers, files=files)
    print('Status of uploading "%s" to google:'%filename)
    print(response.text)

# need the following four environment variables as explained above
# CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, FOLDER_ID
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match arXiv with Publisher')
    parser.add_argument('-f', '--filename', help='csv file to upload to google.')
    args = parser.parse_args()
    if args.filename:
        upload_file(filename=args.filename)
