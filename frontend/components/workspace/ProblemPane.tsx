"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QuestionDetail } from "@/types/problem";
import { FileText, CheckCircle2 } from "lucide-react";

interface ProblemPaneProps {
  problem: QuestionDetail;
}

export function ProblemPane({ problem }: ProblemPaneProps) {
  const [activeTab, setActiveTab] = useState<"description" | "cases">("description");

  const difficultyColor =
    problem.difficulty.toLowerCase() === "easy"
      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
      : problem.difficulty.toLowerCase() === "medium"
      ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
      : "text-rose-400 bg-rose-500/10 border-rose-500/20";

  return (
    <div className="flex flex-col h-full bg-[#0d1117] overflow-hidden select-text">
      {/* Pane Tab Navigation */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 px-3 h-10 bg-[#161b22]/70 shrink-0">
        <div className="flex items-center gap-1" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "description"}
            onClick={() => setActiveTab("description")}
            className={`flex items-center gap-1.5 py-2 px-2.5 text-xs font-medium border-b-2 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 ${
              activeTab === "description"
                ? "border-zinc-200 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <FileText className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Description</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "cases"}
            onClick={() => setActiveTab("cases")}
            className={`flex items-center gap-1.5 py-2 px-2.5 text-xs font-medium border-b-2 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 ${
              activeTab === "cases"
                ? "border-zinc-200 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Test Cases</span>
            <span className="text-[10px] text-zinc-500 font-mono tabular-nums">
              ({problem.test_cases?.length || 0})
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono text-zinc-400">
          <span className={`px-2 py-0.5 rounded border text-[10px] font-medium capitalize ${difficultyColor}`}>
            {problem.difficulty}
          </span>
          <span className="tabular-nums text-zinc-400">{problem.time_limit_sec}s</span>
          <span className="text-zinc-600">/</span>
          <span className="tabular-nums text-zinc-400">{problem.memory_limit_mb}MB</span>
        </div>
      </div>

      {/* Pane Content Body */}
      <div className="flex-1 overflow-y-auto p-4 text-xs leading-relaxed text-zinc-300">
        {activeTab === "description" ? (
          <div className="space-y-3">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="text-base font-semibold text-white tracking-tight pb-2 border-b border-zinc-800/80 mb-3">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mt-4 mb-2">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xs font-semibold text-zinc-200 mt-3 mb-1.5">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="text-xs text-zinc-300 leading-relaxed mb-3">
                    {children}
                  </p>
                ),
                code: ({ children, className }) => {
                  const isBlock = className?.includes("language-");
                  if (isBlock) {
                    return <code className="font-mono text-xs text-zinc-200">{children}</code>;
                  }
                  return (
                    <code className="bg-zinc-800/80 text-zinc-200 font-mono px-1 py-0.5 rounded text-[11px] border border-zinc-700/40">
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="bg-[#0f1117] border border-zinc-800/90 rounded-md p-3 my-2.5 font-mono text-[11px] text-zinc-200 overflow-x-auto leading-relaxed">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc pl-4 space-y-1 my-2 text-xs text-zinc-300">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal pl-4 space-y-1 my-2 text-xs text-zinc-300">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-xs leading-relaxed text-zinc-300">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-zinc-100">{children}</strong>
                ),
              }}
            >
              {problem.description}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-[11px] text-zinc-400 pb-1.5 border-b border-zinc-800/80">
              {problem.test_cases.length} public test cases visible. Additional hidden test cases evaluate upon submission.
            </div>

            {problem.test_cases.map((tc, idx) => (
              <div key={tc.id || idx} className="border border-zinc-800/80 rounded bg-[#161b22]/50 p-3 space-y-2">
                <div className="text-[11px] font-mono font-medium text-zinc-400 flex items-center justify-between">
                  <span>Case {idx + 1}</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase tracking-wider block mb-1">Input</span>
                    <pre className="p-2 rounded bg-[#0d1117] border border-zinc-800 text-zinc-200 overflow-x-auto whitespace-pre-wrap">
                      {tc.stdin}
                    </pre>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase tracking-wider block mb-1">Expected Output</span>
                    <pre className="p-2 rounded bg-[#0d1117] border border-zinc-800 text-emerald-400 overflow-x-auto">
                      {tc.expected_stdout}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
