"""Run with: python3 tests/check_profile.py (stdlib only)."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / "README.md").read_text()

assert "September 2025–Present" in readme
assert "Head of R&D at Vermiliom" in readme
assert "Viserys89/vermillionerp" in readme, "Keep upstream attribution"
for placeholder in ("yourusername", "yourprofile", "coming soon", "2+ years"):
    assert placeholder not in readme.lower(), placeholder
assert readme.count("<details>") == readme.count("</details>") == 6
assert readme.count("<summary>") == readme.count("</summary>") == 6

assets = set(re.findall(r"assets/[\w.-]+", readme))
assert assets, "Missing local artwork"
for asset in assets:
    path = ROOT / asset
    assert path.is_file(), f"Missing asset: {asset}"
    assert path.stat().st_size < 300_000, f"Oversized asset: {asset}"
    if path.suffix == ".svg":
        tree = ET.parse(path)
        tags = {node.tag.split('}')[-1] for node in tree.iter()}
        assert "title" in tags
        assert not {"script", "foreignObject"} & tags
        for node in tree.iter():
            if node.tag.endswith('}image'):
                assert node.attrib.get('href', '').startswith('data:image/svg+xml;base64,'), 'External SVG image dependency'
        source = path.read_text()
        if '@keyframes' in source:
            assert "prefers-reduced-motion" in source
            assert "infinite" not in source

for alt in re.findall(r"!\[([^]]*)\]\(", readme):
    assert alt.strip(), "Empty image description"
for image in re.findall(r"<img\b[^>]*>", readme):
    assert re.search(r'alt="[^"]+"', image), "Missing image alt text"

headings = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
            for h in re.findall(r"^## (.+)$", readme, re.M)}
for anchor in re.findall(r"\]\(#([\w-]+)\)", readme):
    assert anchor in headings, f"Broken section link: {anchor}"
for technology in ('Rust', 'Electron', 'Tauri', 'Hono', 'Tailscale'):
    assert f'alt="{technology}"' in readme
assert len(list((ROOT / 'assets').glob('tech-*.svg'))) == 29
print(f"Profile checks passed: {len(assets)} assets, 6 disclosures, 29 stack badges, section links, attribution, accessibility safeguards.")
