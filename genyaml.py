#!/usr/bin/env python3

import pandas as pd
from collections import defaultdict
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as dq

# Read the Excel file
excel_file = 'CIS-Audit-Reqs-Windows2019Server.xlsx'
df = pd.read_excel(excel_file, engine='openpyxl')

# Remove leading and trailing whitespace from column names
df.columns = [col.strip() for col in df.columns]

# Construct the YAML data
yaml_data = defaultdict(dict)

for _, row in df.iterrows():
    category = dq(row['Category'].strip())
    subcategory = dq(row['Subcategory'].strip())

    # Convert "yes"/"no" to boolean values for "CIS Benchmark"
    cis_benchmark = True if row['CIS Benchmark'].strip().lower() == 'yes' else False

    # Remove trailing spaces and single quotes from "CIS Recommended" values, and add quotation marks
    cis_recommended = dq(row['CIS Recommended'].strip().strip("'"))

    yaml_data[category][subcategory] = {
        dq('CIS Benchmark'): cis_benchmark,
        dq('CIS Recommended'): cis_recommended
    }

# Write the YAML data to a file
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
with open('cis-benchmarks.yaml', 'w') as yaml_file:
    yaml.dump(dict(yaml_data), yaml_file)
