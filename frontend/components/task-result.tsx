import React, { useState } from "react";
import { Copy, Check, ChevronDown, ChevronUp } from "lucide-react";

interface TaskResultProps {
  content: string;
  status?: "completed" | "failed" | "running" | "pending";
}

export function TaskResult({ content, status = "completed" }: TaskResultProps) {
  return (
    <div
      className={`rounded-b-lg border-t overflow-hidden text-sm leading-relaxed ${
        status === "completed"
          ? "border-success/20 bg-success/5"
          : status === "failed"
          ? "border-danger/20 bg-danger/5"
          : "border-border bg-bg-elevated"
      }`}
    >
      <div className="p-4 max-h-[600px] overflow-y-auto">{renderMarkdown(content)}</div>
    </div>
  );
}

function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code blocks (```)
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <CodeBlock key={elements.length} lang={lang} code={codeLines.join("\n")} />
      );
      continue;
    }

    // Horizontal rules (---, ===)
    if (/^={3,}$/.test(line.trim()) || /^-{3,}$/.test(line.trim())) {
      elements.push(
        <hr key={elements.length} className="my-4 border-border" />
      );
      i++;
      continue;
    }

    // Headings (###, ####)
    const headingMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      elements.push(
        <Heading key={elements.length} level={level} text={text} />
      );
      i++;
      continue;
    }

    // Checkboxes (- [ ] or - [x])
    const checkboxMatch = line.match(/^(\s*)-\s+\[([ x])\]\s+(.*)/);
    if (checkboxMatch) {
      const checked = checkboxMatch[2] === "x";
      const indent = checkboxMatch[1].length;
      elements.push(
        <div
          key={elements.length}
          className="flex gap-2 my-1"
          style={{ marginLeft: `${Math.min(indent, 4) * 8 + 4}px` }}
        >
          <div
            className={`w-4 h-4 mt-0.5 rounded border flex-shrink-0 flex items-center justify-center ${
              checked
                ? "bg-accent border-accent text-white"
                : "border-border bg-surface"
            }`}
          >
            {checked && <Check className="w-3 h-3" />}
          </div>
          <span className="text-text-secondary">{renderInline(checkboxMatch[3])}</span>
        </div>
      );
      i++;
      continue;
    }

    // Bold key-value lines (**text**: value)
    const boldLineMatch = line.match(/^\*\*(.+?)\*\*:\s*(.*)/);
    if (boldLineMatch) {
      elements.push(
        <div key={elements.length} className="flex gap-2 my-1">
          <span className="font-semibold text-text">{boldLineMatch[1]}:</span>
          <span className="text-text-secondary">{renderInline(boldLineMatch[2])}</span>
        </div>
      );
      i++;
      continue;
    }

    // Numbered lists (1. **text**:)
    const numberedMatch = line.match(/^(\d+)\.\s+\*\*(.+?)\*\*:?\s*(.*)/);
    if (numberedMatch) {
      elements.push(
        <div key={elements.length} className="flex gap-2 my-1.5 ml-1">
          <span className="font-mono text-xs text-accent mt-0.5 w-5 text-right flex-shrink-0">
            {numberedMatch[1]}.
          </span>
          <div>
            <span className="font-semibold text-text">{numberedMatch[2]}</span>
            {numberedMatch[3] && (
              <span className="text-text-secondary">: {renderInline(numberedMatch[3])}</span>
            )}
          </div>
        </div>
      );
      i++;
      continue;
    }

    // Bullet lists (- text)
    const bulletMatch = line.match(/^(\s*)[-*]\s+(.*)/);
    if (bulletMatch) {
      const indent = bulletMatch[1].length;
      elements.push(
        <div key={elements.length} className="flex gap-2 my-0.5" style={{ marginLeft: `${Math.min(indent, 4) * 8 + 4}px` }}>
          <span className="text-accent mt-1.5 w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />
          <span className="text-text-secondary">{renderInline(bulletMatch[2])}</span>
        </div>
      );
      i++;
      continue;
    }

    // Empty lines
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Regular text
    elements.push(
      <p key={elements.length} className="text-text-secondary my-1">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return elements;
}

function Heading({ level, text }: { level: number; text: string }) {
  const sizeClass =
    level === 1
      ? "text-xl font-bold"
      : level === 2
      ? "text-lg font-semibold"
      : level === 3
      ? "text-base font-semibold"
      : "text-sm font-medium";

  const accentColors: Record<number, string> = {
    1: "bg-accent",
    2: "bg-blue-500",
    3: "bg-purple-500",
    4: "bg-muted",
  };

  return (
    <div className={`mt-4 mb-2 ${sizeClass} text-text flex items-center gap-2`}>
      <div className={`w-1 h-5 rounded-full ${accentColors[level] || "bg-accent"}`} />
      {renderInline(text)}
    </div>
  );
}

function CodeBlock({ lang, code }: { lang: string; code: string }) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const lines = code.split("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const langLabels: Record<string, string> = {
    javascript: "JavaScript",
    typescript: "TypeScript",
    python: "Python",
    bash: "Bash",
    shell: "Shell",
    html: "HTML",
    css: "CSS",
    json: "JSON",
    yaml: "YAML",
    markdown: "Markdown",
    sql: "SQL",
    dockerfile: "Dockerfile",
    go: "Go",
    rust: "Rust",
    java: "Java",
    ruby: "Ruby",
  };

  const langColors: Record<string, string> = {
    javascript: "text-yellow-400",
    typescript: "text-blue-400",
    python: "text-green-400",
    bash: "text-green-300",
    shell: "text-green-300",
    html: "text-orange-400",
    css: "text-blue-300",
    json: "text-yellow-300",
    yaml: "text-purple-400",
    sql: "text-cyan-400",
    dockerfile: "text-blue-400",
  };

  return (
    <div className="my-3 rounded-lg border border-border overflow-hidden">
      <div className="px-3 py-1.5 bg-bg-elevated border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          {lang && (
            <span className={`text-xs font-mono font-medium ${langColors[lang] || "text-text-muted"}`}>
              {langLabels[lang] || lang}
            </span>
          )}
          <span className="text-xs text-text-muted">{lines.length} lines</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text transition-colors"
            title={collapsed ? "Expand" : "Collapse"}
          >
            {collapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text transition-colors"
            title="Copy code"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>
      {!collapsed && (
        <pre className="p-3 bg-[#0d1117] overflow-x-auto">
          <code className="text-xs font-mono text-gray-300 leading-relaxed">
            {lines.map((line, idx) => (
              <div key={idx} className="flex">
                <span className="inline-block w-8 text-right pr-3 text-gray-500 select-none flex-shrink-0">
                  {idx + 1}
                </span>
                <span className="flex-1">{highlightSyntax(line, lang)}</span>
              </div>
            ))}
          </code>
        </pre>
      )}
    </div>
  );
}

function highlightSyntax(line: string, lang: string): React.ReactNode {
  if (!lang || ["markdown", "yaml", "json"].includes(lang)) {
    return <span>{line}</span>;
  }

  // Simple syntax highlighting patterns
  const keywords: Record<string, RegExp> = {
    javascript: /\b(const|let|var|function|return|if|else|for|while|class|import|from|export|default|async|await|new|this|try|catch|throw|typeof|instanceof)\b/g,
    typescript: /\b(const|let|var|function|return|if|else|for|while|class|import|from|export|default|async|await|new|this|try|catch|throw|typeof|instanceof|interface|type|enum|namespace)\b/g,
    python: /\b(def|class|import|from|return|if|elif|else|for|while|try|except|finally|raise|with|as|lambda|yield|True|False|None|self|async|await)\b/g,
    bash: /\b(if|then|else|fi|for|do|done|while|case|esac|function|return|exit|echo|export|source)\b/g,
    go: /\b(func|package|import|return|if|else|for|range|var|const|type|struct|interface|map|chan|go|defer|select|case|switch|default)\b/g,
  };

  const keywordRegex = keywords[lang] || keywords.javascript;
  const parts = line.split(/(\/{2}[^]*|"[^"]*"|'[^']*'|`[^`]*`)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("//") || part.startsWith("#")) {
          return <span key={i} className="text-gray-500 italic">{part}</span>;
        }
        if (part.startsWith('"') || part.startsWith("'") || part.startsWith("`")) {
          return <span key={i} className="text-green-400">{part}</span>;
        }
        // Highlight keywords
        const highlighted = part.replace(keywordRegex, (match) => `<<KW>>${match}<</KW>>`);
        if (highlighted.includes("<<KW>>")) {
          const segments = highlighted.split(/(<<KW>>[^<]*<<?\/KW>>)/g);
          return (
            <span key={i}>
              {segments.map((seg, j) => {
                if (seg.startsWith("<<KW>>")) {
                  const kw = seg.replace(/<<KW>>|<\/?KW>>/g, "");
                  return <span key={j} className="text-purple-400 font-medium">{kw}</span>;
                }
                return <span key={j}>{seg}</span>;
              })}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 rounded bg-surface-hover text-accent text-xs font-mono"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-text">
          {part.slice(2, -2)}
        </strong>
      );
    }
    // Highlight keywords
    if (/\b(SECURITY|CRITICAL|ERROR|HIGH|WARNING|WARN|MEDIUM|INFO|TODO|FIXME)\b/.test(part)) {
      return <span key={i} className="font-mono text-xs font-medium text-warning">{part}</span>;
    }
    return <span key={i}>{part}</span>;
  });
}
