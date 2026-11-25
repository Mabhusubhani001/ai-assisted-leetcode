"use client";

import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import { Lock, Play, Send, CheckCircle2, XCircle, AlertCircle, Clock, Cpu } from "lucide-react";
import { SubmissionResponse } from "@/types/problem";

interface EditorPaneProps {
  questionId: string;
  isUnlocked: boolean;
  code: string;
  language: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (lang: string) => void;
}

export function EditorPane({
  questionId,
  isUnlocked,
  code,
  language,
  onCodeChange,
  onLanguageChange,
}: EditorPaneProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<SubmissionResponse | null>(null);
  const [resultTab, setResultTab] = useState<"results" | "console">("results");

  const handleSubmit = async () => {
    if (!isUnlocked || isSubmitting) return;

    setIsSubmitting(true);
    setSubmissionResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/submissions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev_user_student42",
        },
        body: JSON.stringify({
          question_id: questionId,
          language_id: 71, // 71 = Python 3
          source_code: code,
        }),
      });

      if (!res.ok) {
        throw new Error(`Submission failed with status ${res.status}`);
      }

      const result: SubmissionResponse = await res.json();
      setSubmissionResult(result);
    } catch (err: any) {
      alert(`Submission Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden relative">
      {/* Editor Top Bar */}
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-2.5 bg-zinc-900">
        <div className="flex items-center gap-3">
          <select
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            disabled={!isUnlocked}
            className="bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1 text-xs text-zinc-300 font-mono focus:outline-none focus:border-zinc-700"
          >
            <option value="python">Python 3 (3.12)</option>
            <option value="cpp">C++ (GCC 13)</option>
            <option value="java">Java (OpenJDK 17)</option>
            <option value="javascript">JavaScript (Node 20)</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSubmit}
            disabled={!isUnlocked || isSubmitting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-zinc-950 disabled:opacity-40 disabled:hover:bg-emerald-500 transition-colors shadow-sm"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isSubmitting ? "Running..." : "Submit Solution"}</span>
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 relative overflow-hidden">
        <Editor
          height="100%"
          language={language === "cpp" ? "cpp" : language}
          theme="vs-dark"
          value={code}
          onChange={(val) => onCodeChange(val || "")}
          options={{
            readOnly: !isUnlocked,
            fontSize: 13,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 12 },
            fontFamily: "'Fira Code', 'JetBrains Mono', Consolas, monospace",
          }}
        />

        {/* Locked Overlay */}
        {!isUnlocked && (
          <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center z-10">
            <div className="p-3 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 mb-3">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-white font-bold text-sm mb-1">
              Code Editor Locked
            </h3>
            <p className="text-zinc-400 text-xs max-w-sm mb-4 leading-relaxed">
              Explain your algorithmic approach, data structure, and complexity in the AI Coach panel on the right to receive starter code and unlock the editor.
            </p>
          </div>
        )}
      </div>

      {/* Execution Results Drawer */}
      {submissionResult && (
        <div className="border-t border-zinc-800 bg-zinc-950 p-4 max-h-48 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {submissionResult.status === "ACCEPTED" ? (
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Accepted</span>
                </div>
              ) : submissionResult.status === "TIME_LIMIT_EXCEEDED" ? (
                <div className="flex items-center gap-1.5 text-amber-400 font-bold text-sm">
                  <Clock className="w-4 h-4" />
                  <span>Time Limit Exceeded (TLE)</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-rose-400 font-bold text-sm">
                  <XCircle className="w-4 h-4" />
                  <span>{submissionResult.status}</span>
                </div>
              )}

              <span className="text-xs text-zinc-400 font-mono">
                ({submissionResult.passed_test_cases}/{submissionResult.total_test_cases} Test Cases Passed)
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs text-zinc-400 font-mono">
              {typeof submissionResult.execution_time_sec === "number" && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {submissionResult.execution_time_sec}s
                </span>
              )}
              {typeof submissionResult.memory_used_kb === "number" && (
                <span className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  {Math.round(submissionResult.memory_used_kb / 1024)}MB
                </span>
              )}
            </div>
          </div>

          {/* Stderr or Compile Error message */}
          {submissionResult.stderr && (
            <pre className="p-2 rounded bg-rose-950/30 border border-rose-900/50 text-rose-300 text-xs font-mono overflow-x-auto">
              {submissionResult.stderr}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
