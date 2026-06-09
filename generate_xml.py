from pathlib import Path
import csv
import hashlib
import json
from lxml import etree


root = Path(__file__).resolve().parent

config_folder = root / "01_config"
template_folder = root / "03_templates"
output_folder = root / "04_output"


def synthetic_lu_isin(fund_code: str, instrument_name: str, reporting_period: str) -> str:
    source = f"{fund_code}|{instrument_name}|{reporting_period}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest().upper()
    return "LU" + digest[:10]


with open(config_folder / "reporting_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

mappings = []

with open(config_folder / "xml_field_map.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        mappings.append(row)

jobs = [
    {
        "file_type": "DATMAN",
        "template": template_folder / "AIFMSample.xml",
        "output": output_folder / f"DATMAN_{metadata['aifm_id']}_{metadata['reporting_year']}{metadata['reporting_period']}_SYNTHETIC_{metadata['member_state']}.xml",
    },
    {
        "file_type": "DATAIF",
        "template": template_folder / "AIFSample.xml",
        "output": output_folder / f"DATAIF_{metadata['aifm_id']}_{metadata['aif_code']}_{metadata['reporting_year']}{metadata['reporting_period']}_SYNTHETIC_{metadata['member_state']}.xml",
    },
]

date_replacements = {
    "2014-01-01": metadata["period_start"],
    "2014-07-01": metadata["period_start"],
    "2014-10-01": metadata["period_start"],
    "2014-12-31": metadata["period_end"],
    "2014": metadata["reporting_year"],
    "Q4": metadata["reporting_period"],
    "GB": metadata["member_state"],
    "FR": metadata["member_state"],
}

output_folder.mkdir(parents=True, exist_ok=True)

for job in jobs:
    if not job["template"].exists():
        raise FileNotFoundError(f"Missing XML template: {job['template']}")

    parser = etree.XMLParser(remove_blank_text=False, remove_comments=True)
    document = etree.parse(str(job["template"]), parser)

    field_map = {}

    for row in mappings:
        if row["file_type"] == job["file_type"]:
            field_map[row["tag_name"]] = metadata[row["value_key"]]

    last_instrument_name = ""

    for element in document.getroot().iter():
        tag = etree.QName(element).localname

        for attr_name, attr_value in list(element.attrib.items()):
            value = attr_value

            for old, new in date_replacements.items():
                value = value.replace(old, new)

            if attr_name == "CreationDateAndTime":
                value = metadata["creation_datetime"]

            element.attrib[attr_name] = value

        if element.text:
            value = element.text.strip()

            for old, new in date_replacements.items():
                if value == old:
                    value = new

            if tag in field_map:
                value = field_map[tag]

            if tag == "InstrumentName":
                last_instrument_name = value

            if tag == "ISINInstrumentIdentification":
                value = synthetic_lu_isin(
                    metadata["aif_code"],
                    last_instrument_name or "UNKNOWN_INSTRUMENT",
                    metadata["reporting_year"] + metadata["reporting_period"],
                )

            element.text = value

    document.write(
        str(job["output"]),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )

    print(f"Wrote XML: {job['output']}")
