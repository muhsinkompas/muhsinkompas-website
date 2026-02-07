from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ALLOWED_PRECISIONS = {"year", "month", "day"}
ALLOWED_TIMELINE_TYPES = {"work", "education", "project"}  # istersen genişlet
DOT_PALETTE = ["bg-zinc-100", "bg-zinc-400", "bg-zinc-500", "bg-zinc-600", "bg-zinc-700", "bg-zinc-800"]
IMAGE_PATH = "images/"

class ContextValidationError(Exception):
    def __init__(self, errors: List[str], warnings: Optional[List[str]] = None) -> None:
        self.errors = errors
        self.warnings = warnings or []
        super().__init__("\n".join(errors))


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[str]
    warnings: List[str]


def _is_non_empty_str(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _looks_like_email(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.strip()))


def _looks_like_url(s: str) -> bool:
    try:
        u = urlparse(s.strip())
        return u.scheme in {"http", "https"} and bool(u.netloc)
    except Exception:
        return False


def _check_precision_consistency(d: date, precision: str, path: str, errors: List[str]) -> None:
    if precision not in ALLOWED_PRECISIONS:
        errors.append(f"{path}: precision must be one of {sorted(ALLOWED_PRECISIONS)} (got: {repr(precision)})")
        return
    if precision == "year":
        if not (d.month == 1 and d.day == 1):
            errors.append(f"{path}: precision='year' requires MM-DD = 01-01 (got: {d.isoformat()})")
    elif precision == "month":
        if d.day != 1:
            errors.append(f"{path}: precision='month' requires DD = 01 (got: {d.isoformat()})")


def _format_date(d: date, precision: str) -> str:
    # Basit display format (istersen TR/EN ay isimleri ekleyebiliriz)
    if precision == "year":
        return str(d.year)
    if precision == "month":
        return d.strftime("%b %Y")  # Jan 2022
    return d.strftime("%d %b %Y")  # 23 Apr 2012


def _format_range(item: Dict[str, Any]) -> str:
    sd: date = item["_parsed_start"]
    sp: str = item.get("start_precision", "day")
    start_txt = _format_date(sd, sp)

    if item.get("is_current") is True or item.get("end_date") is None:
        return f"{start_txt} – Present"

    ed: date = item["_parsed_end"]
    ep: str = item.get("end_precision", "day")
    end_txt = _format_date(ed, ep)

    return f"{start_txt} – {end_txt}"


def _timeline_title(item: Dict[str, Any]) -> str:
    if item.get("type") == "work":
        return item.get("role", "") or ""
    if item.get("type") == "education":
        return item.get("degree", "") or ""
    if item.get("type") == "project":
        return item.get("title", "") or ""
    return item.get("title", "")


def _timeline_subtitle(item: Dict[str, Any]) -> str:
    org = item.get("organization", "") or ""
    desc = item.get("description", "") or ""
    if org and desc:
        return f"{org} • {desc}"
    return org or desc


def _parse_iso_date(
    s: Any,
    *,
    path: str = "date",
    errors: Optional[List[str]] = None,
    require_regex: bool = True,
) -> Optional[date]:
    """
    - s: "YYYY-MM-DD" (JSON'dan gelen)
    - errors verilirse: hata mesajı ekler
    - require_regex=True: formatı regex ile kesin kontrol eder
    """
    if not isinstance(s, str) or (require_regex and not DATE_RE.match(s)):
        if errors is not None:
            errors.append(f"{path}: must be 'YYYY-MM-DD' (got: {repr(s)})")
        return None

    try:
        return date.fromisoformat(s)
    except ValueError:
        if errors is not None:
            errors.append(f"{path}: invalid calendar date (got: {repr(s)})")
        return None


def _fmt_month_year(d: date) -> str:
    return f"{MONTHS_EN[d.month - 1]} {d.year}"


def _build_display_range(item: Dict[str, Any], start_dt: date, end_dt: Optional[date]) -> str:
    start_txt = _fmt_month_year(start_dt)

    is_current = item.get("is_current") is True
    if is_current or end_dt is None:
        return f"{start_txt} - Present"

    end_txt = _fmt_month_year(end_dt)
    return f"{start_txt} - {end_txt}"


def _build_display_title(item: Dict[str, Any]) -> str:
    t = item.get("type")
    if t == "work":
        return (item.get("role") or "").strip()
    if t == "education":
        return (item.get("degree") or "").strip()
    if t == "project":
        return (item.get("title") or "").strip()
    # fallback
    return (item.get("title") or item.get("role") or item.get("degree") or "").strip()


def _build_display_subtitle(item: Dict[str, Any]) -> str:
    org = (item.get("organization") or "").strip()
    desc = (item.get("description") or "").strip()

    if org and desc:
        return f"{org} • {desc}"
    return org or desc


