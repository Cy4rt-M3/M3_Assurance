import re
import subprocess
import pandas as pd


EXCEL_FILE = "Pod_Nova_Framework_Registry.xlsx"


FRAMEWORK_PREFIXES = {
    "NIST CSF 2.0": "nist_csf_2_0",
    "PCI DSS": "pci_dss_4_0",
    "GDPR": "gdpr",
    "NIS2": "nis2",
    "ISO 27001": "iso_27001_2022",
    "ISO 27002": "iso_27002_2022",
    "SOC 2": "soc_2",
    "HIPAA": "hipaa",
}


def normalize_source(framework, control_id):
    """
    Convert Excel source values into database control IDs.
    """

    framework = framework.strip()
    control_id = control_id.strip()

    if framework not in FRAMEWORK_PREFIXES:
        raise ValueError(
            f"Unknown framework: {framework}"
        )

    return f"{FRAMEWORK_PREFIXES[framework]}:{control_id}"


def normalize_target(text):
    """
    Convert an Excel target reference into a database-style control ID.

    Returns None when the target is too vague or cannot safely
    be mapped to a real database control.
    """

    text = str(text).strip()

    if not text:
        return None

    # Remove descriptive text in parentheses.
    text = re.sub(
        r"\s+\([^)]*\)",
        "",
        text,
    ).strip()

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # ------------------------------------------------------------
    # NIST CSF
    # ------------------------------------------------------------

    match = re.match(
        r"^NIST CSF(?:\s+2\.0)?\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        # Ignore broad function references such as:
        # NIST CSF GV
        # NIST CSF Protect Function
        if value.lower() in {
            "gv",
            "pr",
            "protect function",
            "protect",
            "identify function",
            "detect function",
            "respond function",
            "recover function",
        }:
            return None

        return f"nist_csf_2_0:{value}"

    # ------------------------------------------------------------
    # ISO 27001
    # ------------------------------------------------------------

    match = re.match(
        r"^ISO 27001(?:\s*:\s*2022)?\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        # Remove generic words that are not actual controls.
        if value.lower() in {
            "compliance",
            "certification",
            "internal audit",
        }:
            return None

        # Convert "Clause X" into "Clause X".
        # We do not invent an Annex A control from a generic clause.
        if re.match(r"^Clause\s+", value, re.I):
            return f"iso_27001_2022:{value}"

        return f"iso_27001_2022:{value}"

    # ------------------------------------------------------------
    # ISO 27002
    # ------------------------------------------------------------

    match = re.match(
        r"^ISO 27002(?:\s*:\s*2022)?\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()
        return f"iso_27002_2022:{value}"

    # ------------------------------------------------------------
    # PCI DSS
    # ------------------------------------------------------------

    match = re.match(
        r"^PCI DSS(?:\s+4\.0)?\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        # Ignore broad/non-control descriptions.
        if value.lower() in {
            "compliance",
            "assessment",
        }:
            return None

        # "Requirement 12" is a valid-looking reference,
        # but only return it if it actually exists in DB later.
        value = re.sub(
            r"^Req\.\s*",
            "Requirement ",
            value,
            flags=re.I,
        )

        return f"pci_dss_4_0:{value}"

    # ------------------------------------------------------------
    # GDPR
    # ------------------------------------------------------------

    match = re.match(
        r"^GDPR\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        if value.lower() in {
            "supervisory authority",
            "administrative fines",
        }:
            return None

        # Normalize:
        # GDPR 32 -> GDPR Article 32
        # GDPR Art.32 -> GDPR Article 32
        # GDPR Article 32 -> same
        article = re.match(
            r"^(?:Art(?:icle)?\.?\s*)?(\d+)$",
            value,
            re.I,
        )

        if article:
            value = f"Article {article.group(1)}"

        return f"gdpr:{value}"

    # ------------------------------------------------------------
    # NIS2
    # ------------------------------------------------------------

    match = re.match(
        r"^NIS2\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        if value.lower() in {
            "compliance",
            "cybersecurity act",
        }:
            return None

        # Normalize:
        # NIS2 20 -> NIS2 Article 20
        # NIS2 Art.20 -> NIS2 Article 20
        # NIS2 Article 20 -> same
        article = re.match(
            r"^(?:Art(?:icle)?\.?\s*)?(\d+)$",
            value,
            re.I,
        )

        if article:
            value = f"Article {article.group(1)}"

        return f"nis2:{value}"

    # ------------------------------------------------------------
    # HIPAA
    # ------------------------------------------------------------

    match = re.match(
        r"^HIPAA\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        # Broad descriptions are not individual controls.
        if value.lower() in {
            "privacy rule",
            "security rule",
            "breach notification rule",
            "documentation requirements",
        }:
            return None

        # Normalize common prefixes.
        value = re.sub(
            r"^Security Rule\s+",
            "",
            value,
            flags=re.I,
        )

        return f"hipaa:{value}"

    # ------------------------------------------------------------
    # SOC 2
    # ------------------------------------------------------------

    match = re.match(
        r"^SOC\s*2\s+(.+)$",
        text,
        re.I,
    )

    if match:
        value = match.group(1).strip()

        if value.lower() in {
            "compliance",
            "assessment",
        }:
            return None

        return f"soc_2:{value}"

    return None


def split_targets(value):
    """
    Split Excel Equivalent Controls into individual targets.

    The spreadsheet uses both ';' and ',' separators.
    """

    value = str(value).strip()

    if not value:
        return []

    # First split on semicolon.
    parts = re.split(r";", value)

    final_parts = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        # Then split comma-separated framework references.
        comma_parts = re.split(r",\s*", part)

        for item in comma_parts:
            item = item.strip()

            if item:
                final_parts.append(item)

    return final_parts


def get_database_controls():
    """
    Read all control IDs currently present in PostgreSQL.
    """

    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "assurance",
        "-d",
        "assurance",
        "-At",
        "-c",
        "SELECT control_id FROM controls ORDER BY control_id;",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    }


def get_existing_crosswalks():
    """
    Read crosswalk rows already present in PostgreSQL.
    """

    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "assurance",
        "-d",
        "assurance",
        "-At",
        "-F",
        "\t",
        "-c",
        """
        SELECT
            source_control_id,
            target_control_id,
            equivalence_level
        FROM cross_walks;
        """,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    existing = set()

    for line in result.stdout.splitlines():

        if not line.strip():
            continue

        parts = line.split("\t")

        if len(parts) != 3:
            continue

        source, target, level = parts

        existing.add(
            (
                source,
                target,
                level,
            )
        )

    return existing


def insert_crosswalks(rows):
    """
    Insert valid crosswalks into PostgreSQL.
    """

    if not rows:
        print()
        print("No new mappings to insert.")
        return

    sql_values = []

    for source, target, level in rows:

        source = source.replace(
            "'",
            "''",
        )

        target = target.replace(
            "'",
            "''",
        )

        level = level.replace(
            "'",
            "''",
        )

        sql_values.append(
            f"('{source}', '{target}', '{level}')"
        )

    sql = f"""
BEGIN;

INSERT INTO cross_walks
    (
        source_control_id,
        target_control_id,
        equivalence_level
    )
VALUES
    {",".join(sql_values)};

COMMIT;
"""

    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "assurance",
        "-d",
        "assurance",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]

    subprocess.run(
        command,
        check=True,
    )

    print()
    print(
        f"Inserted mappings: {len(rows)}"
    )


def main():

    print("=" * 70)
    print("Crosswalk Loader")
    print("=" * 70)

    # ------------------------------------------------------------
    # Read Excel
    # ------------------------------------------------------------

    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Master Controls",
    )

    crosswalk_rows = df[
        df["Equivalent Controls"].notna()
    ].copy()

    print()
    print(
        f"Master controls: {len(df)}"
    )

    print(
        f"Rows containing crosswalks: "
        f"{len(crosswalk_rows)}"
    )

    # ------------------------------------------------------------
    # Parse mappings
    # ------------------------------------------------------------

    mappings = []
    parse_failures = []

    for _, row in crosswalk_rows.iterrows():

        framework = str(
            row["Framework"]
        ).strip()

        source_control = str(
            row["Control ID"]
        ).strip()

        try:
            source_id = normalize_source(
                framework,
                source_control,
            )
        except ValueError as exc:

            parse_failures.append(
                (
                    f"{framework}:{source_control}",
                    str(exc),
                )
            )

            continue

        equivalents = row[
            "Equivalent Controls"
        ]

        for item in split_targets(
            equivalents
        ):

            target_id = normalize_target(
                item
            )

            if target_id:

                mappings.append(
                    (
                        source_id,
                        target_id,
                        "Partial",
                    )
                )

            else:

                parse_failures.append(
                    (
                        source_id,
                        item,
                    )
                )

    # Remove duplicates while preserving order.
    mappings = list(
        dict.fromkeys(mappings)
    )

    print()
    print(
        f"Parsed unique mappings: "
        f"{len(mappings)}"
    )

    # ------------------------------------------------------------
    # Read database controls
    # ------------------------------------------------------------

    controls = get_database_controls()

    print(
        f"Controls in database: "
        f"{len(controls)}"
    )

    # ------------------------------------------------------------
    # Validate mappings
    # ------------------------------------------------------------

    valid = []
    invalid = []

    for source_id, target_id, level in mappings:

        source_exists = (
            source_id in controls
        )

        target_exists = (
            target_id in controls
        )

        if (
            source_exists
            and target_exists
        ):

            valid.append(
                (
                    source_id,
                    target_id,
                    level,
                )
            )

        else:

            invalid.append(
                (
                    source_id,
                    target_id,
                    source_exists,
                    target_exists,
                )
            )

    print()
    print(
        f"Valid mappings: {len(valid)}"
    )

    print(
        f"Invalid mappings: "
        f"{len(invalid)}"
    )

    print(
        f"Parse failures: "
        f"{len(parse_failures)}"
    )

    # ------------------------------------------------------------
    # Invalid mappings
    # ------------------------------------------------------------

    if invalid:

        print()
        print(
            "First 30 invalid mappings:"
        )

        for (
            source,
            target,
            source_ok,
            target_ok,
        ) in invalid[:30]:

            print(
                f"  {source} -> {target} "
                f"(source_exists={source_ok}, "
                f"target_exists={target_ok})"
            )

    # ------------------------------------------------------------
    # Parse failures
    # ------------------------------------------------------------

    if parse_failures:

        print()
        print(
            "First 30 parse failures:"
        )

        for source, item in parse_failures[:30]:

            print(
                f"  {source} -> {item}"
            )

    # ------------------------------------------------------------
    # Existing crosswalks
    # ------------------------------------------------------------

    existing = get_existing_crosswalks()

    new_valid = [
        row
        for row in valid
        if row not in existing
    ]

    print()
    print(
        f"Existing crosswalk rows: "
        f"{len(existing)}"
    )

    print(
        f"New valid mappings to insert: "
        f"{len(new_valid)}"
    )

    # ------------------------------------------------------------
    # Show sample
    # ------------------------------------------------------------

    print()
    print(
        "First 20 valid mappings:"
    )

    for (
        source,
        target,
        level,
    ) in valid[:20]:

        print(
            f"  {source} -> "
            f"{target} [{level}]"
        )

    # ------------------------------------------------------------
    # SAFETY SWITCH
    #
    # Keep this False for now.
    # ------------------------------------------------------------

    DRY_RUN = False

    print()
    print("=" * 70)

    if DRY_RUN:

        print(
            "DRY RUN ONLY — "
            "database was NOT modified."
        )

        print(
            "Review the output before "
            "enabling insertion."
        )

    else:

        print(
            "INSERT MODE — "
            "writing valid mappings to database."
        )

        insert_crosswalks(
            new_valid
        )

    print("=" * 70)


if __name__ == "__main__":
    main()




# import re
# import subprocess
# import pandas as pd


# EXCEL_FILE = "Pod_Nova_Framework_Registry.xlsx"


# FRAMEWORK_PREFIXES = {
#     "NIST CSF 2.0": "nist_csf_2_0",
#     "PCI DSS": "pci_dss_4_0",
#     "GDPR": "gdpr",
#     "NIS2": "nis2",
#     "ISO 27001": "iso_27001_2022",
#     "ISO 27002": "iso_27002_2022",
#     "SOC 2": "soc_2",
#     "HIPAA": "hipaa",
# }


# def normalize_source(framework, control_id):
#     return f"{FRAMEWORK_PREFIXES[framework]}:{control_id.strip()}"


# def normalize_target(text):
#     text = text.strip()

#     # Remove descriptive text in parentheses.
#     text = re.sub(r"\s+\([^)]*\)\s*$", "", text).strip()

#     patterns = [
#         (r"^ISO 27001\s+(.+)$", "iso_27001_2022"),
#         (r"^ISO 27002\s+(.+)$", "iso_27002_2022"),
#         (r"^PCI DSS\s+(.+)$", "pci_dss_4_0"),
#         (r"^GDPR\s+(.+)$", "gdpr"),
#         (r"^NIS2\s+(.+)$", "nis2"),
#         (r"^HIPAA\s+(.+)$", "hipaa"),
#         (r"^SOC 2\s+(.+)$", "soc_2"),
#         (r"^NIST CSF(?: 2\.0)?\s+(.+)$", "nist_csf_2_0"),
#     ]

#     for pattern, prefix in patterns:
#         match = re.match(pattern, text, re.I)
#         if match:
#             return f"{prefix}:{match.group(1).strip()}"

#     return None


# def get_database_controls():
#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-At",
#         "-c",
#         "SELECT control_id FROM controls ORDER BY control_id;",
#     ]

#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True,
#         check=True,
#     )

#     return {
#         line.strip()
#         for line in result.stdout.splitlines()
#         if line.strip()
#     }


# def get_existing_crosswalks():
#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-At",
#         "-F",
#         "\t",
#         "-c",
#         """
#         SELECT source_control_id, target_control_id, equivalence_level
#         FROM cross_walks;
#         """,
#     ]

#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True,
#         check=True,
#     )

#     existing = set()

#     for line in result.stdout.splitlines():
#         if not line.strip():
#             continue

#         source, target, level = line.split("\t")
#         existing.add((source, target, level))

#     return existing


# def insert_crosswalks(rows):
#     if not rows:
#         print("\nNo new mappings to insert.")
#         return

#     values = ",".join(
#         f"({subprocess.list2cmdline([source])})"
#         for source, target, level in []
#     )

#     sql_values = []

#     for source, target, level in rows:
#         source = source.replace("'", "''")
#         target = target.replace("'", "''")
#         level = level.replace("'", "''")

#         sql_values.append(
#             f"('{source}', '{target}', '{level}')"
#         )

#     sql = f"""
#     BEGIN;

#     INSERT INTO cross_walks
#         (source_control_id, target_control_id, equivalence_level)
#     VALUES
#         {",".join(sql_values)};

#     COMMIT;
#     """

#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-v",
#         "ON_ERROR_STOP=1",
#         "-c",
#         sql,
#     ]

#     subprocess.run(command, check=True)

#     print(f"\nInserted mappings: {len(rows)}")


# def main():
#     df = pd.read_excel(
#         EXCEL_FILE,
#         sheet_name="Master Controls",
#     )

#     crosswalk_rows = df[df["Equivalent Controls"].notna()].copy()

#     print(f"Master controls: {len(df)}")
#     print(f"Rows containing crosswalks: {len(crosswalk_rows)}")

#     mappings = []
#     parse_failures = []

#     for _, row in crosswalk_rows.iterrows():
#         framework = str(row["Framework"]).strip()
#         source_control = str(row["Control ID"]).strip()

#         source_id = normalize_source(
#             framework,
#             source_control,
#         )

#         equivalents = str(row["Equivalent Controls"])

#         for item in equivalents.split(";"):
#             item = item.strip()

#             if not item:
#                 continue

#             target_id = normalize_target(item)

#             if target_id:
#                 mappings.append(
#                     (
#                         source_id,
#                         target_id,
#                         "Partial",
#                     )
#                 )
#             else:
#                 parse_failures.append(
#                     (
#                         source_id,
#                         item,
#                     )
#                 )

#     mappings = list(dict.fromkeys(mappings))

#     print(f"\nParsed unique mappings: {len(mappings)}")

#     controls = get_database_controls()

#     print(f"Controls in database: {len(controls)}")

#     valid = []
#     invalid = []

#     for source_id, target_id, level in mappings:
#         source_exists = source_id in controls
#         target_exists = target_id in controls

#         if source_exists and target_exists:
#             valid.append(
#                 (
#                     source_id,
#                     target_id,
#                     level,
#                 )
#             )
#         else:
#             invalid.append(
#                 (
#                     source_id,
#                     target_id,
#                     source_exists,
#                     target_exists,
#                 )
#             )

#     print(f"Valid mappings: {len(valid)}")
#     print(f"Invalid mappings: {len(invalid)}")
#     print(f"Parse failures: {len(parse_failures)}")

#     if invalid:
#         print("\nFirst 30 invalid mappings:")
#         for source, target, source_ok, target_ok in invalid[:30]:
#             print(
#                 f"  {source} -> {target} "
#                 f"(source_exists={source_ok}, target_exists={target_ok})"
#             )

#     if parse_failures:
#         print("\nFirst 30 parse failures:")
#         for source, item in parse_failures[:30]:
#             print(f"  {source} -> {item}")

#     existing = get_existing_crosswalks()

#     new_valid = [
#         row
#         for row in valid
#         if row not in existing
#     ]

#     print(f"\nExisting crosswalk rows: {len(existing)}")
#     print(f"New valid mappings to insert: {len(new_valid)}")

#     print("\nFirst 20 valid mappings:")
#     for source, target, level in valid[:20]:
#         print(f"  {source} -> {target} [{level}]")

#     print("\nReady to insert valid mappings.")
#     insert_crosswalks(new_valid)


# if __name__ == "__main__":
#     main()
# PYcat > scripts_load_crosswalks.py <<'PY'
# import re
# import subprocess
# import pandas as pd


# EXCEL_FILE = "Pod_Nova_Framework_Registry.xlsx"


# FRAMEWORK_PREFIXES = {
#     "NIST CSF 2.0": "nist_csf_2_0",
#     "PCI DSS": "pci_dss_4_0",
#     "GDPR": "gdpr",
#     "NIS2": "nis2",
#     "ISO 27001": "iso_27001_2022",
#     "ISO 27002": "iso_27002_2022",
#     "SOC 2": "soc_2",
#     "HIPAA": "hipaa",
# }


# def normalize_source(framework, control_id):
#     return f"{FRAMEWORK_PREFIXES[framework]}:{control_id.strip()}"


# def normalize_target(text):
#     text = text.strip()

#     # Remove descriptive text in parentheses.
#     text = re.sub(r"\s+\([^)]*\)\s*$", "", text).strip()

#     patterns = [
#         (r"^ISO 27001\s+(.+)$", "iso_27001_2022"),
#         (r"^ISO 27002\s+(.+)$", "iso_27002_2022"),
#         (r"^PCI DSS\s+(.+)$", "pci_dss_4_0"),
#         (r"^GDPR\s+(.+)$", "gdpr"),
#         (r"^NIS2\s+(.+)$", "nis2"),
#         (r"^HIPAA\s+(.+)$", "hipaa"),
#         (r"^SOC 2\s+(.+)$", "soc_2"),
#         (r"^NIST CSF(?: 2\.0)?\s+(.+)$", "nist_csf_2_0"),
#     ]

#     for pattern, prefix in patterns:
#         match = re.match(pattern, text, re.I)
#         if match:
#             return f"{prefix}:{match.group(1).strip()}"

#     return None


# def get_database_controls():
#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-At",
#         "-c",
#         "SELECT control_id FROM controls ORDER BY control_id;",
#     ]

#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True,
#         check=True,
#     )

#     return {
#         line.strip()
#         for line in result.stdout.splitlines()
#         if line.strip()
#     }


# def get_existing_crosswalks():
#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-At",
#         "-F",
#         "\t",
#         "-c",
#         """
#         SELECT source_control_id, target_control_id, equivalence_level
#         FROM cross_walks;
#         """,
#     ]

#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True,
#         check=True,
#     )

#     existing = set()

#     for line in result.stdout.splitlines():
#         if not line.strip():
#             continue

#         source, target, level = line.split("\t")
#         existing.add((source, target, level))

#     return existing


# def insert_crosswalks(rows):
#     if not rows:
#         print("\nNo new mappings to insert.")
#         return

#     values = ",".join(
#         f"({subprocess.list2cmdline([source])})"
#         for source, target, level in []
#     )

#     sql_values = []

#     for source, target, level in rows:
#         source = source.replace("'", "''")
#         target = target.replace("'", "''")
#         level = level.replace("'", "''")

#         sql_values.append(
#             f"('{source}', '{target}', '{level}')"
#         )

#     sql = f"""
#     BEGIN;

#     INSERT INTO cross_walks
#         (source_control_id, target_control_id, equivalence_level)
#     VALUES
#         {",".join(sql_values)};

#     COMMIT;
#     """

#     command = [
#         "docker",
#         "compose",
#         "exec",
#         "-T",
#         "postgres",
#         "psql",
#         "-U",
#         "assurance",
#         "-d",
#         "assurance",
#         "-v",
#         "ON_ERROR_STOP=1",
#         "-c",
#         sql,
#     ]

#     subprocess.run(command, check=True)

#     print(f"\nInserted mappings: {len(rows)}")


# def main():
#     df = pd.read_excel(
#         EXCEL_FILE,
#         sheet_name="Master Controls",
#     )

#     crosswalk_rows = df[df["Equivalent Controls"].notna()].copy()

#     print(f"Master controls: {len(df)}")
#     print(f"Rows containing crosswalks: {len(crosswalk_rows)}")

#     mappings = []
#     parse_failures = []

#     for _, row in crosswalk_rows.iterrows():
#         framework = str(row["Framework"]).strip()
#         source_control = str(row["Control ID"]).strip()

#         source_id = normalize_source(
#             framework,
#             source_control,
#         )

#         equivalents = str(row["Equivalent Controls"])

#         for item in equivalents.split(";"):
#             item = item.strip()

#             if not item:
#                 continue

#             target_id = normalize_target(item)

#             if target_id:
#                 mappings.append(
#                     (
#                         source_id,
#                         target_id,
#                         "Partial",
#                     )
#                 )
#             else:
#                 parse_failures.append(
#                     (
#                         source_id,
#                         item,
#                     )
#                 )

#     mappings = list(dict.fromkeys(mappings))

#     print(f"\nParsed unique mappings: {len(mappings)}")

#     controls = get_database_controls()

#     print(f"Controls in database: {len(controls)}")

#     valid = []
#     invalid = []

#     for source_id, target_id, level in mappings:
#         source_exists = source_id in controls
#         target_exists = target_id in controls

#         if source_exists and target_exists:
#             valid.append(
#                 (
#                     source_id,
#                     target_id,
#                     level,
#                 )
#             )
#         else:
#             invalid.append(
#                 (
#                     source_id,
#                     target_id,
#                     source_exists,
#                     target_exists,
#                 )
#             )

#     print(f"Valid mappings: {len(valid)}")
#     print(f"Invalid mappings: {len(invalid)}")
#     print(f"Parse failures: {len(parse_failures)}")

#     if invalid:
#         print("\nFirst 30 invalid mappings:")
#         for source, target, source_ok, target_ok in invalid[:30]:
#             print(
#                 f"  {source} -> {target} "
#                 f"(source_exists={source_ok}, target_exists={target_ok})"
#             )

#     if parse_failures:
#         print("\nFirst 30 parse failures:")
#         for source, item in parse_failures[:30]:
#             print(f"  {source} -> {item}")

#     existing = get_existing_crosswalks()

#     new_valid = [
#         row
#         for row in valid
#         if row not in existing
#     ]

#     print(f"\nExisting crosswalk rows: {len(existing)}")
#     print(f"New valid mappings to insert: {len(new_valid)}")

#     print("\nFirst 20 valid mappings:")
#     for source, target, level in valid[:20]:
#         print(f"  {source} -> {target} [{level}]")

#     print("\nReady to insert valid mappings.")
#     insert_crosswalks(new_valid)


# if __name__ == "__main__":
#     main()
