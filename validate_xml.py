from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
from lxml import etree


@dataclass
class ValidationJob:
    file_type: str
    xml_path: Path
    xsd_path: Path


@dataclass
class ValidationError:
    file_type: str
    xml_file: str
    schema_file: str
    line: int | None
    column: int | None
    field_name: str
    field_label: str
    domain: str
    error_type: str
    level: str
    message: str


@dataclass
class ValidationResult:
    file_type: str
    xml_file: str
    schema_file: str
    valid: bool
    error_count: int
    errors: list[ValidationError]


FIELD_LABELS = {
    "FilingType": "Filing Type (INIT / AMND / CANC)",
    "ReportingMemberState": "Reporting Member State",
    "AIFMNationalCode": "AIFM National Code",
    "AIFMIdentifierLEI": "AIFM LEI",
    "AIFMIdentifierBIC": "AIFM BIC",
    "AIFMName": "AIFM Name",
    "ReportingPeriodType": "Reporting Period Type",
    "ReportingYear": "Reporting Year",
    "PeriodStart": "Reporting Period Start Date",
    "PeriodEnd": "Reporting Period End Date",
    "AIFNationalCode": "AIF National Code",
    "AIFIdentifierLEI": "AIF LEI",
    "AIFName": "AIF Name",
    "AIFDomicile": "AIF Domicile",
    "InstrumentName": "Instrument Name",
    "ISINInstrumentIdentification": "Instrument ISIN",
}


def extract_field_name(message: str) -> str:
    match = re.search(r"\{[^}]+\}([A-Za-z0-9_]+)", message)

    if match:
        return match.group(1)

    match = re.search(r"Element '([^']+)'", message)

    if match:
        raw = match.group(1)
        return raw.split("}")[-1]

    return ""


root = Path(__file__).resolve().parent

schema_folder = root / "02_schemas"
output_folder = root / "04_output"

jobs = [
    ValidationJob(
        file_type="DATMAN",
        xml_path=output_folder / "DATMAN_A00018427_2026Q1_SYNTHETIC_LU.xml",
        xsd_path=schema_folder / "AIFMD_DATMAN.xsd",
    ),
    ValidationJob(
        file_type="DATAIF",
        xml_path=output_folder / "DATAIF_A00018427_LBSCF01_2026Q1_SYNTHETIC_LU.xml",
        xsd_path=schema_folder / "AIFMD_DATAIF.xsd",
    ),
]

schema_cache = {}
results = []

for job in jobs:
    if not job.xml_path.exists():
        raise FileNotFoundError(f"Missing XML file: {job.xml_path}")

    if not job.xsd_path.exists():
        raise FileNotFoundError(f"Missing XSD file: {job.xsd_path}")

    if job.xsd_path not in schema_cache:
        schema_doc = etree.parse(str(job.xsd_path))
        schema_cache[job.xsd_path] = etree.XMLSchema(schema_doc)

    schema = schema_cache[job.xsd_path]
    errors = []

    try:
        xml_doc = etree.parse(str(job.xml_path))
        valid = schema.validate(xml_doc)

        if not valid:
            for error in schema.error_log:
                field_name = extract_field_name(error.message)

                errors.append(
                    ValidationError(
                        file_type=job.file_type,
                        xml_file=job.xml_path.name,
                        schema_file=job.xsd_path.name,
                        line=error.line,
                        column=error.column,
                        field_name=field_name,
                        field_label=FIELD_LABELS.get(field_name, field_name),
                        domain=error.domain_name,
                        error_type=error.type_name,
                        level=error.level_name,
                        message=error.message,
                    )
                )

    except etree.XMLSyntaxError as e:
        valid = False
        errors.append(
            ValidationError(
                file_type=job.file_type,
                xml_file=job.xml_path.name,
                schema_file=job.xsd_path.name,
                line=e.position[0],
                column=e.position[1],
                field_name="",
                field_label="XML syntax",
                domain="XML",
                error_type="XMLSyntaxError",
                level="FATAL",
                message=str(e),
            )
        )

    results.append(
        ValidationResult(
            file_type=job.file_type,
            xml_file=job.xml_path.name,
            schema_file=job.xsd_path.name,
            valid=valid,
            error_count=len(errors),
            errors=errors,
        )
    )

report = {
    "run_status": "PASS" if all(result.valid for result in results) else "FAIL",
    "file_count": len(results),
    "invalid_file_count": sum(not result.valid for result in results),
    "results": [asdict(result) for result in results],
}

report_path = output_folder / "validation_report.json"

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"Wrote validation report: {report_path}")
print(json.dumps(report, indent=2))
