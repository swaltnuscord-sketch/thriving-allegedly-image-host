import base64
from datetime import datetime, timezone
import io
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
HANDLE = "@thri.ving.allegedly"
NAME = "Thriving Allegedly"
PAGES_BASE = "https://swaltnuscord-sketch.github.io/thriving-allegedly-image-host/images"

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_text(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for w in para.split(" "):
            cand = w if not cur else f"{cur} {w}"
            b = draw.textbbox((0, 0), cand, font=font)
            if b[2] - b[0] <= max_w:
                cur = cand
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines

def load_logo(size):
    b64_path = "assets/logo.jpg.b64"
    if os.path.exists(b64_path):
        raw = base64.b64decode(open(b64_path, "r", encoding="utf-8").read().strip())
        img = Image.open(io.BytesIO(raw)).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGBA", (size, size), (255, 59, 154, 255))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    return img, mask

def render_a1_tweet(text, out_path, dark=False):
    bg = "#15202B" if dark else "#FFFFFF"
    fg = "#F7F9F9" if dark else "#0F1419"
    sub = "#8B98A5" if dark else "#536471"
    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)
    mx = random.choice([68, 76, 84])
    f_name = get_font(42, bold=True)
    f_handle = get_font(33, bold=False)
    f_body = get_font(50, bold=False)
    lines = wrap_text(draw, text, f_body, W - 2 * mx)
    lh = 68
    av = 128
    gap = 42
    sy = (H - (av + gap + len(lines) * lh)) // 2
    logo, mask = load_logo(av)
    canvas.paste(logo, (mx, sy), mask)
    draw.text((mx + av + 28, sy + 14), NAME, font=f_name, fill=fg)
    draw.text((mx + av + 28, sy + 68), HANDLE, font=f_handle, fill=sub)
    by = sy + av + gap
    for i, l in enumerate(lines):
        if l:
            draw.text((mx, by + i * lh), l, font=f_body, fill=fg)
    canvas.save(out_path, "JPEG", quality=88, optimize=True)

