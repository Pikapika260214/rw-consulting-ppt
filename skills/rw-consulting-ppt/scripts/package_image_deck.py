#!/usr/bin/env python3
"""Package full-slide PNGs into an image-only PPTX and validate the result."""

from __future__ import annotations

import argparse
import html
import math
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path


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


def slide_xml(image_name: str) -> str:
    safe_name = html.escape(image_name)
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
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


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
<a:theme xmlns:a="{NS_A}" name="RW Consulting">
  <a:themeElements>
    <a:clrScheme name="RW"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="1E5BFF"/></a:accent1><a:accent2><a:srgbClr val="F59E0B"/></a:accent2><a:accent3><a:srgbClr val="94A3B8"/></a:accent3><a:accent4><a:srgbClr val="CBD5E1"/></a:accent4><a:accent5><a:srgbClr val="0F172A"/></a:accent5><a:accent6><a:srgbClr val="64748B"/></a:accent6><a:hlink><a:srgbClr val="1E5BFF"/></a:hlink><a:folHlink><a:srgbClr val="475569"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="RW"><a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="RW"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>'''


def core_props(title: str) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    safe_title = html.escape(title)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="{NS_CP}" xmlns:dc="{NS_DC}" xmlns:dcterms="{NS_DCTERMS}" xmlns:xsi="{NS_XSI}">
  <dc:title>{safe_title}</dc:title>
  <dc:creator>RW Consulting PPT</dc:creator>
  <cp:lastModifiedBy>RW Consulting PPT</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def app_props(slide_count: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>RW Consulting PPT</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>{slide_count}</Slides>
</Properties>'''


def build_contact_sheet(images: list[Path], output: Path) -> None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return
    thumbs = []
    for path in images:
        img = Image.open(path).convert("RGB")
        img.thumbnail((520, 292))
        thumbs.append((path, img.copy()))
    cols = 2
    rows = math.ceil(len(thumbs) / cols)
    pad = 28
    label_h = 28
    cell_w = 560
    cell_h = 340
    sheet = Image.new("RGB", (cols * cell_w + pad, rows * cell_h + pad), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (path, img) in enumerate(thumbs):
        col = idx % cols
        row = idx // cols
        x = pad + col * cell_w
        y = pad + row * cell_h
        sheet.paste(img, (x, y + label_h))
        draw.text((x, y), path.stem, fill=(31, 41, 55))
    sheet.save(output)


def write_pptx(images: list[Path], output: Path, title: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(images)))
        z.writestr("_rels/.rels", rels([
            ("rId1", f"{NS_P_REL}/officeDocument", "ppt/presentation.xml"),
            ("rId2", f"{NS_P_REL}/metadata/core-properties", "docProps/core.xml"),
            ("rId3", f"{NS_P_REL}/extended-properties", "docProps/app.xml"),
        ]))
        z.writestr("docProps/core.xml", core_props(title))
        z.writestr("docProps/app.xml", app_props(len(images)))
        z.writestr("ppt/presentation.xml", presentation_xml(len(images)))
        z.writestr("ppt/_rels/presentation.xml.rels", rels(
            [("rId1", f"{NS_P_REL}/slideMaster", "slideMasters/slideMaster1.xml")]
            + [(f"rId{i + 1}", f"{NS_P_REL}/slide", f"slides/slide{i}.xml") for i in range(1, len(images) + 1)]
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
        for idx, image in enumerate(images, start=1):
            z.write(image, f"ppt/media/image{idx}.png")
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(image.name))
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
        "pictures": picture_count,
        "editableTextBodies": text_body_count,
        "editableShapes": shape_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="Image-only consulting deck")
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()

    images = sorted(args.image_dir.glob("slide_*.png"))
    if not images:
        raise SystemExit(f"No slide_*.png files found in {args.image_dir}")

    for image in images:
        w, h = read_png_size(image)
        if abs((w / h) - (16 / 9)) > 0.01:
            raise SystemExit(f"{image.name} is not 16:9: {w}x{h}")

    write_pptx(images, args.out, args.title)
    if args.contact_sheet:
        build_contact_sheet(images, args.contact_sheet)

    validation = validate_pptx(args.out)
    for key, value in validation.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
