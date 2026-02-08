from flask import Flask, render_template, abort, request
from utils.context import ContextManager
from utils.blog_engine import get_blog_engine
from utils.knowledge_base_manager import get_kb_manager
from utils.projects_engine import get_projects_engine

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
    "chess_bg": "images/chess_bg.jpg",
}

FILES = {
    "resume": "resume_MuhsinKompas.pdf",
}

# Initialize context manager, blog engine, knowledge base, and projects
PCTX = ContextManager("./data/personal_info.json")
blog = get_blog_engine()
kb = get_kb_manager()
projects = get_projects_engine()


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
# Projects Routes
# =============================================================================

@app.route("/projects")
def projects_list():
    """Display list of all projects."""
    # Get optional tag filter
    tag_filter = request.args.get("tag")
    
    if tag_filter:
        project_items = projects.get_projects_by_tag(tag_filter)
        page_title = f"Projects tagged '{tag_filter}'"
    else:
        project_items = projects.get_all_projects()
        page_title = "Projects"
    
    # Get all tags for sidebar/filter
    all_tags = projects.get_all_tags()
    
    # Convert projects to dict for template
    projects_data = [proj.to_dict() for proj in project_items]
    
    return render_template(
        "projects_list.html",
        projects=projects_data,
        all_tags=all_tags,
        current_tag=tag_filter,
        page_title=page_title,
    )


@app.route("/projects/<slug>")
def project_detail(slug):
    """Display a single project."""
    project = projects.get_project_by_slug(slug)
    
    if not project:
        abort(404)
    
    # Don't show drafts in production
    if project.is_draft and not app.debug:
        abort(404)
    
    return render_template(
        "project_detail.html",
        project=project.to_dict(),
    )


@app.route("/projects/tag/<tag>")
def projects_by_tag(tag):
    """Display projects filtered by tag."""
    project_items = projects.get_projects_by_tag(tag)
    
    if not project_items:
        abort(404)
    
    all_tags = projects.get_all_tags()
    projects_data = [proj.to_dict() for proj in project_items]
    
    return render_template(
        "projects_list.html",
        projects=projects_data,
        all_tags=all_tags,
        current_tag=tag,
        page_title=f"Projects tagged '{tag}'",
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
    
    # Get terminals from knowledge base
    terminals = kb.get_terminals()
    terminals_data = [term.to_dict() for term in terminals]
    
    # Get featured projects for projects section
    featured_projects = projects.get_featured_projects(limit=3)
    featured_projects_data = [proj.to_dict() for proj in featured_projects]
    
    print("hobbies:")
    print(PCTX.hobbies)
    return render_template(
        "index.html",
        images=IMAGES,
        files=FILES,
        about_me=PCTX.about,
        timeline=PCTX.timeline,
        personal_info=PCTX.personal,
        contact=PCTX.contact,
        recent_posts=recent_posts_data,
        hobbies=PCTX.hobbies,
        terminals=terminals_data,
        featured_projects=featured_projects_data,
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