#!/usr/bin/env python3
"""Package clean slide backgrounds plus editable text boxes into a PPTX."""

from __future__ import annotations

import argparse
import html
import json
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EMU_PER_INCH = 914400
SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
EMU_WIDE_W = 12192000
EMU_WIDE_H = 6858000

NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_P_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


def read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


def clean_hex(value: str | None, default: str = "111111") -> str:
    if not value:
        return default
    value = value.strip().lstrip("#")
    if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        return default
    return value.upper()


def bool_attr(name: str, enabled: bool | None) -> str:
    return f' {name}="1"' if enabled else ""


def rels(items: list[tuple[str, str, str]]) -> str:
    body = "\n".join(
        f'<Relationship Id="{rid}" Type="{typ}" Target="{html.escape(target)}"/>'
        for rid, typ, target in items
    )
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{NS_REL}">\n{body}\n</Relationships>'


def content_types(slide_count: int) -> str:
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{NS_CT}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>'''


def presentation_xml(slide_count: int) -> str:
    slides = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>'
        for i in range(1, slide_count + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{NS_A}" xmlns:r="{NS_P_REL}" xmlns:p="{NS_P}">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{slides}</p:sldIdLst>
  <p:sldSz cx="{EMU_WIDE_W}" cy="{EMU_WIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle>
</p:presentation>'''


def slide_master_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{NS_A}" xmlns:r="{NS_P_REL}" xmlns:p="{NS_P}">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>'''


def slide_layout_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{NS_A}" xmlns:r="{NS_P_REL}" xmlns:p="{NS_P}" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''


def theme_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{NS_A}" name="PPT to Editable">
  <a:themeElements>
    <a:clrScheme name="PPT to Editable"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="1E5BFF"/></a:accent1><a:accent2><a:srgbClr val="F59E0B"/></a:accent2><a:accent3><a:srgbClr val="94A3B8"/></a:accent3><a:accent4><a:srgbClr val="CBD5E1"/></a:accent4><a:accent5><a:srgbClr val="0F172A"/></a:accent5><a:accent6><a:srgbClr val="64748B"/></a:accent6><a:hlink><a:srgbClr val="1E5BFF"/></a:hlink><a:folHlink><a:srgbClr val="475569"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="PPT to Editable"><a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="PPT to Editable"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>'''


def core_props(title: str) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    safe_title = html.escape(title)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="{NS_CP}" xmlns:dc="{NS_DC}" xmlns:dcterms="{NS_DCTERMS}" xmlns:xsi="{NS_XSI}">
  <dc:title>{safe_title}</dc:title>
  <dc:creator>PPT to Editable</dc:creator>
  <cp:lastModifiedBy>PPT to Editable</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def app_props(slide_count: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>PPT to Editable</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>{slide_count}</Slides>
</Properties>'''


def pos_emu(value: float, axis: str, units: str) -> int:
    if units == "normalized":
        inches = value * (SLIDE_W_IN if axis == "x" else SLIDE_H_IN)
    else:
        inches = value
    return int(round(inches * EMU_PER_INCH))


def size_emu(value: float, axis: str, units: str) -> int:
    return pos_emu(value, axis, units)


def paragraph_xml(text: str, box: dict[str, Any]) -> str:
    align = {"left": "l", "center": "ctr", "right": "r"}.get(str(box.get("align", "left")).lower(), "l")
    font_size = int(round(float(box.get("font_size", 14)) * 100))
    line_spacing = box.get("line_spacing")
    line_spacing_xml = ""
    if line_spacing is not None:
        spacing_pct = max(100000, int(round(float(line_spacing) * 100000)))
        line_spacing_xml = f'<a:lnSpc><a:spcPct val="{spacing_pct}"/></a:lnSpc>'
    color = clean_hex(box.get("color"))
    font_face = html.escape(str(box.get("font_face", "Aptos")))
    east_asian = html.escape(str(box.get("east_asian_font", "Microsoft YaHei")))
    bold = bool_attr("b", bool(box.get("bold", False)))
    italic = bool_attr("i", bool(box.get("italic", False)))
    character_spacing = box.get("character_spacing")
    spacing_attr = ""
    if character_spacing is not None:
        spacing_attr = f' spc="{int(round(float(character_spacing) * 100))}"'
    safe_text = html.escape(text)
    return f'''<a:p>
        <a:pPr algn="{align}">{line_spacing_xml}</a:pPr>
        <a:r>
          <a:rPr lang="zh-CN" sz="{font_size}"{bold}{italic}{spacing_attr}>
            <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
            <a:latin typeface="{font_face}"/>
            <a:ea typeface="{east_asian}"/>
          </a:rPr>
          <a:t>{safe_text}</a:t>
        </a:r>
        <a:endParaRPr lang="zh-CN" sz="{font_size}"/>
      </a:p>'''


