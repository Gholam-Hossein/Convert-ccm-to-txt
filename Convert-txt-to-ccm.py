import struct
from enum import IntEnum
from typing import Dict, Tuple, Set
from dataclasses import dataclass
import re

# تعریف نسخه‌های CCM
class CCMVer(IntEnum):
    DemonsSouls = 0x100
    DarkSouls1 = 0x10001
    DarkSouls2 = 0x20000

# کلاس Glyph
@dataclass
class Glyph:
    uv1: Tuple[float, float]
    uv2: Tuple[float, float]
    pre_space: int
    width: int
    advance: int
    tex_index: int

# ساختار TexRegion
@dataclass
class TexRegion:
    x1: int
    y1: int
    x2: int
    y2: int

    def __eq__(self, other):
        if not isinstance(other, TexRegion):
            return False
        return self.x1 == other.x1 and self.y1 == other.y1 and self.x2 == other.x2 and self.y2 == other.y2

    def __hash__(self):
        return hash((self.x1, self.y1, self.x2, self.y2))

# کلاس CCM
class CCM:
    def __init__(self):
        self.version: CCMVer = CCMVer.DarkSouls2
        self.full_width: int = 0
        self.tex_width: int = 0
        self.tex_height: int = 0
        self.unk0e: int = 0
        self.unk1c: int = 0
        self.unk1d: int = 0
        self.tex_count: int = 0
        self.glyphs: Dict[int, Glyph] = {}

    def read(self, file_path: str):
        with open(file_path, 'rb') as f:
            big_endian = False
            self.version = CCMVer(struct.unpack('<I', f.read(4))[0])
            if self.version == CCMVer.DemonsSouls:
                big_endian = True
            endian = '>' if big_endian else '<'

            file_size = struct.unpack(f'{endian}i', f.read(4))[0]
            self.full_width = struct.unpack(f'{endian}h', f.read(2))[0]
            self.tex_width = struct.unpack(f'{endian}h', f.read(2))[0]
            self.tex_height = struct.unpack(f'{endian}h', f.read(2))[0]

            if self.version in (CCMVer.DemonsSouls, CCMVer.DarkSouls1):
                self.unk0e = struct.unpack(f'{endian}h', f.read(2))[0]
                code_group_count = struct.unpack(f'{endian}h', f.read(2))[0]
                tex_region_count = -1
                glyph_count = struct.unpack(f'{endian}h', f.read(2))[0]
            else:
                self.unk0e = 0
                code_group_count = -1
                tex_region_count = struct.unpack(f'{endian}h', f.read(2))[0]
                glyph_count = struct.unpack(f'{endian}h', f.read(2))[0]
                assert struct.unpack(f'{endian}h', f.read(2))[0] == 0

            assert struct.unpack(f'{endian}i', f.read(4))[0] == 0x20
            glyph_offset = struct.unpack(f'{endian}i', f.read(4))[0]
            self.unk1c = struct.unpack('B', f.read(1))[0]
            self.unk1d = struct.unpack('B', f.read(1))[0]
            self.tex_count = struct.unpack('B', f.read(1))[0]
            assert struct.unpack('B', f.read(1))[0] == 0

            self.glyphs = {}
            if self.version == CCMVer.DarkSouls2:
                tex_regions = {}
                for _ in range(tex_region_count):
                    pos = f.tell()
                    x1 = struct.unpack(f'{endian}h', f.read(2))[0]
                    y1 = struct.unpack(f'{endian}h', f.read(2))[0]
                    x2 = struct.unpack(f'{endian}h', f.read(2))[0]
                    y2 = struct.unpack(f'{endian}h', f.read(2))[0]
                    tex_regions[pos] = TexRegion(x1, y1, x2, y2)

                for _ in range(glyph_count):
                    code = struct.unpack(f'{endian}i', f.read(4))[0]
                    tex_region_offset = struct.unpack(f'{endian}i', f.read(4))[0]
                    tex_index = struct.unpack(f'{endian}h', f.read(2))[0]
                    pre_space = struct.unpack(f'{endian}h', f.read(2))[0]
                    width = struct.unpack(f'{endian}h', f.read(2))[0]
                    advance = struct.unpack(f'{endian}h', f.read(2))[0]
                    assert struct.unpack(f'{endian}i', f.read(4))[0] == 0
                    assert struct.unpack(f'{endian}i', f.read(4))[0] == 0

                    tex_region = tex_regions[tex_region_offset]
                    uv1 = (tex_region.x1 / self.tex_width, tex_region.y1 / self.tex_height)
                    uv2 = (tex_region.x2 / self.tex_width, tex_region.y2 / self.tex_height)
                    self.glyphs[code] = Glyph(uv1, uv2, pre_space, width, advance, tex_index)

    def write(self, file_path: str):
        with open(file_path, 'wb') as f:
            endian = '<'  # DarkSouls2 از little-endian استفاده می‌کند

            # نوشتن هدر
            f.write(struct.pack(f'{endian}I', self.version))
            file_size_offset = f.tell()
            f.write(struct.pack(f'{endian}i', 0))  # Placeholder for file size
            f.write(struct.pack(f'{endian}h', self.full_width))
            f.write(struct.pack(f'{endian}h', self.tex_width))
            f.write(struct.pack(f'{endian}h', self.tex_height))
            
            # For DarkSouls2 format
            f.write(struct.pack(f'{endian}h', len(self.glyphs)))  # tex_region_count
            f.write(struct.pack(f'{endian}h', len(self.glyphs)))  # glyph_count
            f.write(struct.pack(f'{endian}h', 0))  # padding
            
            f.write(struct.pack(f'{endian}i', 0x20))  # offset check
            glyph_offset_pos = f.tell()
            f.write(struct.pack(f'{endian}i', 0))  # Placeholder for glyph offset
            
            # Write header values
            f.write(struct.pack('B', self.unk1c))
            f.write(struct.pack('B', self.unk1d))
            f.write(struct.pack('B', self.tex_count))
            f.write(struct.pack('B', 0))  # padding byte

            # Prepare tex regions
            codes = sorted(self.glyphs.keys())
            tex_regions = []
            tex_region_offsets = {}
            
            # Calculate tex regions first
            for code in codes:
                glyph = self.glyphs[code]
                x1 = round(glyph.uv1[0] * self.tex_width)
                y1 = round(glyph.uv1[1] * self.tex_height)
                x2 = round(glyph.uv2[0] * self.tex_width)
                y2 = round(glyph.uv2[1] * self.tex_height)
                region = TexRegion(x1, y1, x2, y2)
                tex_regions.append(region)

            # Write tex regions
            current_pos = f.tell()
            for region in tex_regions:
                tex_region_offsets[region] = current_pos
                f.write(struct.pack(f'{endian}h', region.x1))
                f.write(struct.pack(f'{endian}h', region.y1))
                f.write(struct.pack(f'{endian}h', region.x2))
                f.write(struct.pack(f'{endian}h', region.y2))
                current_pos += 8  # 4 shorts * 2 bytes each

            # Update glyph offset
            glyph_offset = f.tell()
            f.seek(glyph_offset_pos)
            f.write(struct.pack(f'{endian}i', glyph_offset))
            f.seek(glyph_offset)

            # Write glyphs
            for i, code in enumerate(codes):
                glyph = self.glyphs[code]
                region = tex_regions[i]
                
                f.write(struct.pack(f'{endian}i', code))
                f.write(struct.pack(f'{endian}i', tex_region_offsets[region]))
                f.write(struct.pack(f'{endian}h', glyph.tex_index))
                f.write(struct.pack(f'{endian}h', glyph.pre_space))
                f.write(struct.pack(f'{endian}h', glyph.width))
                f.write(struct.pack(f'{endian}h', glyph.advance))
                f.write(struct.pack(f'{endian}i', 0))  # padding
                f.write(struct.pack(f'{endian}i', 0))  # padding

            # Update file size
            file_size = f.tell()
            f.seek(file_size_offset)
            f.write(struct.pack(f'{endian}i', file_size))

