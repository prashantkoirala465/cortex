"use client";

import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

type NoteEditorProps = {
  content: JSONContent;
  onChange: (content: JSONContent) => void;
};

export function NoteEditor({ content, onChange }: NoteEditorProps) {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    immediatelyRender: false,
    onUpdate: ({ editor }) => onChange(editor.getJSON()),
    editorProps: {
      attributes: {
        class: "note-prose min-h-[60vh] outline-none",
      },
    },
  });

  // keep the editor in sync when a different note's content loads in
  useEffect(() => {
    if (!editor) return;
    const current = JSON.stringify(editor.getJSON());
    const next = JSON.stringify(content);
    if (current !== next) editor.commands.setContent(content);
  }, [editor, content]);

  return <EditorContent editor={editor} />;
}
