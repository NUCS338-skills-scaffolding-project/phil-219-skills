type Props = { text: string };

/**
 * Tiny inline-markdown renderer that handles **bold** and *italic* without
 * pulling in a real markdown library. Newlines are preserved via CSS
 * (`white-space: pre-wrap`).
 */
export function Markdown({ text }: Props) {
  const nodes = renderInline(text);
  return <span className="content">{nodes}</span>;
}

function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let lastIdx = 0;
  let key = 0;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.slice(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(<em key={key++}>{token.slice(1, -1)}</em>);
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code key={key++} style={{ background: "#f3f4f6", padding: "0 4px", borderRadius: 4 }}>
          {token.slice(1, -1)}
        </code>
      );
    }
    lastIdx = match.index + token.length;
  }
  if (lastIdx < text.length) parts.push(text.slice(lastIdx));
  return parts;
}
