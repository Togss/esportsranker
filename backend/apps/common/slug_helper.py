from __future__ import annotations
from typing import Optional, Iterable
from django.utils.text import slugify

def _slug(s: Optional[str]) -> str:
    """Slugify but safely handle None/blank."""
    return slugify((s or "").strip()) or ""

def ensure_unique_slug(
    base: str,
    model_cls,
    instance_pk: Optional[int | str] = None,
    max_len: int = 255,
) -> str:
    """
    Ensure slug uniqueness for model_cls.slug by appending -2, -3, ...
    Respects max_len.
    """
    base = (base or "item")[:max_len]
    slug = base
    n = 2
    qs = model_cls.objects.all()
    if instance_pk is not None:
        qs = qs.exclude(pk=instance_pk)

    # Fast path: first try the base
    if not qs.filter(slug=slug).exists():
        return slug

    # Otherwise suffix
    while True:
        suffix = f"-{n}"
        candidate = (base[: max_len - len(suffix)]) + suffix
        if not qs.filter(slug=candidate).exists():
            return candidate
        n += 1

def join_slug_parts(parts: Iterable[str], max_len: int = 255) -> str:
    """
    Join pre-slugified parts with '-'; drop empties; respect max_len.
    """
    cleaned = [p for p in (parts or []) if p]
    s = "-".join(cleaned)
    return s[:max_len] if s else ""

# --------------------------
# App-specific builder(s)
# --------------------------

def build_stage_slug_base(stage) -> str:
    """
    Build a deterministic Stage slug *base* using:
    tournament (slug or name) + stage_type + optional variant + order.
    Uniqueness is NOT enforced here—use ensure_unique_slug afterwards.
    """
    # Tournament base prefers its slug, falls back to its name
    t_base = getattr(stage.tournament, "slug", None) or getattr(stage.tournament, "name", "")
    parts = [
        _slug(t_base),
        _slug(str(stage.stage_type).lower()),
    ]
    # Optional variant
    if getattr(stage, "variant", None):
        parts.append(_slug(stage.variant))
    # Include order to keep bases deterministic even with repeated variants
    parts.append(_slug(f"o{getattr(stage, 'order', '')}"))
    return join_slug_parts(parts)