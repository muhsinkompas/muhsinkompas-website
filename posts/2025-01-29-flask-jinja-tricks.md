---
title: "Flask & Jinja2: Template Inheritance Best Practices"
date: 2025-01-29
slug: flask-jinja-tricks
author: Muhsin Kompas
tags:
  - Python
  - Flask
  - Web Development
  - Tutorial
featured_image: images/blog/2025/flask-jinja2-thumbnail.png
excerpt: "Learn how to structure your Flask templates with Jinja2 inheritance for clean, maintainable code."
draft: false
---

# Why Template Inheritance Matters

When building Flask applications, **template inheritance** is your best friend. It helps you:

- Avoid repeating HTML across pages
- Maintain consistent layouts
- Make global changes in one place
- Keep your code DRY (Don't Repeat Yourself)k

## The Base Layout Pattern

Create a `layout.html` that contains your site's skeleton:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}My Site{% endblock %}</title>
    {% block head %}{% endblock %}
</head>
<body>
    <nav>
        {% include "partials/navbar.html" %}
    </nav>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        {% include "partials/footer.html" %}
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

## Using the Layout

Child templates extend the layout and override blocks:

```html
{% extends "layout.html" %}

{% block title %}Blog - My Site{% endblock %}

{% block content %}
    <h1>Welcome to my blog!</h1>
    <p>Latest posts...</p>
{% endblock %}
```

## Advanced Patterns

### 1. Block Super

Need to add to a block rather than replace it?

```html
{% block head %}
    {{ super() }}  {# Keep parent's content #}
    <link rel="stylesheet" href="/css/blog.css">
{% endblock %}
```

### 2. Macros for Components

Create reusable components with macros:

```html
{# macros/cards.html #}
{% macro post_card(post) %}
<article class="card">
    <h2>{{ post.title }}</h2>
    <time>{{ post.date }}</time>
    <p>{{ post.excerpt }}</p>
    <a href="{{ url_for('blog_detail', slug=post.slug) }}">Read more</a>
</article>
{% endmacro %}
```

Use it in templates:

```html
{% from "macros/cards.html" import post_card %}

{% for post in posts %}
    {{ post_card(post) }}
{% endfor %}
```

### 3. Context Processors

Add variables globally to all templates:

```python
@app.context_processor
def utility_processor():
    def format_date(date, fmt='%B %d, %Y'):
        return date.strftime(fmt)
    
    return dict(
        format_date=format_date,
        site_name="Muhsin Kompas",
        current_year=datetime.now().year
    )
```

Now use anywhere:

```html
<footer>
    &copy; {{ current_year }} {{ site_name }}
</footer>
```

## Project Structure

Here's my recommended template structure:

```
templates/
├── layout.html          # Base template
├── index.html           # Homepage
├── blog_list.html       # Blog listing
├── blog_detail.html     # Single post
├── partials/
│   ├── navbar.html
│   ├── footer.html
│   └── sidebar.html
├── macros/
│   ├── cards.html
│   └── forms.html
└── errors/
    ├── 404.html
    └── 500.html
```

## Conclusion

Template inheritance in Jinja2 is powerful. Use it to:

1. Create a solid base layout
2. Extract reusable partials
3. Build component macros
4. Add context processors for global data

Your future self will thank you for the clean, maintainable templates!

---

*Happy templating! 🐍*
