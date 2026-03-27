import asyncio
from pipelines.reports_to_excel import monitor as monitor_reports
from pipelines.excel_to_json import monitor as monitor_excels
from pipelines.create_metadata_template import create_metadata_template

async def main():    
    create_metadata_template()

    await asyncio.gather(
        monitor_reports(),
        monitor_excels(),
    )

if __name__ == "__main__":
    asyncio.run(main())
