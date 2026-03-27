import asyncio
import os
import json
from io import BytesIO

async def upload_excel(client, file_path: str , output_folder_id: str ):
    with open(file_path, "rb") as f:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: client.uploads.upload_file(
                {"name": os.path.basename(file_path), "parent": {"id": output_folder_id}},
                file=f
            )
        )

    os.remove(file_path)

async def upload_json_data(client, data: dict, file_name: str, output_folder_id: str):
    """
    Upload JSON data directly to Box without writing to disk.
    
    :param client: Box client
    :param data: Python dict to upload
    :param file_name: Desired file name in Box (e.g., 'report.json')
    :param output_folder_id: Box folder ID to upload into
    """
    # Convert dict to JSON bytes
    json_bytes = json.dumps(data, indent=4).encode("utf-8")
    
    # Use BytesIO to mimic a file
    file_like = BytesIO(json_bytes)
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: client.uploads.upload_file(
            {"name": file_name, "parent": {"id": output_folder_id}},
            file=file_like
        )
    )