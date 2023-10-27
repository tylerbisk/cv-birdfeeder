import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
import datetime


def upload_to_youtube(client_secret_file, api_name, api_version, filename,
                      title, *scopes):
    scopes = [scope for scope in scopes[0]]

    cred = None

    pickle_file = f'token_{api_name}_{api_version}.pickle'
    # print(pickle_file)

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, scopes)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(api_name, api_version, credentials=cred)

        # set to past to upload now
        upload_date_time = datetime.datetime(2000, 1, 1, 12, 00,
                                             0).isoformat() + '.000Z'

        #education, 28 for tech, and 15 for animals / pets
        request_body = {
            'snippet': {
                'categoryI': 27,
                'title': title,
                'description': 'video of ' + str(title),
                'tags': ['Raspberry Pi', 'Embedded System', 'Computer Vision']
            },
            'status': {
                'privacyStatus': 'public',
                'publishAt': upload_date_time,
                'selfDeclaredMadeForKids': False,
                'embeddable': True,
            },
            'notifySubscribers': False
        }

        mediaFile = MediaFileUpload(filename)

        response = service.videos().insert(part='snippet,status',
                                           body=request_body,
                                           media_body=mediaFile).execute()

        return response
    except Exception as e:
        print('Unable to connect to Youtube')
        print(e)
        return None