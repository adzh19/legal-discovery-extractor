from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth

def get_box_client(token: str) -> BoxClient:
    auth = BoxDeveloperTokenAuth(token=token)
    return BoxClient(auth=auth)