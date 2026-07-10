"""
Builds attack_mapping for every NIST CSF 2.0 control by joining:
  1. NIST's official CSF 2.0 -> SP 800-53 Rev 5 crosswalk (user-supplied)
  2. CTID's verified SP 800-53 Rev 5 -> ATT&CK mapping
     (data/nist800_53_r5_to_attack.json)

Usage:
    python3 build_attack_mapping.py <crosswalk_file> <nist_csf_2_0.json> \
        <output.json>

The crosswalk file can be:
  - The OLIR JSON export from
    https://csrc.nist.gov/extensions/nudp/services/json/csf/download?olirids=all
  - The CSF/PF-to-800-53r5 xlsx from
    https://csrc.nist.gov/files/pubs/sp/800/53/r5/upd1/final/docs/csf-pf-to-sp800-53r5-mappings.xlsx

NOTE: the exact parsing logic for the crosswalk (`load_crosswalk`) is left as a
stub below because the schema of NIST's export wasn't accessible to verify in
this environment. Once you upload the actual file, this will be filled in to
match its real structure rather than guessed.
"""

import json
import sys
from pathlib import Path


def load_attack_data(path: Path) -> dict[str, list[str]]:
    """Loads the verified 800-53 -> ATT&CK mapping."""
    data = json.loads(Path(path).read_text())
    return data["mappings"]


def load_crosswalk(path: Path) -> dict[str, list[str]]:
    """Loads the CSF 2.0 -> SP 800-53 Rev 5 crosswalk.

    Returns: dict mapping CSF control_id (e.g. "GV.OC-01") -> list of
    SP 800-53 control IDs (e.g. ["PM-11", "RA-3"]).

    STUB: implement once the real crosswalk file/schema is available.
    """
    raise NotImplementedError(
        "Upload the NIST CSF-to-800-53 crosswalk file and this function "
        "will be implemented to match its actual schema."
    )


def build(
    csf_json_path: Path, crosswalk_path: Path, attack_data_path: Path, out_path: Path
):
    csf = json.loads(csf_json_path.read_text())
    crosswalk = load_crosswalk(crosswalk_path)
    attack_data = load_attack_data(attack_data_path)

    for control in csf["controls"]:
        cid = control["control_id"]
        sp80053_controls = crosswalk.get(cid, [])
        techniques: set[str] = set()
        for sp_ctrl in sp80053_controls:
            techniques.update(attack_data.get(sp_ctrl, []))
        control["attack_mapping"] = sorted(techniques)

    out_path.write_text(json.dumps(csf, indent=2))
    mapped = sum(1 for c in csf["controls"] if c.get("attack_mapping"))
    print(f"Populated attack_mapping for {mapped}/{len(csf['controls'])} controls")


if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) != 4:
        print(
            "Usage: build_attack_mapping.py <crosswalk_file> "
            "<nist_csf_2_0.json> <output.json>"
        )
        sys.exit(1)
    build(
        csf_json_path=Path(sys.argv[2]),
        crosswalk_path=Path(sys.argv[1]),
        attack_data_path=Path(__file__).parent
        / "data"
        / "nist800_53_r5_to_attack.json",
        out_path=Path(sys.argv[3]),
    )
