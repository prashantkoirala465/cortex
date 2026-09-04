from app.text import chunk_text, render_plain_text


def test_render_plain_text_from_empty_doc():
    assert render_plain_text({"type": "doc", "content": []}) == ""


def test_render_plain_text_joins_paragraphs():
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "First paragraph."}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Second paragraph."}]},
        ],
    }
    assert render_plain_text(doc) == "First paragraph.\nSecond paragraph."


def test_render_plain_text_handles_heading_and_lists_without_duplication():
    doc = {
        "type": "doc",
        "content": [
            {"type": "heading", "content": [{"type": "text", "text": "Title"}]},
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "Item one"}]}
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "Item two"}]}
                        ],
                    },
                ],
            },
        ],
    }
    assert render_plain_text(doc) == "Title\nItem one\nItem two"


def test_render_plain_text_skips_empty_paragraphs():
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": []},
            {"type": "paragraph", "content": [{"type": "text", "text": "Real content"}]},
        ],
    }
    assert render_plain_text(doc) == "Real content"


def test_chunk_text_empty_string_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_chunk_text_groups_short_paragraphs_together():
    text = "one\ntwo\nthree"
    chunks = chunk_text(text, max_chars=100)
    assert chunks == ["one\ntwo\nthree"]


def test_chunk_text_splits_when_over_limit():
    text = "a" * 50 + "\n" + "b" * 50
    chunks = chunk_text(text, max_chars=60)
    assert chunks == ["a" * 50, "b" * 50]


def test_chunk_text_splits_a_single_oversized_paragraph():
    text = "x" * 150
    chunks = chunk_text(text, max_chars=60)
    assert chunks == ["x" * 60, "x" * 60, "x" * 30]


def test_chunk_text_reassembles_to_original_content():
    text = "\n".join(f"paragraph {i}" for i in range(20))
    chunks = chunk_text(text, max_chars=40)
    # every paragraph must show up somewhere - chunking must not drop content
    for i in range(20):
        assert any(f"paragraph {i}" in c for c in chunks)
