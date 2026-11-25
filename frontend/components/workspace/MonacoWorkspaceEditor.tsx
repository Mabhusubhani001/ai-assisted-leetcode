"use client";

import React, { useEffect, useRef, useState } from "react";
import { Code2 } from "lucide-react";

interface MonacoWorkspaceEditorProps {
  code: string;
  language: string;
  isUnlocked: boolean;
  onCodeChange: (code: string) => void;
}

export default function MonacoWorkspaceEditor({
  code,
  language,
  isUnlocked,
  onCodeChange,
}: MonacoWorkspaceEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<any>(null);
  const isUpdatingFromProp = useRef(false);
  const [isReady, setIsReady] = useState(false);

  // Initialize Monaco Editor directly from local AMD distribution
  useEffect(() => {
    let disposed = false;

    function initMonaco() {
      if (disposed || !containerRef.current) return;

      const monaco = (window as any).monaco;
      if (!monaco?.editor) return;

      // Clean up previous instance if any
      if (editorRef.current) {
        editorRef.current.dispose();
      }

      // Create native Monaco instance directly in container
      const editor = monaco.editor.create(containerRef.current, {
        value: code,
        language: language === "cpp" ? "cpp" : language,
        theme: "vs-dark",
        automaticLayout: true,
        fontSize: 13,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        padding: { top: 12 },
        fontFamily: "'Fira Code', 'JetBrains Mono', Consolas, monospace",
        lineNumbers: "on",
        renderLineHighlight: "all",
        tabSize: 4,
        insertSpaces: true,
        readOnly: !isUnlocked,
      });

      editorRef.current = editor;
      setIsReady(true);

      // Relayout on next frame to ensure the bounding rect matches computed flex layout
      requestAnimationFrame(() => {
        if (editorRef.current && containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            editorRef.current.layout({ width: rect.width, height: rect.height });
          }
        }
      });

      // Two-way sync: editor -> React state
      editor.onDidChangeModelContent(() => {
        if (!isUpdatingFromProp.current) {
          onCodeChange(editor.getValue());
        }
      });
    }

    function loadMonacoScript(onSuccess: () => void) {
      if ((window as any).monaco?.editor) {
        onSuccess();
        return;
      }

      const win = window as any;
      if (win.require && win.require.config) {
        win.require.config({ paths: { vs: "/vs" } });
        win.require(["vs/editor/editor.main"], () => {
          if (!disposed) onSuccess();
        });
        return;
      }

      let script = document.getElementById("monaco-amd-loader") as HTMLScriptElement;
      if (!script) {
        script = document.createElement("script");
        script.id = "monaco-amd-loader";
        script.src = "/vs/loader.js";
        script.onload = () => {
          win.require.config({ paths: { vs: "/vs" } });
          win.require(["vs/editor/editor.main"], () => {
            if (!disposed) onSuccess();
          });
        };
        document.body.appendChild(script);
      } else {
        const interval = setInterval(() => {
          if (win.require && win.require.config) {
            clearInterval(interval);
            win.require.config({ paths: { vs: "/vs" } });
            win.require(["vs/editor/editor.main"], () => {
              if (!disposed) onSuccess();
            });
          }
        }, 50);
      }
    }

    loadMonacoScript(initMonaco);

    return () => {
      disposed = true;
      if (editorRef.current) {
        editorRef.current.dispose();
        editorRef.current = null;
      }
    };
  }, []); // Run once on mount

  // Sync external code updates (e.g. from AI Coach push) to Monaco
  useEffect(() => {
    if (editorRef.current) {
      const currentVal = editorRef.current.getValue();
      if (currentVal !== code) {
        isUpdatingFromProp.current = true;
        editorRef.current.setValue(code);
        isUpdatingFromProp.current = false;
      }
    }
  }, [code]);

  // Sync language selection changes to Monaco model
  useEffect(() => {
    if (editorRef.current && (window as any).monaco) {
      const model = editorRef.current.getModel();
      if (model) {
        (window as any).monaco.editor.setModelLanguage(
          model,
          language === "cpp" ? "cpp" : language
        );
      }
    }
  }, [language]);

  // Sync read-only status based on algorithmic verification lock
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({ readOnly: !isUnlocked });
    }
  }, [isUnlocked]);

  // Observe container size changes (split pane drag, window resize) and relayout Monaco
  useEffect(() => {
    if (!containerRef.current) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0 && editorRef.current) {
          editorRef.current.layout({ width, height });
        }
      }
    });

    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [isReady]);

  return (
    <div className="w-full h-full min-h-0 relative bg-[#1e1e1e] overflow-hidden">
      {!isReady && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 text-zinc-500 font-mono text-xs bg-[#0d1117] z-10">
          <Code2 className="w-5 h-5 animate-pulse text-zinc-400" />
          <span>Loading Monaco Editor…</span>
        </div>
      )}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
}
