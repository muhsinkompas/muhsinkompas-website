"""
Projects Engine - Portfolio Project Manager
============================================
Handles both GitHub repositories and local Markdown project descriptions.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


# Configuration
PROJECTS_DIR = Path("./projects")
DEFAULT_AUTHOR = "Muhsin Kompas"
DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Project:
    """Represents a single project (GitHub repo or local markdown)."""
    slug: str
    title: str
    description: str
    content_html: str
    content_raw: str
    tags: List[str] = field(default_factory=list)
    date: Optional[datetime] = None
    project_type: str = "local"  # "github" or "local"
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    featured_image: Optional[str] = None
    featured: bool = False
    technologies: List[str] = field(default_factory=list)
    stars: int = 0
    forks: int = 0
    is_draft: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def date_formatted(self) -> str:
        """Return formatted date string."""
        if self.date:
            return self.date.strftime("%B %d, %Y")
        return ""

    @property
    def date_iso(self) -> str:
        """Return ISO formatted date string."""
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for template rendering."""
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "content": self.content_html,
            "content_raw": self.content_raw,
            "tags": self.tags,
            "date": self.date,
            "date_formatted": self.date_formatted,
            "date_iso": self.date_iso,
            "project_type": self.project_type,
            "github_url": self.github_url,
            "demo_url": self.demo_url,
            "featured_image": self.featured_image,
            "featured": self.featured,
            "technologies": self.technologies,
            "stars": self.stars,
            "forks": self.forks,
            "is_draft": self.is_draft,
            "meta": self.meta,
        }


