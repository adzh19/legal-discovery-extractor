import os
import json
import asyncio
from io import BytesIO
from dotenv import load_dotenv

from box_sdk_gen import BoxClient
from box_client import get_box_client
from box_sdk_gen.box.errors import BoxSDKError, BoxAPIError
from excel_utils import rebuild_data_from_combined_excel
from uploader import upload_json_data
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


async def process_file(client: BoxClient, item, output_folder_id, project_name):
    uploader_email = None

    try:
        if not item.name.lower().endswith(".xlsx"):
            print(f"🗑 [{project_name}] Non-Excel deleted: {item.name}")
            client.files.delete_file_by_id(item.id)
            return

        print(f"📄 [{project_name}] Processing: {item.name}")

        try:
            report_file_id = item.name.split("_")[-2]
            report_file = client.files.get_file_by_id(report_file_id, fields=["created_by", "name"])
            uploader_email = report_file.created_by.login

            # Delete original report after grabbing info
            client.files.delete_file_by_id(report_file_id)
        except Exception as e:
            print(f"❌ [{project_name}] Failed to get original report info: {e}")
            return

        # --- Step 2: Download Excel ---
        byte_stream = client.downloads.download_file(item.id)
        if not byte_stream:
            print(f"❌ [{project_name}] Failed to download file: {item.id}")
            return

        # Delete uploaded Excel
        client.files.delete_file_by_id(item.id)

        # --- Step 3: Process Excel to JSON ---
        excel_stream = BytesIO(byte_stream.read())
        excel_json = rebuild_data_from_combined_excel(excel_stream)

        file_name = f"{os.path.splitext(report_file.name)[0]}.json"

        await upload_json_data(
            client,
            data=excel_json,
            file_name=file_name,
            output_folder_id=output_folder_id,
        )

        print(f"☁ [{project_name}] {file_name} uploaded")

    except Exception as e:
        print(f"❌ [{project_name}] Failed processing {item.name}: {e}")
        if email_service and uploader_email:
            email_service.send_mail(
                uploader_email,
                f"[{project_name}] Your Excel failed processing",
                f"Failed to process file '{item.name}': {e}"
            )
        raise


async def monitor():
    client = get_box_client(DEV_TOKEN)
    box_projects = load_box_projects()

    print(f"🚀 Excel-to-JSON monitor started.")

    while True:
        tasks = []

        try:
            for project_name, config in box_projects.items():
                input_folder_id = config.get("APPROVED_EXCELS_FOLDER_ID")
                output_folder_id = config.get("JSON_FOLDER_ID")

                if not input_folder_id or not output_folder_id:
                    continue

                try:
                    folder_items = client.folders.get_folder_items(
                        folder_id=input_folder_id,
                        direction="ASC",
                    )

                    for item in folder_items.entries:
                        tasks.append(asyncio.create_task(
                            process_file(client, item, output_folder_id, project_name)
                        ))

                except BoxAPIError as e:
                    print(f"❌ [{project_name}] Box API error: {e.message}")
                except Exception as e:
                    print(f"❌ [{project_name}] Unexpected error: {e}")
                    raise

            if tasks:
                print(f"⚙ Processing {len(tasks)} Excel file(s)...")
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