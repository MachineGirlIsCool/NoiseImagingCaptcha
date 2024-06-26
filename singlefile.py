# Please install modules from requirements.txt before usage.
import numpy as np
import PIL, PIL.ImageFilter, PIL.ImageDraw, PIL.ImageFont
import matplotlib as mpl
import matplotlib.pyplot as plt

# Make noise with dimensions (h, w)
def noise_make(h, w):
    return np.random.rand(h, w)

# Convert float values of pixels into corresponding hex colors of colormap
def noise_image(a, cmap=mpl.cm.Paired, *args, **kwargs):
    return (255 * cmap(a)[:, :, :3]).astype(np.uint8)

# Change random pixels of noise, mr is fraction of changed pixels
def noise_mutate(a, mr=0):
    h, w = a.shape[0], a.shape[1]
    c = int(h * w * mr)
    a[np.random.randint(0, h, c), np.random.randint(0, w, c)] = np.random.rand(c)

# Shift image torus-like by 2d vector
def shift_2d(a, v):
    return np.roll(np.roll(a, v[0], 0), v[1], 1)

# Generate shift sequence with cnt shifts, each with smoothness factor (max abs change for each coordinate) sf. Also bounding box (lx, hx, ly, hy) should always be in bounds of picture
def shift_seq(lx, hx, ly, hy, cnt=1, sf=10, *args, **kwargs):
    res = []
    cum = [0, 0]
    for it in range(cnt):
        cv = [np.random.randint(max(lx - cum[0], -sf), min(hx - cum[0], sf)), np.random.randint(max(ly - cum[1], -sf), min(hy - cum[1], sf))]
        cum[0] += cv[0]
        cum[1] += cv[1]
        res.append(cv)
    return np.array(res)

# Find bounding box of 1s in 0/1 array
def bbox(a): # we except a to be array of 0s ans 1s
    x, y, _ = np.where(a == 1)
    return np.min(x), np.max(x), np.min(y), np.max(y)

# Find contour of width d and bounding box for image
def get_zones(img, edge=4): # returns (wb, g, bbox)
    if edge & 1:
        raise Exception("Parameter d (edge) must be even.")
    wb_mask = np.asarray(img).mean(axis=-1, keepdims=True) > 127
    fimg = img.filter(PIL.ImageFilter.MaxFilter(edge + 1))
    wb_mask_f = np.asarray(fimg).mean(axis=-1, keepdims=True) > 127
    box = bbox(wb_mask_f)
    return wb_mask, (1 - wb_mask) * wb_mask_f, box

# Compile zones and noises into one image
def make_frame(mwb, mg, nw, nb, ng, *args, **kwargs):
    return PIL.Image.fromarray(np.where(mg, noise_image(ng, *args, **kwargs), np.where(mwb, noise_image(nw, *args, **kwargs), noise_image(nb, *args, **kwargs))))

# Return series of images generated by series of shifts
def make_gif_shift(img, frames=50, coef=0.04, *args, **kwargs):
    w, h = img.size
    nw, nb, ng = noise_make(h, w), noise_make(h, w), noise_make(h, w)
    mwb, mg, box = get_zones(img, *args, **kwargs)
    shifts = shift_seq(-box[0], h - box[1], -box[2], w - box[3], cnt=frames, *args, **kwargs)
    gif = []
    for it in range(frames):
        mwb = shift_2d(mwb, shifts[it])
        mg = shift_2d(mg, shifts[it])
        noise_mutate(nw, coef)
        noise_mutate(nb, coef)
        ng = noise_make(h, w)
        gif.append(make_frame(mwb, mg, nw, nb, ng, *args, **kwargs))
    return gif

# Generate captcha using words. It works perfect with [3; 7] words of length [4; 7] and font Golos Regular, needs calibration on other configs
def captcha_words(save_path, words_path, cnt=5, font_path=None, *args, **kwargs):
    if cnt < 3 or cnt > 7:
        raise Exception(f"Excepted from 3 to 7 words, got {cnt}.")
    words = open(words_path, 'r').read().split('\n')[:-1]
    sample = np.random.choice(words, cnt)
    mask = PIL.Image.new("RGB", (500, 200))
    if font_path:
        font12 = PIL.ImageFont.truetype(font_path, 12)
        font100 = PIL.ImageFont.truetype(font_path, 100)
    else:
        font12 = PIL.ImageFont.load_default(12)
        font100 = PIL.ImageFont.load_default(100)
    draw_mask = PIL.ImageDraw.Draw(mask)
    draw_mask.text((np.random.randint(0, 70), np.random.randint(0, 70)), sample[np.random.randint(0, cnt)], font=font100, fill=(255, 255, 255))
    noise_gif = make_gif_shift(mask, *args, **kwargs)
    template = PIL.Image.new("RGB", (500, 225))
    draw_template = PIL.ImageDraw.Draw(template)
    for i in range(cnt):
        draw_template.text((10 + (480 // cnt) * i, 0), sample[i], font=font12, fill=(255, 255, 255))
    gif = []
    for frame in noise_gif:
        cur_frame = template.copy()
        cur_frame.paste(frame, (0, 25))
        gif.append(cur_frame)
    gif[0].save(save_path, save_all=True, optimize=True, append_images=gif[1:], duration=50, loop=0)

# Example:
# captcha_words("captcha/fin_test.gif", "words.txt", font_path="golos-text_regular.ttf", cnt=7, edge=6, frames=120)
