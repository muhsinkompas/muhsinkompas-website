from flask import Flask, render_template
from utils.context import ContextManager

app = Flask(__name__, template_folder="templates")

IMAGES = {
    "profile": "images/profile.jpeg",
    "f1_bg": "images/f1_bg.jpg",
    "cooking_bg": "images/cooking_bg.webp",
    "movies_bg": "images/movies_bg.png",
    "steam_panoramic": "images/steam_panoramic.png",
}

FILES = {
    "resume": "resume_MuhsinKompas.pdf",
}

BLOG_POSTS = [
    {
        "slug": "ubuntu-dual-boot-bluetooth",
        "title": "Ubuntu & Windows Dual Boot Bluetooth Fix",
        "date": "2024-01-30",
        "tags": ["Ubuntu", "System"],
        "content": "<p>Bluetooth cihazların MAC adresleri çakıştığı için...</p>" # Burayı sonra detaylandırırız
    },
    {
        "slug": "flask-jinja-tricks",
        "title": "Flask ve Jinja2 ile Template Inheritance",
        "date": "2024-01-29",
        "tags": ["Python", "Flask"],
        "content": "<p>Layout yapısı hayat kurtarır...</p>"
    }
]

PCTX = ContextManager("./data/personal_info.json")

@app.route("/blog")
def blog_list():
    return render_template("blog_list.html", posts=BLOG_POSTS)

@app.route("/blog/<slug>")
def blog_detail(slug):
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    if post:
        return render_template("blog_detail.html", post=post)
    return "Yazı bulunamadı", 404

@app.route("/cv")
def cv():
    return render_template("cv.html", files=FILES, contact=PCTX.contact)

@app.route("/")
def index():
    print("About Me Timeline:")
    for item in PCTX.timeline:
        print(item)
    print("----")
    print("Parsed Timeline:")
    for item in PCTX.timeline:
        print(item)
    print("====")
    print("About Me Section:")
    print(PCTX.about)
    
    return render_template("index.html", images=IMAGES, files=FILES, about_me=PCTX.about, timeline=PCTX.timeline, personal_info=PCTX.personal, contact=PCTX.contact)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)