def _tailor_timeline_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tailored: List[Dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        it = dict(item)  # shallow copy

        start_dt = _parse_iso_date(it.get("start_date"))
        end_dt = _parse_iso_date(it.get("end_date"))

        # Display alanları (Jinja2’de direkt kullanacaksın)
        if start_dt:
            it["display_range"] = _build_display_range(it, start_dt, end_dt)
        else:
            it["display_range"] = ""  # istersen "Unknown" yazdırabilirsin

        it["display_title"] = _build_display_title(it)
        it["display_subtitle"] = _build_display_subtitle(it)

        # Sort için internal key’ler
        it["_start_dt"] = start_dt or date.min
        it["_is_current"] = 1 if it.get("is_current") is True else 0

        tailored.append(it)

    # current olanlar önce, sonra start_date desc
    tailored.sort(key=lambda x: (x["_is_current"], x["_start_dt"]), reverse=True)

    # ✅ Dot renkleri: en yeni açık, eskidikçe koyu
    for idx, it in enumerate(tailored):
        it["dot_class"] = DOT_PALETTE[idx] if idx < len(DOT_PALETTE) else DOT_PALETTE[-1]
    
    # internal alanları temizle
    for it in tailored:
        it.pop("_start_dt", None)
        it.pop("_is_current", None)

    return tailored



class ContextManager:
    def __init__(self, context_file: str = "./data/context.json") -> None:
        self.context_file = context_file
        self._mtime: Optional[float] = None

        # dışarıya vereceğin alanlar
        self.data: Dict[str, Any] = {}
        self.personal: Dict[str, Any] = {}
        self.about: Dict[str, Any] = {}
        self.contact: Dict[str, Any] = {}
        self.timeline: List[Dict[str, Any]] = []
        self.hobbies: Dict[str, Any] = {}

        # opsiyonel asset shortcut'ları (template isterse)
        self.assets: Dict[str, Any] = {}
        self.images: Dict[str, Any] = {}
        self.files: Dict[str, Any] = {}

        self.reload(force=True)  # ilk load + validate

    # --------- Public helpers ---------

    def reload_if_changed(self) -> None:
        """Dosya değiştiyse yeniden yükle."""
        try:
            mtime = os.path.getmtime(self.context_file)
        except FileNotFoundError:
            raise

        if self._mtime is None or mtime != self._mtime:
            self.reload(force=True)

    def reload(self, force: bool = False) -> None:
        if not force:
            return self.reload_if_changed()

        ctx = self._load_json()

        result = self.validate(ctx)
        if not result.ok:
            raise ContextValidationError(result.errors, result.warnings)

        ctx = self._build_derived(ctx)

        # assign
        self.data = ctx
        self.personal = ctx.get("personal_info", {})
        self.about = ctx.get("about_me", {})
        self.contact = ctx.get("contact", {})
        # self.timeline = self.about.get("timeline", []) if isinstance(self.about.get("timeline"), list) else []
        # self.timeline = _tailor_timeline_items(self.about.get("timeline", []))
        self.timeline = self.about.get("timeline", [])
        self.hobbies = ctx.get("hobbies", {}) if isinstance(ctx.get("hobbies"), dict) else {}

        self.assets = ctx.get("assets", {}) if isinstance(ctx.get("assets"), dict) else {}
        self.images = self.assets.get("images", {}) if isinstance(self.assets.get("images"), dict) else {}
        self.files = self.assets.get("files", {}) if isinstance(self.assets.get("files"), dict) else {}

        self._mtime = os.path.getmtime(self.context_file)

    def template_kwargs(self) -> Dict[str, Any]:
        """
        render_template'e direkt **kwargs olarak basılacak dict.
        Hem "ctx" hem de shortcut alanlar var.
        """
        return {
            "ctx": self.data,
            "personal_info": self.personal,
            "about_me": self.about,
            "timeline": self.timeline,
            "contact": self.contact,
            "hobbies": self.hobbies,
            "assets": self.assets,
            "images": self.images,
            "files": self.files,
        }

    # --------- Load / Validate / Derived ---------

    def _load_json(self) -> Dict[str, Any]:
        with open(self.context_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ContextValidationError([f"root: must be an object (dict), got {type(data).__name__}"])
        return data

    @staticmethod
    def validate(ctx: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # root keys
        for k in ("personal_info", "about_me", "contact"):
            if k not in ctx:
                errors.append(f"root: missing key '{k}'")

        # personal_info
        p = ctx.get("personal_info", {})
        if not isinstance(p, dict):
            errors.append("personal_info: must be object")
        else:
            if not _is_non_empty_str(p.get("name")):
                errors.append("personal_info.name: must be non-empty string")
            email = p.get("email")
            if not _is_non_empty_str(email) or not _looks_like_email(email):
                errors.append("personal_info.email: must be valid email")
            if not isinstance(p.get("title", ""), str):
                errors.append("personal_info.title: must be string")

        # about_me
        a = ctx.get("about_me", {})
        if not isinstance(a, dict):
            errors.append("about_me: must be object")
        else:
            bio = a.get("professional_bio")
            if not isinstance(bio, list) or not all(isinstance(x, str) for x in bio):
                errors.append("about_me.professional_bio: must be list[str]")

            tl = a.get("timeline")
            if not isinstance(tl, list):
                errors.append("about_me.timeline: must be list")
            else:
                for i, item in enumerate(tl):
                    path = f"about_me.timeline[{i}]"
                    if not isinstance(item, dict):
                        errors.append(f"{path}: must be object")
                        continue

                    ttype = item.get("type")
                    if ttype not in ALLOWED_TIMELINE_TYPES:
                        warnings.append(f"{path}.type: expected {sorted(ALLOWED_TIMELINE_TYPES)} (got {repr(ttype)})")

                    sp = item.get("start_precision")
                    if sp not in ALLOWED_PRECISIONS:
                        errors.append(f"{path}.start_precision: must be one of {sorted(ALLOWED_PRECISIONS)}")
                    sd = _parse_iso_date(item.get("start_date"), path=f"{path}.start_date", errors=errors)
                    if sd and isinstance(sp, str):
                        _check_precision_consistency(sd, sp, f"{path}.start_date", errors)

                    is_current = item.get("is_current")
                    if not isinstance(is_current, bool):
                        errors.append(f"{path}.is_current: must be boolean")

                    ed_raw = item.get("end_date", None)
                    if is_current is True:
                        if ed_raw is not None:
                            errors.append(f"{path}.end_date: must be null when is_current=true")
                    else:
                        if ed_raw is not None:
                            ep = item.get("end_precision")
                            if ep not in ALLOWED_PRECISIONS:
                                errors.append(f"{path}.end_precision: must be one of {sorted(ALLOWED_PRECISIONS)} when end_date set")
                            ed = _parse_iso_date(ed_raw, path=f"{path}.end_date", errors=errors)
                            if ed and sd and ed < sd:
                                errors.append(f"{path}: end_date must be >= start_date")
                            if ed and isinstance(ep, str):
                                _check_precision_consistency(ed, ep, f"{path}.end_date", errors)

                    if not isinstance(item.get("organization", ""), str):
                        errors.append(f"{path}.organization: must be string")

                    # work / education alanları
                    if ttype == "work" and "role" not in item:
                        warnings.append(f"{path}.role: missing (expected for work)")
                    if ttype == "education" and "degree" not in item:
                        warnings.append(f"{path}.degree: missing (expected for education)")
                    if ttype == "project" and "title" not in item:
                        warnings.append(f"{path}.title: missing (expected for project)")

                    # thesis link kontrol (opsiyonel)
                    th = item.get("thesis")
                    if th is not None:
                        if not isinstance(th, dict):
                            errors.append(f"{path}.thesis: must be object")
                        else:
                            link = th.get("link")
                            if link is not None and (not isinstance(link, str) or not _looks_like_url(link)):
                                errors.append(f"{path}.thesis.link: must be http(s) url")

        # contact
        c = ctx.get("contact", {})
        if not isinstance(c, dict):
            errors.append("contact: must be object")
        else:
            cemail = c.get("email")
            if not _is_non_empty_str(cemail) or not _looks_like_email(cemail):
                errors.append("contact.email: must be valid email")
            if not isinstance(c.get("location", ""), str):
                errors.append("contact.location: must be string")

            socials = c.get("socials", {})
            if socials is not None:
                if not isinstance(socials, dict):
                    errors.append("contact.socials: must be object")
                else:
                    for k, v in socials.items():
                        if not isinstance(v, str) or not _looks_like_url(v):
                            errors.append(f"contact.socials.{k}: must be http(s) url")

        return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)

    @staticmethod
    def _build_derived(ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Timeline itemlarına:
          - display_range
          - display_title
          - display_subtitle
        ekler ve sıralar.
        
        Hobbies background imagelarına static/{IMAGE_PATH} prefix ekler.
        """
        ctx = dict(ctx)
        about = dict(ctx.get("about_me", {}))
        tl = about.get("timeline", [])
        if not isinstance(tl, list):
            ctx["about_me"] = about
        else:
            about["timeline"] = _tailor_timeline_items(tl)
            ctx["about_me"] = about

        # Add images/ prefix to hobby background paths (url_for adds static/ automatically)
        hobbies = ctx.get("hobbies", {})
        if isinstance(hobbies, dict):
            hobbies = dict(hobbies)
            for hobby_id, hobby_data in hobbies.items():
                if isinstance(hobby_data, dict):
                    hobby_data = dict(hobby_data)
                    if "background" in hobby_data and isinstance(hobby_data["background"], str):
                        bg = hobby_data["background"]
                        # Remove static/ prefix if present, ensure images/ prefix only
                        bg = bg.replace("static/", "")
                        if not bg.startswith(IMAGE_PATH):
                            hobby_data["background"] = f"{IMAGE_PATH}{bg}"
                        else:
                            hobby_data["background"] = bg
                    hobbies[hobby_id] = hobby_data
            ctx["hobbies"] = hobbies
        
        return ctx
