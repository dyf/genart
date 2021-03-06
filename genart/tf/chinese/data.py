import os
import pandas as pd
import imageio
import numpy as np
from PIL import ImageFont, ImageDraw, Image
import glob
import unicodedata
import re
import enum

FONT_DIR = 'data/chinese/ttf'
DEFAULT_INDEX = 'data/chinese/rendered_chinese_characters.csv'
DEFAULT_VARIANT_LOOKUP_FILE = 'data/chinese/Unihan_Variants.txt'
DEFAULT_VARIANT_IMAGE_FILE = 'data/chinese/rendered_variants.csv'
RENDERED_IMAGE_DIR = 'data/chinese/rendered'

@enum.unique
class CharacterClass(enum.Enum):
    FAKE = 0
    TRADITIONAL = 1
    SIMPLIFIED = 2

def classify_character_from_filename(fname):
    fname_lower = fname.lower()
    
    if 'traditional' in fname_lower:
        return CharacterClass.TRADITIONAL
    elif 'simplified' in fname_lower:
        return CharacterClass.SIMPLIFIED

    return CharacterClass.UNKNOWN

def build_index(df, fonts, out_dir):
    files = []

    for font in fonts:
        font_name = os.path.basename(os.path.splitext(font)[0])
                        
        for idx, row in df.iterrows():
            trad_char = row['traditional_char']
            simp_char = row['simplified_char']

            trad_file = os.path.normpath(os.path.join(out_dir, font_name, trad_char + '.png'))
            simp_file = os.path.normpath(os.path.join(out_dir, font_name, simp_char + '.png'))

            is_both = trad_char == simp_char
            
            if os.path.exists(trad_file):

                files.append({
                    'font': font_name,
                    #'class': CharacterClass.BOTH if is_both else CharacterClass.TRADITIONAL, 
                    'class_name': CharacterClass.TRADITIONAL.name, 
                    'class_code': CharacterClass.TRADITIONAL.value, 
                    'character': trad_char,
                    'file': trad_file
                })
            
            if (not is_both) and os.path.exists(simp_file):
                files.append({
                    'font': font_name,
                    'class_name': CharacterClass.SIMPLIFIED.name,
                    'class_code': CharacterClass.SIMPLIFIED.value,
                    'character': simp_char,
                    'file': simp_file
                })

    df = pd.DataFrame.from_records(files).drop_duplicates(ignore_index=True)

    lut = font_lut(df['font'])    
    df['font_code'] = df['font'].apply(lambda x: lut[x])

    return df


def string_code(s):
    return re.sub('<.*', '', s.split()[0])

def decode_string(s):    
    return s.replace('U+','\\u').encode('latin1').decode('unicode-escape')
    
def valid_range(val):
    vint = int(val[2:],16)
    valid_ranges =  [0x4E00, 0x62FF], [0x6300, 0x77FF], [0x7800, 0x8CFF], [0x8D00, 0x9FFF]

    return any( (vint >= vr[0]) & (vint <= vr[1]) for vr in valid_ranges )

def font_lut(series):
    font_names = series.unique()
    font_names = ["FAKE"] + sorted(font_names)

    return dict(zip(font_names, range(len(font_names))))

def load_variant_lookup(path=DEFAULT_VARIANT_LOOKUP_FILE):
    df = pd.read_csv(path, comment='#', sep='\t', header=None, names=['from_code','type','to_code'])        

    # clean, choose one (the first)
    df['from_code'] = df['from_code'].apply(string_code)
    df['to_code'] = df['to_code'].apply(string_code)

    
    # only use valid range
    df = df[df['from_code'].apply(valid_range)&df['to_code'].apply(valid_range)]

    df = df[df['type']=='kSimplifiedVariant']
    df['traditional_char'] = df['from_code'].apply(decode_string)
    df['simplified_char'] = df['to_code'].apply(decode_string)
            
    return df[(df['simplified_char']!="")&(df['traditional_char']!="")]

def load(index_path=DEFAULT_INDEX):
    return pd.read_csv(index_path)

def iterdata(index_path=DEFAULT_INDEX, batch_size=10, shuffle=True, random_seed=None):    
    df = load(index_path=index_path)
   
    if shuffle:
        df = df.sample(frac=1, random_state=random_seed)

    for i in range(0, len(df), batch_size):
        rows = df[i:i+batch_size]

        images = []
        for fname in rows.file:
            images.append(imageio.imread(fname))
        
        images = np.array(images, dtype='float32') / 255.0 * 2.0 - 1.0
        s = images.shape
        images = images.reshape([s[0], s[1], s[2], 1])
        yield rows, images

