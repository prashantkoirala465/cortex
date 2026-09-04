"""Turns a Tiptap/ProseMirror JSON document into plain text for the LLM
pipeline, and splits that text into chunks for embedding."""

# node types whose full text content is captured as a single line; their
# children are never walked into separately, which is what prevents e.g. a
# listItem's paragraph from being emitted twice
LEAF_TEXT_TYPES = {"paragraph", "heading", "codeBlock"}


def _collect_text(node: dict) -> str:
    if node.get("type") == "text":
        return node.get("text", "")
    return "".join(_collect_text(child) for child in node.get("content", []))


def render_plain_text(content: dict) -> str:
    lines: list[str] = []

    def walk(node: dict) -> None:
        if node.get("type") in LEAF_TEXT_TYPES:
            text = _collect_text(node).strip()
            if text:
                lines.append(text)
            return
        for child in node.get("content", []):
            walk(child)

    walk(content)
    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n{para}" if current else para
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current:
        chunks.append(current)

    # a single paragraph longer than max_chars still needs splitting
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final.append(chunk)
        else:
            for i in range(0, len(chunk), max_chars):
                final.append(chunk[i : i + max_chars])
    return final
