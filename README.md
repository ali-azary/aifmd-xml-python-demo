# AIFMD XML Python Demo

This is a compact demo package to accompany the article:

**Generating and Validating AIFMD XML Files with Python**

It demonstrates:

- config-driven XML generation
- XML template population with `lxml`
- deterministic synthetic ISIN generation
- XSD validation with schema caching
- JSON validation reports with human-readable field labels

## Folder structure

```text
01_config/
    reporting_metadata.json
    xml_field_map.csv

02_schemas/
    AIFMD_DATMAN.xsd
    AIFMD_DATAIF.xsd

03_templates/
    AIFMSample.xml
    AIFSample.xml

04_output/
    generated XML and validation_report.json

generate_xml.py
validate_xml.py
requirements.txt
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python generate_xml.py
python validate_xml.py
```

## Output

The scripts generate:

```text
04_output/DATMAN_A00018427_2026Q1_SYNTHETIC_LU.xml
04_output/DATAIF_A00018427_LBSCF01_2026Q1_SYNTHETIC_LU.xml
04_output/validation_report.json
```

## Note

The included XSD files are compact demo schemas, not official ESMA schemas.

For production or regulatory submission work, replace them with the applicable official schema files and add business-rule validation, reconciliation checks, identifier controls, audit logs, and approval workflow controls.