def load_variant_images(image_index_path=DEFAULT_INDEX, variant_path=DEFAULT_VARIANT_LOOKUP_FILE):
    images = load(image_index_path)
    variants = load_variant_lookup(variant_path)
    font_codes = images['font_code'].unique()    

    out = []
    for fc in font_codes:
        for vi,v in variants.iterrows():
            trad_image = images[(images['character']==v['traditional_char'])&(images['font_code']==fc)]
            simp_image = images[(images['character']==v['simplified_char'])&(images['font_code']==fc)]
            
            try:
                tf = trad_image['file'].values[0]
                sf = simp_image['file'].values[0]
            except IndexError:
                print("skipping: ", v)
                continue

            out.append({
                'font_code': fc,
                'traditional_char': v['traditional_char'],
                'simplified_char': v['simplified_char'],
                'traditional_file': tf,
                'simplified_file': sf
            })
            
    return pd.DataFrame.from_records(out)


def iterdata_variants(variant_image_path=DEFAULT_VARIANT_IMAGE_FILE, shuffle=True, random_seed=None, split_range=None):
    df = pd.read_csv(variant_image_path)

    if split_range is not None:
        n = len(df)
        idx_range = [ int(split_range[0]*n), int(split_range[1]*n) ]
        df = df[idx_range[0]:idx_range[1]]

    if shuffle:
        df = df.sample(frac=1, random_state=random_seed)
    
    for idx,row in df.iterrows():
        trad_image = imageio.imread(row['traditional_file'])
        simp_image = imageio.imread(row['simplified_file'])
        
        trad_image = trad_image.astype(np.float32) / 255.0 * 2.0 - 1.0
        simp_image = simp_image.astype(np.float32) / 255.0 * 2.0 - 1.0
        
        s = trad_image.shape
        new_shape = [s[0], s[1],  1]        

        yield trad_image.reshape(new_shape), simp_image.reshape(new_shape)

def list_available_font_ttfs(basedir=FONT_DIR):
    fonts = glob.glob(basedir + "/*.ttf")
    return [ os.path.normpath(f) for f in fonts]

def render_font(msg, font_file, image_file):
    bigW, bigH = 256,256
    W,H = 128,128
    pt = 128
    padding = 5

    image = Image.new(mode='L', size=[W,H], color='white')
    image_big = Image.new(mode='L', size=[bigW,bigH], color='white')

    draw = ImageDraw.Draw(image)
    draw_big = ImageDraw.Draw(image_big)

    # use a truetype font
    font = ImageFont.truetype(font_file, pt, encoding='unic')
    
    w,h = (pt, pt)    
    #draw.text( ( (W-w)//2, (H-h)//2 ), msg, fill="black", font=font)
    draw_big.text( (0,0), msg, fill="black", font=font)
    im_array = np.asarray(image_big)
    pr, pc = np.where(im_array < 255)
    rmin, rmax, cmin, cmax = pr.min(), pr.max(), pc.min(), pc.max()
    charw, charh = rmax-rmin, cmax-cmin
    cent_r, cent_c = pr.mean(), pc.mean()
   
    pos = W // 2 - cent_c, H // 2 - cent_r   

    image.paste( 255, [0,0,image.size[0],image.size[1]])
    draw.text( pos, msg, fill="black", font=font)

    image.save(image_file)

def render_characters(chars, fonts, out_dir):
    for font in fonts:
        font_name = os.path.basename(os.path.splitext(font)[0])
                        
        for char in chars:
            
            image_file = os.path.normpath(os.path.join(out_dir, font_name, char + '.png'))
            
            try:
                os.makedirs(os.path.dirname(image_file))
            except FileExistsError:
                pass

            try:
                render_font(char, font, image_file)
            except Exception as e:
                print(image_file)
                print(e)    

        

if __name__ == "__main__":
    #fonts = list_available_font_ttfs()
    #df = load_variant_lookup()  
    #trad_chars = set(df['traditional_char'].values.tolist())
    #simp_chars =  set(df['simplified_char'].values.tolist())
    #unique_chars =  trad_chars | simp_chars
    #render_characters(unique_chars, fonts, 'chinese/rendered')

    #file_index = build_index(df, fonts, RENDERED_IMAGE_DIR)
    #file_index.to_csv(DEFAULT_INDEX, index=False)
    
    df = load_variant_images()
    df = df.sample(frac=1)
    df.to_csv(DEFAULT_VARIANT_IMAGE_FILE, index=False)
    
