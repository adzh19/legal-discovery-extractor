import os
import json
import asyncio
from io import BytesIO
from dotenv import load_dotenv

from box_sdk_gen import GetMetadataTemplateScope , BoxAPIError
from box_client import get_box_client

load_dotenv()

DEV_TOKEN = os.getenv("DEVELOPER_TOKEN")

def create_metadata_template():
    client = get_box_client(DEV_TOKEN)
    template_key = "box_gen_file_metadata2"

    try:
        client.metadata_templates.get_metadata_template(
            GetMetadataTemplateScope.ENTERPRISE,
            template_key=template_key
        )
        
    except BoxAPIError as e:
        if e.response_info.status_code == 404:
            try:
                client.metadata_templates.create_metadata_template(
                    scope=GetMetadataTemplateScope.ENTERPRISE,
                    hidden=True,
                    fields=[
                        {
                            "type": "string",
                            "key": "processed",
                            "displayName": "Processed"
                        }
                    ],
                    display_name="Box Gen File Metadata",
                    template_key=template_key
                )

                print("✅ Metadata template created successfully")

            except BoxAPIError as create_error:
                print("❌ Failed to create metadata template:", create_error)

        else:
            print("❌ Box API error:", e)

    except Exception as e:
        print("❌ Unexpected error:", e)
