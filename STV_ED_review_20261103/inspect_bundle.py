"""Read-only source inspection; all generated files go to the review directory."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

SOURCE = Path(r"E:\Documents\ChatGPT\New project\STV_ED_reproducible_pilot_bundle\rural_narrow_road_research")
OUT = Path(__file__).resolve().parent
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}

def visible_text(element):
    return "".join(n.text or "" for n in element.iter() if n.tag in (f"{{{NS['w']}}}t", f"{{{NS['m']}}}t"))

inventory = []
for path in sorted(SOURCE.rglob("*")):
    if not path.is_file():
        continue
    data = path.read_bytes()
    inventory.append({"path": str(path.relative_to(SOURCE)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    if path.suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
            lines = []
            body = root.find("w:body", NS)
            for index, block in enumerate(body, 1):
                kind = block.tag.rsplit("}", 1)[-1]
                if kind == "p":
                    lines.append(f"[BLOCK {index} PARAGRAPH] {visible_text(block)}")
                elif kind == "tbl":
                    lines.append(f"[BLOCK {index} TABLE]")
                    for row in block.findall("w:tr", NS):
                        lines.append(" | ".join(visible_text(cell) for cell in row.findall("w:tc", NS)))
            for name in archive.namelist():
                if name.startswith("word/") and ("comments" in name or "footnotes" in name or "endnotes" in name or "header" in name or "footer" in name) and name.endswith(".xml"):
                    lines.append(f"[PART {name}] {visible_text(ET.fromstring(archive.read(name)))}")
            (OUT / (path.stem + ".txt")).write_text("\n".join(lines), encoding="utf-8")
            media = [n for n in archive.namelist() if n.startswith("word/media/")]
            media_out = OUT / "embedded_media" / path.stem
            media_out.mkdir(parents=True, exist_ok=True)
            for name in media:
                (media_out / Path(name).name).write_bytes(archive.read(name))
            print(json.dumps({"document": path.name, "blocks": len(body), "tables": len(root.findall(".//w:tbl", NS)), "equations": len(root.findall(".//m:oMath", NS)), "media": len(media), "tracked_insertions": len(root.findall(".//w:ins", NS)), "tracked_deletions": len(root.findall(".//w:del", NS))}, ensure_ascii=False))
(OUT / "source_manifest.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Inspected {len(inventory)} original files")