def text_box_xml(box: dict[str, Any], shape_id: int, units: str) -> str:
    name = html.escape(str(box.get("name") or box.get("role") or f"Text {shape_id}"))
    x = pos_emu(float(box["x"]), "x", units)
    y = pos_emu(float(box["y"]), "y", units)
    w = size_emu(float(box["w"]), "x", units)
    h = size_emu(float(box["h"]), "y", units)
    valign = {"top": "t", "middle": "ctr", "bottom": "b"}.get(str(box.get("valign", "top")).lower(), "t")
    margin = int(round(float(box.get("margin", 0)) * EMU_PER_INCH))
    wrap = "none" if bool(box.get("no_wrap", False)) else "square"
    autofit_xml = "" if bool(box.get("allow_autofit", False)) else "<a:noAutofit/>"
    paragraphs = "\n      ".join(paragraph_xml(line, box) for line in str(box.get("text", "")).splitlines() or [""])
    return f'''<p:sp>
        <p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="{wrap}" anchor="{valign}" lIns="{margin}" tIns="{margin}" rIns="{margin}" bIns="{margin}">{autofit_xml}</a:bodyPr>
          <a:lstStyle/>
          {paragraphs}
        </p:txBody>
      </p:sp>'''


def slide_xml(image_name: str, text_boxes: list[dict[str, Any]], units: str) -> str:
    safe_name = html.escape(image_name)
    box_xml = "\n      ".join(
        text_box_xml(box, shape_id=idx + 3, units=units)
        for idx, box in enumerate(text_boxes)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{NS_A}" xmlns:r="{NS_P_REL}" xmlns:p="{NS_P}">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{EMU_WIDE_W}" cy="{EMU_WIDE_H}"/><a:chOff x="0" y="0"/><a:chExt cx="{EMU_WIDE_W}" cy="{EMU_WIDE_H}"/></a:xfrm></p:grpSpPr>
      <p:pic>
        <p:nvPicPr><p:cNvPr id="2" name="{safe_name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{EMU_WIDE_W}" cy="{EMU_WIDE_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
      </p:pic>
      {box_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def resolve_background(manifest_path: Path, slide: dict[str, Any], asset_root: Path | None) -> Path:
    raw = Path(str(slide["background"]))
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(manifest_path.parent / raw)
        if asset_root:
            candidates.append(asset_root / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Background not found for slide {slide.get('slide')}: {raw}")


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data.get("slides"), list) or not data["slides"]:
        raise ValueError("Manifest must contain a non-empty slides list")
    return data


def write_pptx(manifest: dict[str, Any], manifest_path: Path, output: Path, asset_root: Path | None) -> None:
    slides = manifest["slides"]
    title = str(manifest.get("title") or "Clean-background editable PPT deck")
    units = str(manifest.get("units", "inches")).lower()
    if units not in {"inches", "normalized"}:
        raise ValueError("Manifest units must be 'inches' or 'normalized'")

    backgrounds = [resolve_background(manifest_path, slide, asset_root) for slide in slides]
    for background in backgrounds:
        w, h = read_png_size(background)
        if abs((w / h) - (16 / 9)) > 0.01:
            raise ValueError(f"{background.name} is not 16:9: {w}x{h}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(slides)))
        z.writestr("_rels/.rels", rels([
            ("rId1", f"{NS_P_REL}/officeDocument", "ppt/presentation.xml"),
            ("rId2", f"{NS_P_REL}/metadata/core-properties", "docProps/core.xml"),
            ("rId3", f"{NS_P_REL}/extended-properties", "docProps/app.xml"),
        ]))
        z.writestr("docProps/core.xml", core_props(title))
        z.writestr("docProps/app.xml", app_props(len(slides)))
        z.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", rels(
            [("rId1", f"{NS_P_REL}/slideMaster", "slideMasters/slideMaster1.xml")]
            + [(f"rId{i + 1}", f"{NS_P_REL}/slide", f"slides/slide{i}.xml") for i in range(1, len(slides) + 1)]
        ))
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([
            ("rId1", f"{NS_P_REL}/slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", f"{NS_P_REL}/theme", "../theme/theme1.xml"),
        ]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([
            ("rId1", f"{NS_P_REL}/slideMaster", "../slideMasters/slideMaster1.xml"),
        ]))
        z.writestr("ppt/theme/theme1.xml", theme_xml())

        for idx, (slide, background) in enumerate(zip(slides, backgrounds), start=1):
            z.write(background, f"ppt/media/image{idx}.png")
            text_boxes = slide.get("text_boxes") or []
            if not isinstance(text_boxes, list):
                raise ValueError(f"Slide {idx} text_boxes must be a list")
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(background.name, text_boxes, units))
            z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", rels([
                ("rId1", f"{NS_P_REL}/slideLayout", "../slideLayouts/slideLayout1.xml"),
                ("rId2", f"{NS_P_REL}/image", f"../media/image{idx}.png"),
            ]))


def validate_pptx(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as z:
        slide_names = sorted(
            [name for name in z.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        )
        picture_count = 0
        text_body_count = 0
        shape_count = 0
        for name in slide_names:
            xml = z.read(name).decode("utf-8", errors="ignore")
            picture_count += xml.count("<p:pic>")
            text_body_count += xml.count("<p:txBody>")
            shape_count += xml.count("<p:sp>")
    return {
        "slides": len(slide_names),
        "backgroundPictures": picture_count,
        "editableTextBodies": text_body_count,
        "editableShapes": shape_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an editable PPTX from clean textless backgrounds and a text manifest.")
    parser.add_argument("manifest", type=Path, help="Path to text_layout_manifest.json")
    parser.add_argument("--out", type=Path, required=True, help="Output PPTX path")
    parser.add_argument("--asset-root", type=Path, help="Optional root for background image paths")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    write_pptx(manifest, args.manifest, args.out, args.asset_root)
    validation = validate_pptx(args.out)
    for key, value in validation.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