def render_gradient_card(text, out_path):
    palettes = [
        ((226, 209, 244), (250, 218, 210)),
        ((209, 232, 224), (245, 230, 205)),
        ((244, 214, 220), (252, 244, 228)),
        ((212, 228, 247), (236, 224, 248)),
    ]
    c1, c2 = random.choice(palettes)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    fq = get_font(58, bold=True)
    fwm = get_font(24)
    lines = wrap_text(d, text, fq, W - 180)
    lh = 80
    qy = (H - len(lines) * lh) // 2
    for i, l in enumerate(lines):
        b = d.textbbox((0, 0), l, font=fq)
        d.text(((W - (b[2] - b[0])) // 2, qy + i * lh), l, font=fq, fill="#1E1B24")
    if random.random() > 0.3:
        wb = d.textbbox((0, 0), HANDLE, font=fwm)
        d.text(((W - (wb[2] - wb[0])) // 2, H - 84), HANDLE, font=fwm, fill="#555555")
    img.save(out_path, "JPEG", quality=88, optimize=True)

def render_imessage(msgs, out_path):
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    fsms = get_font(38)
    ftime = get_font(26)
    t_str = random.choice(["Today 8:41 PM", "Today 11:14 AM", "Yesterday 11:52 PM"])
    tb = d.textbbox((0, 0), t_str, font=ftime)
    d.text(((W - (tb[2] - tb[0])) // 2, 290), t_str, font=ftime, fill="#8E8E93")
    yc = 365
    for txt, is_blue in msgs:
        blines = wrap_text(d, txt, fsms, 620)
        lh = 52
        bh = len(blines) * lh + 40
        max_lw = max((d.textbbox((0, 0), l, font=fsms)[2] - d.textbbox((0, 0), l, font=fsms)[0]) for l in blines)
        bw = max_lw + 64
        bx = (W - 76 - bw) if is_blue else 76
        d.rounded_rectangle([bx, yc, bx + bw, yc + bh], radius=34, fill="#007AFF" if is_blue else "#E9E9EB")
        for i, l in enumerate(blines):
            d.text((bx + 32, yc + 20 + i * lh), l, font=fsms, fill="#FFFFFF" if is_blue else "#000000")
        yc += bh + 22
    img.save(out_path, "JPEG", quality=88, optimize=True)

def render_contrast(top_txt, bot_txt, out_path):
    img = Image.new("RGB", (W, H), "#CFE3C8")
    d = ImageDraw.Draw(img)
    d.rectangle([0, H // 2, W, H], fill="#14213D")
    f = get_font(56, bold=True)
    for txt, y0, col in [(top_txt, 0, "#1B3A2B"), (bot_txt, H // 2, "#FFFFFF")]:
        lines = wrap_text(d, txt, f, W - 160)
        lh = 76
        sy = y0 + (H // 2 - len(lines) * lh) // 2
        for i, l in enumerate(lines):
            d.text((80, sy + i * lh), l, font=f, fill=col)
    img.save(out_path, "JPEG", quality=88, optimize=True)

TWEET_POOL = [
    "my favorite hobby is saying 'let's catch up soon!' to people i will not speak to until 2028",
    "nothing humbles you faster than hearing your own voice in a voice note you accidentally played out loud",
    "me: i should really start going to bed early\n\nalso me at 1:42 am: researching whether penguins have knees",
    "just answered a work email with 'happy to help!' while staring at the wall trying to remember what my job is",
    "opened my calendar to plan my week and immediately needed a nap",
    "my toxic trait is putting 3 things i already finished on my to-do list just to cross them off",
    "love when someone asks 'any fun plans this weekend?' like i'm not about to stare at two different screens in sweatpants",
    "every adult conversation is just two people taking turns saying 'yeah, it's been a crazy week'",
    "me: i'm going to save money this month\n\nalso me: $7 iced coffee because i sent one awkward email",
    "why does 5 extra minutes in bed somehow make me 45 minutes late",
]

QUOTE_POOL = [
    "i am one minor inconvenience away from becoming a person who bakes sourdough in the woods",
    "adulting is just saying 'next week will be calmer' until you retire",
    "my brain has 47 tabs open and 3 of them are playing music i can't find",
    "not a single person asked me if i can run fast in my new shoes today",
    "i don't need a 5-year plan i just need to make it to 5 pm",
    "my sleep schedule is currently a suggestion",
]

IMESSAGE_POOL = [
    [("are u on your way?", False), ("yes!! literally walking out the door", True), ("(i am still in a towel on my bed)", True)],
    [("did u actually sleep last night?", False), ("i laid down with my eyes closed for 6 hours and worried about 2014", True)],
    [("want to hang out tonight?", False), ("i would love to but my couch already booked me", True)],
    [("how's work going today?", False), ("just typed 'per my last email' and now my heart rate is 140", True)],
]

CONTRAST_POOL = [
    ("Me: I will cook healthy meals all week.", "Also me: Eating shredded cheese over the sink at 11 pm."),
    ("Me: Setting 1 alarm for 7:00 am.", "Also me: 7:00, 7:05, 7:10, 7:15, 7:22."),
    ("Me: I need some fresh air.", "My brain: Where? Rome, Florence, or Milan?"),
    ("Me: Quick 10-minute break.", "Also me: 2 hours deep into watching someone pressure-wash a driveway."),
]

CAPTIONS = [
    "thriving, allegedly.",
    "no thoughts just 47 open tabs",
    "posting proof that none of us have it figured out",
    "another week, another iced coffee",
    "please do not perceive me before noon",
]

def main():
    now = datetime.now(timezone.utc)
    batch = now.strftime("batch_%Y%m%d_%H%M")
    out_dir = os.path.join("docs", "images", batch)
    os.makedirs(out_dir, exist_ok=True)

    ledger_path = "used_jokes.json"
    used = []
    if os.path.exists(ledger_path):
        used = json.load(open(ledger_path, "r", encoding="utf-8"))

    def pick_fresh(pool):
        avail = [x for x in pool if json.dumps(x) not in used]
        if not avail:
            avail = pool
        choice = random.choice(avail)
        used.append(json.dumps(choice))
        return choice

    slides = []
    # Mix 10 varied slides
    for idx in range(1, 11):
        fname = f"slide_{idx:02d}.jpg"
        fpath = os.path.join(out_dir, fname)
        if idx in (1, 5, 8):
            render_a1_tweet(pick_fresh(TWEET_POOL), fpath, dark=(idx == 8 and random.random() > 0.3))
        elif idx in (2, 6, 10):
            render_gradient_card(pick_fresh(QUOTE_POOL), fpath)
        elif idx in (3, 9):
            render_imessage(pick_fresh(IMESSAGE_POOL), fpath)
        else:
            top, bot = pick_fresh(CONTRAST_POOL)
            render_contrast(top, bot, fpath)
        slides.append(f"{PAGES_BASE}/{batch}/{fname}")

    manifest = {
        "batch": batch,
        "caption": random.choice(CAPTIONS),
        "slides": slides,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(used[-100:], f, indent=2)

    print("Generated batch:", batch)

if __name__ == "__main__":
    main()