# تابع برای تبدیل txt به CCM با استفاده از فایل اصلی
def txt_to_ccm_with_original(original_ccm_path: str, txt_file_path: str, ccm_file_path: str):
    # Read original CCM
    original_ccm = CCM()
    original_ccm.read(original_ccm_path)

    # Create new CCM with all original header values
    ccm = CCM()
    ccm.version = original_ccm.version
    ccm.full_width = original_ccm.full_width
    ccm.tex_width = original_ccm.tex_width
    ccm.tex_height = original_ccm.tex_height
    ccm.unk0e = original_ccm.unk0e
    ccm.unk1c = original_ccm.unk1c
    ccm.unk1d = original_ccm.unk1d
    ccm.tex_count = original_ccm.tex_count
    ccm.glyphs = {}

    # خواندن اطلاعات کاراکترها از فایل متنی
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith('char id='):
            match = re.match(r'char id=(\d+)\s+x=(\d+)\s+y=(\d+)\s+width=(\d+)\s+height=(\d+)\s+xoffset=(-?\d+)\s+yoffset=\d+\s+xadvance=(\d+)\s+page=(\d+)\s+chnl=\d+', line)
            if match:
                code = int(match.group(1))
                x = int(match.group(2))
                y = int(match.group(3))
                width = int(match.group(4))
                height = int(match.group(5))
                xoffset = int(match.group(6))
                xadvance = int(match.group(7))
                tex_index = int(match.group(8))

                # تبدیل مختصات پیکسلی به UV
                uv1_x = x / ccm.tex_width
                uv1_y = y / ccm.tex_height
                uv2_x = (x + width) / ccm.tex_width
                uv2_y = (y + height) / ccm.tex_height

                # ایجاد Glyph
                ccm.glyphs[code] = Glyph(
                    uv1=(uv1_x, uv1_y),
                    uv2=(uv2_x, uv2_y),
                    pre_space=xoffset,
                    width=width,
                    advance=xadvance,
                    tex_index=tex_index
                )

    # نوشتن به فایل CCM
    ccm.write(ccm_file_path)
    print(f"فایل متنی به {ccm_file_path} تبدیل شد.")

# استفاده از تابع
original_ccm_path = "FeFont_Small_original.ccm"  # مسیر فایل اصلی CCM
txt_file_path = "FeFont_Small.txt"  # مسیر فایل متنی
ccm_file_path = "FeFont_Small_new.ccm"  # مسیر فایل CCM خروجی
txt_to_ccm_with_original(original_ccm_path, txt_file_path, ccm_file_path)