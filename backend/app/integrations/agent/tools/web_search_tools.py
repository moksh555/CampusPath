"""Construct web tools only when executing a research job."""


def build_web_tools():
    from langchain_tavily import TavilyExtract, TavilySearch

    return [
        TavilySearch(search_depth="basic", include_usage=True, safe_search=True),
        TavilyExtract(extract_depth="basic", include_image=False),
    ]
