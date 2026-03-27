import asyncio
import os
import json
from dotenv import load_dotenv

from box_client import get_box_client
from box_sdk_gen import BoxClient, GetMetadataTemplateScope
from box_sdk_gen.box.errors import BoxSDKError, BoxAPIError

import time
from extractor import extract_structured_data
from excel_utils import create_excel_combined_parties
from uploader import upload_excel
from mailer import EmailService


load_dotenv()

DEV_TOKEN = os.getenv("DEVELOPER_TOKEN")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 30))

APP_PASSWORD = os.getenv("APP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

BOX_FOLDERS_FILE = "box_folders.json"


email_service = None

if APP_PASSWORD and SENDER_EMAIL:
    email_service = EmailService(SENDER_EMAIL, APP_PASSWORD)
    email_service.connect()


def load_box_projects():
    if not os.path.exists(BOX_FOLDERS_FILE):
        raise FileNotFoundError("box_folders.json not found")
    with open(BOX_FOLDERS_FILE, "r") as f:
        return json.load(f)


async def process_file(
    client: BoxClient,
    project_name: str,
    file_id: str,
    file_name: str,
    uploader_email: str,
    output_folder_id: str,
):
    try:
        if not file_name.lower().endswith(".pdf"):
            print(f"🗑 [{project_name}] Non-PDF deleted: {file_name}")
            client.files.delete_file_by_id(file_id)
            return

        print(f"[{project_name}] Processing: {file_name}")

        data = await extract_structured_data(client, file_id, file_name)
        print(f"[{project_name}] Extraction complete ({data['process_time']:.2f}s): {file_name}")

        base_name, ext = os.path.splitext(file_name)
        new_file_name = f"{base_name}_{file_id}_{int(time.time())}{ext}"

        excel_path = create_excel_combined_parties(data, new_file_name)

        await upload_excel(client, excel_path, output_folder_id)
        print(f"[{project_name}] Excel uploaded")

        client.file_metadata.create_file_metadata_by_id(
            file_id=file_id,
            scope=GetMetadataTemplateScope.ENTERPRISE,
            template_key="box_gen_file_metadata2",
            request_body={"processed": "true"}
        )

    except Exception as e:
        print(f"❌ [{project_name}] Failed processing {file_name}: {e}")
        if email_service and uploader_email:
            email_service.send_mail(
                uploader_email,
                f"[{project_name}] Your report failed processing",
                f"Failed to process file '{file_name}': {e}"
            )
        raise


async def monitor():
    client = get_box_client(DEV_TOKEN)
    box_projects = load_box_projects()

    print("🚀 Reports-to-Excel monitor started. Projects loaded")

    while True:
        tasks = []

        try:
            for project_name, config in box_projects.items():
                input_folder_id = config.get("REPORTS_FOLDER_ID")
                output_folder_id = config.get("PENDING_EXCELS_FOLDER_ID")

                if not input_folder_id or not output_folder_id:
                    continue

                try:
                    folder_items = client.folders.get_folder_items(
                        folder_id=input_folder_id,
                        direction="ASC",
                        fields=[
                            "name",
                            "created_by",
                            "metadata.enterprise.box_gen_file_metadata2"
                        ],
                    )

                    for item in folder_items.entries:
                        uploader_email = item.created_by.login

                        if item.metadata and item.metadata.enterprise and item.metadata.enterprise.get("box_gen_file_metadata2"):
                            continue

                        task = asyncio.create_task(
                            process_file(
                                client,
                                project_name,
                                item.id,
                                item.name,
                                uploader_email,
                                output_folder_id
                            )
                        )
                        tasks.append(task)

                except BoxAPIError as e:
                    print(f"❌ [{project_name}] Box API Error: {e.message}")
                except Exception as e:
                    raise

            if tasks:
                print(f"⚙ Processing {len(tasks)} file(s)...")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"❌ Task failed: {result}")

        except BoxSDKError as e:
            print(f"❌ Box SDK fatal error: {e.message}")
            break
        except Exception as e:
            print(f"❌ Fatal error: {e}")

        await asyncio.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    asyncio.run(monitor())