class ProjectsEngine:
    """
    Projects Portfolio Engine.
    
    Scans a directory for Markdown project files and provides methods
    to retrieve projects with caching.
    """

    def __init__(self, projects_dir: str | Path = PROJECTS_DIR):
        self.projects_dir = Path(projects_dir)
        self._cache_timestamp: Optional[float] = None
        
        # Configure Markdown parser with extensions
        self.md = markdown.Markdown(
            extensions=[
                FencedCodeExtension(),
                CodeHiliteExtension(
                    css_class="highlight",
                    linenums=False,
                    guess_lang=True,
                ),
                TableExtension(),
                "nl2br",
                "smarty",
                "attr_list",
            ],
            output_format="html5",
        )

    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate excerpt from content."""
        clean_text = re.sub(r"<[^>]+>", "", content)
        clean_text = " ".join(clean_text.split())
        
        if len(clean_text) <= max_length:
            return clean_text
        
        truncated = clean_text[:max_length].rsplit(" ", 1)[0]
        return truncated + "..."

    def _extract_slug_from_filename(self, filename: str) -> str:
        """Extract slug from filename."""
        name = filename.rsplit(".", 1)[0]
        return name

    def _parse_project(self, filepath: Path) -> Optional[Project]:
        """Parse a single Markdown file into a Project object."""
        try:
            # Load frontmatter and content
            proj = frontmatter.load(filepath)
            
            # Skip drafts in production
            is_draft = proj.get("draft", False)
            
            # Extract metadata
            title = proj.get("title", "Untitled Project")
            description = proj.get("description", "")
            
            # Parse date if available
            date_str = proj.get("date")
            date = None
            if date_str:
                if isinstance(date_str, datetime):
                    date = date_str
                else:
                    try:
                        date = datetime.strptime(str(date_str), DATE_FORMAT)
                    except:
                        date = None
            
            # Get slug
            slug = proj.get("slug") or self._extract_slug_from_filename(filepath.name)
            
            # Parse tags and technologies
            tags = proj.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            
            technologies = proj.get("technologies", [])
            if isinstance(technologies, str):
                technologies = [t.strip() for t in technologies.split(",")]
            
            # Reset markdown parser state
            self.md.reset()
            
            # Render content
            content_html = self.md.convert(proj.content)
            
            # Project type
            project_type = proj.get("type", "local")
            
            return Project(
                slug=slug,
                title=title,
                description=description or self._generate_excerpt(content_html),
                content_html=content_html,
                content_raw=proj.content,
                tags=tags,
                date=date,
                project_type=project_type,
                github_url=proj.get("github_url"),
                demo_url=proj.get("demo_url"),
                featured_image=proj.get("featured_image") or proj.get("image"),
                featured=proj.get("featured", False),
                technologies=technologies,
                stars=proj.get("stars", 0),
                forks=proj.get("forks", 0),
                is_draft=is_draft,
                meta=dict(proj.metadata),
            )
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None

    def _get_projects_dir_mtime(self) -> float:
        """Get the latest modification time of the projects directory."""
        if not self.projects_dir.exists():
            return 0.0
        
        latest_mtime = self.projects_dir.stat().st_mtime
        
        for filepath in self.projects_dir.glob("*.md"):
            mtime = filepath.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
        
        return latest_mtime

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed based on file changes."""
        current_mtime = self._get_projects_dir_mtime()
        
        if self._cache_timestamp is None:
            return True
        
        return current_mtime > self._cache_timestamp

    @lru_cache(maxsize=1)
    def _load_all_projects_cached(self, cache_key: float) -> List[Project]:
        """
        Load all projects with LRU cache.
        
        The cache_key parameter is used to invalidate the cache
        when files are modified.
        """
        projects = []
        
        if not self.projects_dir.exists():
            print(f"Warning: Projects directory '{self.projects_dir}' does not exist.")
            return projects
        
        for filepath in self.projects_dir.glob("*.md"):
            project = self._parse_project(filepath)
            if project:
                projects.append(project)
        
        # Sort by date (newest first) if dates exist, then by title
        projects.sort(key=lambda p: (p.date or datetime.min, p.title), reverse=True)
        
        return projects

    def get_all_projects(self, include_drafts: bool = False) -> List[Project]:
        """
        Get all projects, sorted by date (newest first).
        
        Args:
            include_drafts: Whether to include draft projects.
        
        Returns:
            List of Project objects.
        """
        if self._should_refresh_cache():
            self._load_all_projects_cached.cache_clear()
            self._cache_timestamp = self._get_projects_dir_mtime()
        
        projects = self._load_all_projects_cached(self._cache_timestamp or 0)
        
        if not include_drafts:
            projects = [p for p in projects if not p.is_draft]
        
        return projects

    def get_project_by_slug(self, slug: str) -> Optional[Project]:
        """
        Get a single project by its slug.
        
        Args:
            slug: The project slug.
        
        Returns:
            Project object or None if not found.
        """
        projects = self.get_all_projects(include_drafts=True)
        
        for project in projects:
            if project.slug == slug:
                return project
        
        return None

    def get_featured_projects(self, limit: int = 3) -> List[Project]:
        """
        Get featured projects for homepage.
        
        Args:
            limit: Maximum number of projects to return.
        
        Returns:
            List of featured Project objects.
        """
        projects = self.get_all_projects()
        featured = [p for p in projects if p.featured]
        
        # If not enough featured, add recent projects
        if len(featured) < limit:
            non_featured = [p for p in projects if not p.featured]
            featured.extend(non_featured[:limit - len(featured)])
        
        return featured[:limit]

    def get_projects_by_tag(self, tag: str) -> List[Project]:
        """
        Get all projects with a specific tag.
        
        Args:
            tag: The tag to filter by.
        
        Returns:
            List of Project objects.
        """
        projects = self.get_all_projects()
        return [p for p in projects if tag.lower() in [t.lower() for t in p.tags]]

    def get_all_tags(self) -> Dict[str, int]:
        """
        Get all tags with their project counts.
        
        Returns:
            Dictionary mapping tags to project counts.
        """
        tags: Dict[str, int] = {}
        
        for project in self.get_all_projects():
            for tag in project.tags:
                tag_lower = tag.lower()
                tags[tag_lower] = tags.get(tag_lower, 0) + 1
        
        return dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))

    def clear_cache(self) -> None:
        """Clear the projects cache."""
        self._load_all_projects_cached.cache_clear()
        self._cache_timestamp = None


# Global projects engine instance
projects_engine = ProjectsEngine()


def get_projects_engine() -> ProjectsEngine:
    """Get the global projects engine instance."""
    return projects_engine
