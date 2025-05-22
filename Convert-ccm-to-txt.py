import struct
from enum import IntEnum
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass

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

# ساختار CodeGroup
@dataclass
class CodeGroup:
    start_code: int
    end_code: int
    glyph_index: int

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
        self.version: CCMVer = CCMVer.DemonsSouls
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
            if self.version in (CCMVer.DemonsSouls, CCMVer.DarkSouls1):
                code_groups = []
                for _ in range(code_group_count):
                    start_code = struct.unpack(f'{endian}i', f.read(4))[0]
                    end_code = struct.unpack(f'{endian}i', f.read(4))[0]
                    glyph_index = struct.unpack(f'{endian}i', f.read(4))[0]
                    code_groups.append(CodeGroup(start_code, end_code, glyph_index))

                glyphs = []
                for _ in range(glyph_count):
                    uv1_x = struct.unpack(f'{endian}f', f.read(4))[0]
                    uv1_y = struct.unpack(f'{endian}f', f.read(4))[0]
                    uv2_x = struct.unpack(f'{endian}f', f.read(4))[0]
                    uv2_y = struct.unpack(f'{endian}f', f.read(4))[0]
                    pre_space = struct.unpack(f'{endian}h', f.read(2))[0]
                    width = struct.unpack(f'{endian}h', f.read(2))[0]
                    advance = struct.unpack(f'{endian}h', f.read(2))[0]
                    tex_index = struct.unpack(f'{endian}h', f.read(2))[0]
                    glyphs.append(Glyph((uv1_x, uv1_y), (uv2_x, uv2_y), pre_space, width, advance, tex_index))

                for group in code_groups:
                    code_count = group.end_code - group.start_code + 1
                    for i in range(code_count):
                        self.glyphs[group.start_code + i] = glyphs[group.glyph_index + i]
            else:
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

# تابع برای تبدیل CCM به فایل متنی با فرمت مشابه .fnt
def ccm_to_fnt_txt(ccm_file_path: str, txt_file_path: str):
    # خواندن فایل CCM
    ccm = CCM()
    ccm.read(ccm_file_path)

    # نوشتن اطلاعات به فایل متنی
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        # بخش info (مقادیر پیش‌فرض برای موارد نامشخص)
        f.write('info face="Arial" size=32 bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1 outline=0\n')
        
        # بخش common
        line_height = ccm.full_width  # فرض: lineHeight برابر با full_width
        base = int(line_height * 0.8)  # فرض: base حدود 80% lineHeight
        f.write(f'common lineHeight={line_height} base={base} scaleW={ccm.tex_width} scaleH={ccm.tex_height} '
                f'pages={ccm.tex_count} packed=0 alphaChnl=1 redChnl=0 greenChnl=0 blueChnl=0\n')
        
        # بخش page
        for i in range(ccm.tex_count):
            f.write(f'page id={i} file="DarkSouls2_{i}.dds"\n')
        
        # بخش chars
        f.write(f'chars count={len(ccm.glyphs)}\n')
        
        # نوشتن اطلاعات Glyphها
        for code, glyph in sorted(ccm.glyphs.items()):
            # تبدیل مختصات UV به پیکسل
            x = round(glyph.uv1[0] * ccm.tex_width)
            y = round(glyph.uv1[1] * ccm.tex_height)
            width = round((glyph.uv2[0] - glyph.uv1[0]) * ccm.tex_width)
            height = round((glyph.uv2[1] - glyph.uv1[1]) * ccm.tex_height)
            
            # افست‌ها (فرض: pre_space به عنوان xoffset و yoffset به صورت پیش‌فرض)
            xoffset = glyph.pre_space
            yoffset = 6  # مقدار پیش‌فرض مشابه نمونه
            xadvance = glyph.advance
            
            f.write(f'char id={code:<4} x={x:<5} y={y:<5} width={width:<5} height={height:<5} '
                    f'xoffset={xoffset:<5} yoffset={yoffset:<5} xadvance={xadvance:<5} page={glyph.tex_index} chnl=15\n')

# استفاده از تابع
ccm_file_path = r"E:\Dark Souls 2 - Scholar of the First Sin\font\English\FeFont_Small-fontbnd-dcx\FeFont_Small.ccm"  # مسیر فایل CCM
txt_file_path = "FeFont_Small.txt"  # مسیر فایل متنی خروجی
ccm_to_fnt_txt(ccm_file_path, txt_file_path)
print(f"فایل CCM به {txt_file_path} تبدیل شد.")