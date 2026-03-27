import asyncio
import time
import json
from box_sdk_gen import BoxClient

# ---- Fix stringified object arrays (Box AI quirk) ----
def normalize_object_array(value, field_name):
    """Convert stringified JSON objects into real dicts."""
    if not value or not isinstance(value, list):
        return []

    normalized = []

    for i, item in enumerate(value):
        # Already a valid object
        if isinstance(item, dict):
            normalized.append(item)
            continue

        # Stringified JSON object
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    normalized.append(parsed)
                else:
                    print(f"[WARN] {field_name}[{i}] parsed but not an object")
            except json.JSONDecodeError:
                print(f"[WARN] Failed to parse {field_name}[{i}] JSON string")

    return normalized


async def extract_structured_data(client : BoxClient , file_id: str, file_name: str):
    """Call Box AI to extract structured data asynchronously."""
    loop = asyncio.get_running_loop()
    start_time = time.perf_counter()

    response = await loop.run_in_executor(
        None,
        lambda: client.ai.create_ai_extract_structured(
            items=[{"id": file_id, "type": "file"}],
            fields=[
                {
                    "key": "confidence_score",
                    "description": "The confidence score of the accuracy this police report.",
                    "displayName": "Confidence Score",
                    "prompt": "The confidence score of the accuracy this police report",
                    "type": "number",
                },
                {
                    "key": "report_id",
                    "description": "The unique identifier or number assigned to this police report.",
                    "displayName": "Report ID",
                    "prompt": "Identify and extract the report ID or case number associated with this police report. If multiple IDs are present, choose the main case or report number.",
                    "type": "string",
                },
                {
                    "key": "report_classification",
                    "description": "The classification or type of this police report (e.g., Theft, Assault, Traffic Accident).",
                    "displayName": "Report Classification",
                    "prompt": "Determine and extract the specific type or classification of this police report (e.g., Burglary, Homicide, Vehicle Collision, Domestic Disturbance). Do not provide legal codes or statute numbers—just describe the type of incident using terminology from the document.",
                    "type": "string",
                },
                {
                    "key": "report_location",
                    "description": "The location where the incident or event described in the police report occurred.",
                    "displayName": "Report Location",
                    "prompt": "Identify the location of the incident as described in the report. Include available details such as street address, city, state, and any relevant landmarks. Expand abbreviations where possible.",
                    "type": "string",
                },
                {
                    "key": "report_time",
                    "description": "The date and time when the incident or report was filed or occurred.",
                    "displayName": "Report Time",
                    "prompt": "Identify the date and time associated with the police report — either when the report was filed, when the incident occurred, or both if available. Return in ISO 8601 format if possible (YYYY-MM-DDTHH:MM:SS).",
                    "type": "string",
                },
                {
                    "key": "persons",
                    "description": "All individuals mentioned in the police report, including victims, suspects, witnesses, officers, and other relevant parties.",
                    "type" : "array",
                    "displayName": "Persons",
                    "prompt" : """
                        Identify and list all individuals mentioned in the police report, categorizing each by their role (for example, 'victim,' 'suspect,' 'witness,' 'officer,' 'reporting party,' etc.)
                        About Bates numbers: A Bates number is a unique identifier printed on each page or section of the report (formatted as a 5-digit number like '00001', '00002', etc.). Each person may appear or be referenced multiple times across different Bates pages.
                
                        The 'first_seen_bate' field indicates the Bates number of the page where a person’s name first appears in a narrative — the part of the report that tells the story of events, including the people involved and relevant details — not the page where the officer recorded the person’s personal information.
                        The 'bates_references' field is an array of all Bates numbers (as strings) where this person is mentioned anywhere in the document, including the first_seen_bate.
                    
                        About addresses: The 'address' field should contain the physical or mailing address of the person as listed in the report, if available. If no address is provided in the report, use null.
                        About relationships: The 'relationships' field should list **every other person mentioned in the report who has a defined connection to this person**, along with the nature of that connection. For example, if a victim knows a witness, or a suspect is related to another suspect, that relationship should be recorded here. If no relationships are mentioned for this person, use an empty array.
                        
                        The structure for each person must strictly follow this JSON format: 

                        {
                            "name": "Last Name , First Name",
                            "role": "string (e.g., 'victim', 'suspect', 'officer', etc.)",
                            "date_of_birth": "MM-DD-YYYY or null",
                            "age": "string or null",
                            "race": "string or null",
                            "address": "string or null",
                            "first_seen_bate": "string (e.g., '00001')",
                            "bates_references": ["string"],
                            "narrative_snippet": "short descriptive text about this person's involvement or actions",
                            "relationships": [
                                {
                                    "name": "string",
                                    "relationship": "string"
                                }
                            ]
                        }

                        Important: Each person must be a separate object in the array.
                    """
                },
                {
                    "key": "officers",
                    "description": "All law enforcement officers mentioned in the police report.",
                    "displayName": "Officers",
                    "type": "array",
                    "prompt" : """
                        Identify and list all law enforcement officers mentioned in the police report, categorizing each by their role (for example, 'officer,' 'sergeant,' 'detective,' etc.).
                        About Bates numbers: A Bates number is a unique identifier printed on each page or section of the report (formatted as a 5-digit number like '00001', '00002', etc.). Each person may appear or be referenced multiple times across different Bates pages.

                        The 'first_seen_bate' field indicates the Bates number of the page where the officer's name first appears in a narrative — the part of the report that tells the story of events, including the people involved and relevant details — not the page where the officer recorded the person’s personal information.

                        The structure for each officer must strictly follow this JSON format: 

                        {
                            "name": "string (full name without rank)",
                            "rank": "string (e.g., 'Officer', 'Sergeant', 'Detective')",
                            "badge_number": "string or null",
                            "first_seen_bate": "string (e.g., '00001')",
                            "bates_references": ["string", "string", "string"],
                            "narrative_snippet": "short descriptive text about this officer's involvement or actions"
                        }

                        Important: Each officer must be a separate object in the array.
                    """
                },
                {
                    "key": "officials",
                    "description": "Judges, prosecutors, or other high-level officials involved in the case.",
                    "displayName": "Officials",
                    "type": "array",
                    "prompt": """
                        Identify and list all high-level officials mentioned in the police report, such as judges, prosecutors, or other authorities, categorizing each by their role (e.g., 'Judge,' 'Prosecutor,' 'District Attorney').
                    
                        About Bates numbers: A Bates number is a unique identifier printed on each page or section of the report (formatted as a 5-digit number like '00001', '00002', etc.). Each person may appear or be referenced multiple times across different Bates pages.

                        The 'first_seen_bate' field indicates the Bates number of the page where the officer's name first appears in a narrative — the part of the report that tells the story of events, including the people involved and relevant details — not the page where the officer recorded the person’s personal information.
                        
                        The structure for each official must strictly follow this JSON format:
                            
                        {
                            "name": "string (full name without title)",
                            "title": "string (official role, e.g., 'Judge', 'District Attorney')",
                            "agency_or_court": "string or null",
                            "first_seen_bate": "string (e.g., '00001')",
                            "bates_references": ["string", "string", "string"],
                            "narrative_snippet": "short descriptive text about this official's involvement or actions"
                        }

                        Important: Each official must be a separate object in the array.
                    """,
                },
                {
                    "key": "police_agency",
                    "description": "The name of the police agency.",
                    "displayName": "Police Agency",
                    "prompt": "Identify the name of the police agency responsible for or mentioned in this report.",
                    "type": "string",
                },
            ],
            ai_agent={
                "type": "ai_agent_extract_structured",
                "long_text": {"model": "aws__claude_4_6_opus"},
                "basic_text": {"model": "aws__claude_4_6_opus"},
            },
        ),
    )

    elapsed = time.perf_counter() - start_time

    extracted_data = response.raw_data["answer"]

    #  okay we need to do some hacky thing the api doesn't an array of objects anymore...

    extracted_data["persons"] = normalize_object_array(
        extracted_data.get("persons"),
        "persons"
    )

    extracted_data["officers"] = normalize_object_array(
        extracted_data.get("officers"),
        "officers"
    )

    extracted_data["officials"] = normalize_object_array(
        extracted_data.get("officials"),
        "officials"
    )

    extracted_data["confidence_score"] = response.raw_data.get("confidence_score")

    extracted_data["report_filename"] = file_name
    extracted_data["process_time"] = round(elapsed, 2)
    
    return extracted_data
