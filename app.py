from flask import Flask, render_template, abort, request
from utils.context import ContextManager
from utils.blog_engine import get_blog_engine

app = Flask(__name__, template_folder="templates")

# =============================================================================
# Configuration
# =============================================================================

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

# Initialize context manager and blog engine
PCTX = ContextManager("./data/personal_info.json")
blog = get_blog_engine()


# =============================================================================
# Blog Routes
# =============================================================================

@app.route("/blog")
def blog_list():
    """Display list of all blog posts."""
    # Get optional tag filter
    tag_filter = request.args.get("tag")
    
    if tag_filter:
        posts = blog.get_posts_by_tag(tag_filter)
        page_title = f"Posts tagged '{tag_filter}'"
    else:
        posts = blog.get_all_posts()
        page_title = "Blog"
    
    # Get all tags for sidebar/filter
    all_tags = blog.get_all_tags()
    
    # Convert posts to dict for template
    posts_data = [post.to_dict() for post in posts]
    
    return render_template(
        "blog_list.html",
        posts=posts_data,
        all_tags=all_tags,
        current_tag=tag_filter,
        page_title=page_title,
    )


@app.route("/blog/<slug>")
def blog_detail(slug):
    """Display a single blog post."""
    post = blog.get_post_by_slug(slug)
    
    if not post:
        abort(404)
    
    # Don't show drafts in production
    if post.is_draft and not app.debug:
        abort(404)
    
    # Get related posts
    related_posts = blog.get_related_posts(post, limit=3)
    related_posts_data = [p.to_dict() for p in related_posts]
    
    return render_template(
        "blog_detail.html",
        post=post.to_dict(),
        related_posts=related_posts_data,
    )


@app.route("/blog/tag/<tag>")
def blog_by_tag(tag):
    """Display posts filtered by tag."""
    posts = blog.get_posts_by_tag(tag)
    
    if not posts:
        abort(404)
    
    all_tags = blog.get_all_tags()
    posts_data = [post.to_dict() for post in posts]
    
    return render_template(
        "blog_list.html",
        posts=posts_data,
        all_tags=all_tags,
        current_tag=tag,
        page_title=f"Posts tagged '{tag}'",
    )


# =============================================================================
# CV Route
# =============================================================================

@app.route("/cv")
def cv():
    """Display CV page with embedded PDF."""
    return render_template("cv.html", files=FILES, contact=PCTX.contact)


# =============================================================================
# Main Routes
# =============================================================================

@app.route("/")
def index():
    """Display the homepage."""
    # Get recent blog posts for the wiki section
    recent_posts = blog.get_recent_posts(limit=3)
    recent_posts_data = [post.to_dict() for post in recent_posts]
    
    return render_template(
        "index.html",
        images=IMAGES,
        files=FILES,
        about_me=PCTX.about,
        timeline=PCTX.timeline,
        personal_info=PCTX.personal,
        contact=PCTX.contact,
        recent_posts=recent_posts_data,
    )


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("404.html"), 404


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)