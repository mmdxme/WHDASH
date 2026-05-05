"""
Standardized pagination utilities for WHDASH.

This module provides consistent pagination across all routes and modules.
Replace inline pagination code with imports from this module.

Usage:
    from utils.pagination import get_pagination_params, build_pagination_response

    page, per_page, offset = get_pagination_params()
    # Use offset in SQL query
    # ...
    # Then build response:
    return build_pagination_response(items, total, page, per_page)
"""

from flask import request
from typing import Tuple, Dict, Any, List


# Default pagination values (can be overridden per-module)
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 50
MAX_PER_PAGE = 100
MIN_PER_PAGE = 1


def get_pagination_params(
    default_page: int = DEFAULT_PAGE,
    default_per_page: int = DEFAULT_PER_PAGE,
    max_per_page: int = MAX_PER_PAGE
) -> Tuple[int, int, int]:
    """
    Extract and validate pagination parameters from request.

    Args:
        default_page: Default page number if not provided
        default_per_page: Default items per page if not provided
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (page, per_page, offset)
        - page: Validated page number (1-indexed, min 1)
        - per_page: Validated items per page (clamped between MIN_PER_PAGE and max_per_page)
        - offset: Calculated SQL offset ((page - 1) * per_page)
    """
    page = request.args.get('page', default_page, type=int)
    per_page = request.args.get('per_page', default_per_page, type=int)

    # Clamp values to valid ranges
    page = max(1, page)
    per_page = max(MIN_PER_PAGE, min(max_per_page, per_page))

    offset = (page - 1) * per_page
    return page, per_page, offset


def build_pagination_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int
) -> Dict[str, Any]:
    """
    Build standardized pagination metadata for JSON responses.

    Args:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number
        per_page: Items per page

    Returns:
        Dict with 'items' and 'pagination' metadata containing:
        - page, per_page, total, total_pages
        - has_next, has_prev, next_page, prev_page
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None,
        }
    }


def build_template_pagination(
    total: int,
    page: int,
    per_page: int,
    **kwargs
) -> Dict[str, Any]:
    """
    Build pagination context for template rendering.

    Args:
        total: Total number of items
        page: Current page number
        per_page: Items per page
        **kwargs: Additional pagination context (search, filters, etc.)

    Returns:
        Dict with pagination data for templates including:
        - page, pages, per_page, total, total_count
        - start, end (row numbers for display)
        - has_prev, has_next, prev_page, next_page
        - page_links (list of page numbers for display)
        - Any additional kwargs preserved
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    start = (page - 1) * per_page + 1 if total > 0 else 0
    end = min(page * per_page, total) if total > 0 else 0

    # Build page links (show up to 10 pages around current)
    page_links = []
    for p in range(max(1, page - 5), min(total_pages + 1, page + 6)):
        page_links.append(p)

    result = {
        'page': page,
        'pages': total_pages,
        'per_page': per_page,
        'total': total,
        'total_count': total,
        'start': start,
        'end': end,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None,
        'page_links': page_links,
    }
    result.update(kwargs)
    return result


def paginate_query_limit(page: int, per_page: int) -> Tuple[int, int]:
    """
    Get LIMIT and OFFSET for SQL queries.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (limit, offset) for SQL
    """
    limit = per_page
    offset = (page - 1) * per_page
    return limit, offset