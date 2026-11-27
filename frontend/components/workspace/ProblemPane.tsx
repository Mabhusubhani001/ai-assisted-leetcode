"use client";

import React, { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QuestionDetail, SubmissionResponse } from "@/types/problem";
import {
  FileText,
  CheckCircle2,
  History,
  XCircle,
  Clock,
  Cpu,
  AlertTriangle,
  RotateCcw,
  Loader2,
  ChevronDown,
  ChevronUp,
  Code2,
  Check,
} from "lucide-react";

interface ProblemPaneProps {
  problem: QuestionDetail;
  submissionTrigger?: number;
  onRestoreCode?: (code: string) => void;
}

export function ProblemPane({
  problem,
  submissionTrigger = 0,
  onRestoreCode,
}: ProblemPaneProps) {
  const [activeTab, setActiveTab] = useState<"description" | "cases" | "submissions">("description");
  const [submissions, setSubmissions] = useState<SubmissionResponse[]>([]);
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [expandedSubmissionId, setExpandedSubmissionId] = useState<string | null>(null);
  const [restoredId, setRestoredId] = useState<string | null>(null);

  const difficultyColor =
    problem.difficulty.toLowerCase() === "easy"
      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
      : problem.difficulty.toLowerCase() === "medium"
      ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
      : "text-rose-400 bg-rose-500/10 border-rose-500/20";

  const fetchSubmissions = useCallback(async () => {
    setIsLoadingSubmissions(true);
    setSubmissionError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/v1/submissions/history/${problem.id}`, {
        headers: {
          Authorization: "Bearer dev_user_student42",
        },
      });
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      const data: SubmissionResponse[] = await res.json();
      setSubmissions(data);
    } catch (err: any) {
      setSubmissionError(err.message || "Failed to load submission history");
    } finally {
      setIsLoadingSubmissions(false);
    }
  }, [problem.id]);

  useEffect(() => {
    if (activeTab === "submissions" || submissionTrigger > 0) {
      fetchSubmissions();
    }
  }, [activeTab, submissionTrigger, fetchSubmissions]);

  const handleRestore = (submission: SubmissionResponse) => {
    if (onRestoreCode && submission.source_code) {
      onRestoreCode(submission.source_code);
      setRestoredId(submission.id);
      setTimeout(() => setRestoredId(null), 2500);
    }
  };

  const getLanguageName = (id: number): string => {
    switch (id) {
      case 71:
        return "Python 3";
      case 54:
        return "C++ (GCC 13)";
      case 62:
        return "Java 17";
      case 63:
        return "JavaScript";
      default:
        return "Code";
    }
  };

  const formatRelativeTime = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
      if (diffSeconds < 60) return "Just now";
      const diffMinutes = Math.floor(diffSeconds / 60);
      if (diffMinutes < 60) return `${diffMinutes}m ago`;
      const diffHours = Math.floor(diffMinutes / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return dateString;
    }
  };

  const acceptedCount = submissions.filter((s) => s.status === "ACCEPTED").length;

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
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "submissions"}
            onClick={() => setActiveTab("submissions")}
            className={`flex items-center gap-1.5 py-2 px-2.5 text-xs font-medium border-b-2 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 ${
              activeTab === "submissions"
                ? "border-zinc-200 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <History className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Submissions</span>
            {submissions.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-400 font-mono tabular-nums">
                {submissions.length}
              </span>
            )}
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
        ) : activeTab === "cases" ? (
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
        ) : (
          /* Submissions History Tab */
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[11px] text-zinc-400 pb-2 border-b border-zinc-800/80">
              <span>Past Evaluation Attempts</span>
              <div className="flex items-center gap-2">
                {submissions.length > 0 && (
                  <span className="text-[10px] font-mono text-zinc-400">
                    <span className="text-emerald-400 font-medium">{acceptedCount}</span> / {submissions.length} Accepted
                  </span>
                )}
                <button
                  type="button"
                  onClick={fetchSubmissions}
                  disabled={isLoadingSubmissions}
                  className="hover:text-zinc-200 disabled:opacity-40 transition-colors cursor-pointer"
                  title="Refresh history"
                >
                  <RotateCcw className={`w-3 h-3 ${isLoadingSubmissions ? "animate-spin text-zinc-400" : ""}`} />
                </button>
              </div>
            </div>

            {isLoadingSubmissions && submissions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2.5 text-zinc-500 font-mono text-xs">
                <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                <span>Loading submission history…</span>
              </div>
            ) : submissionError && submissions.length === 0 ? (
              <div className="p-3 rounded-lg border border-rose-900/40 bg-rose-950/20 text-rose-300 text-xs flex flex-col gap-2">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>Unable to retrieve submissions</span>
                </div>
                <p className="text-[11px] text-rose-400/80">{submissionError}</p>
                <button
                  type="button"
                  onClick={fetchSubmissions}
                  className="self-start px-2 py-1 rounded bg-rose-900/40 hover:bg-rose-900/60 text-white text-[10px] font-medium transition-colors"
                >
                  Try Again
                </button>
              </div>
            ) : submissions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2 text-zinc-500 text-center">
                <History className="w-8 h-8 text-zinc-600 stroke-[1.5]" />
                <p className="text-xs font-medium text-zinc-400">No submissions recorded yet</p>
                <p className="text-[11px] text-zinc-500 max-w-xs leading-relaxed">
                  Write your solution in the middle editor and click <strong className="text-zinc-300 font-medium">Submit Solution</strong> to test against both public and hidden test cases.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {submissions.map((sub, idx) => {
                  const isAccepted = sub.status === "ACCEPTED";
                  const isTLE = sub.status === "TIME_LIMIT_EXCEEDED";
                  const isExpanded = expandedSubmissionId === sub.id;

                  const statusBadgeClass = isAccepted
                    ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                    : isTLE
                    ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
                    : "text-rose-400 bg-rose-500/10 border-rose-500/30";

                  const StatusIcon = isAccepted
                    ? CheckCircle2
                    : isTLE
                    ? Clock
                    : XCircle;

                  return (
                    <div
                      key={sub.id || idx}
                      className="border border-zinc-800/80 rounded-lg bg-[#161b22]/40 overflow-hidden transition-colors hover:border-zinc-700/80"
                    >
                      {/* Summary Row */}
                      <div
                        onClick={() => setExpandedSubmissionId(isExpanded ? null : sub.id)}
                        className="p-3 flex items-center justify-between cursor-pointer select-none hover:bg-zinc-800/20 transition-colors gap-2"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <StatusIcon
                            className={`w-4 h-4 shrink-0 ${
                              isAccepted ? "text-emerald-400" : isTLE ? "text-amber-400" : "text-rose-400"
                            }`}
                          />
                          <div className="flex flex-col min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`text-[10px] font-mono font-medium px-1.5 py-0.5 rounded border uppercase tracking-wider ${statusBadgeClass}`}>
                                {sub.status.replace(/_/g, " ")}
                              </span>
                              <span className="text-[11px] font-mono text-zinc-400">
                                {getLanguageName(sub.language_id)}
                              </span>
                            </div>
                            <span className="text-[10px] text-zinc-500 mt-0.5 font-mono">
                              {formatRelativeTime(sub.created_at)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          {/* Metrics Pill */}
                          <div className="text-right font-mono text-[10px] text-zinc-400 hidden sm:flex flex-col items-end">
                            <span className="tabular-nums">
                              {sub.execution_time_sec !== null && sub.execution_time_sec !== undefined
                                ? `${sub.execution_time_sec.toFixed(3)}s`
                                : "—"}
                            </span>
                            <span className="text-zinc-500 tabular-nums">
                              {sub.passed_test_cases}/{sub.total_test_cases} passed
                            </span>
                          </div>

                          <div className="text-zinc-500">
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Expanded Submission Details & Code Preview */}
                      {isExpanded && (
                        <div className="border-t border-zinc-800/70 bg-[#0d1117] p-3 space-y-2.5">
                          {/* Detailed Metrics Strip */}
                          <div className="grid grid-cols-3 gap-2 p-2 rounded bg-zinc-900/80 border border-zinc-800 text-[10px] font-mono text-zinc-300">
                            <div>
                              <span className="text-zinc-500 block">Runtime</span>
                              <span className="text-zinc-200 font-medium">
                                {sub.execution_time_sec !== null && sub.execution_time_sec !== undefined
                                  ? `${(sub.execution_time_sec * 1000).toFixed(0)} ms`
                                  : "N/A"}
                              </span>
                            </div>
                            <div>
                              <span className="text-zinc-500 block">Memory</span>
                              <span className="text-zinc-200 font-medium">
                                {sub.memory_used_kb
                                  ? `${(sub.memory_used_kb / 1024).toFixed(1)} MB`
                                  : "N/A"}
                              </span>
                            </div>
                            <div>
                              <span className="text-zinc-500 block">Test Cases</span>
                              <span
                                className={`font-medium ${
                                  sub.passed_test_cases === sub.total_test_cases
                                    ? "text-emerald-400"
                                    : "text-rose-400"
                                }`}
                              >
                                {sub.passed_test_cases} / {sub.total_test_cases}
                              </span>
                            </div>
                          </div>

                          {/* Action Toolbar */}
                          <div className="flex items-center justify-between pt-1">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 flex items-center gap-1">
                              <Code2 className="w-3 h-3 text-zinc-400" />
                              Submitted Source Code
                            </span>
                            {onRestoreCode && (
                              <button
                                type="button"
                                onClick={() => handleRestore(sub)}
                                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 hover:text-white text-[11px] font-mono transition-colors shadow-sm cursor-pointer"
                              >
                                {restoredId === sub.id ? (
                                  <>
                                    <Check className="w-3 h-3 text-emerald-400" />
                                    <span className="text-emerald-400 font-medium">Restored!</span>
                                  </>
                                ) : (
                                  <>
                                    <RotateCcw className="w-3 h-3 text-zinc-400" />
                                    <span>Restore to Editor</span>
                                  </>
                                )}
                              </button>
                            )}
                          </div>

                          {/* Code Snippet Box */}
                          <pre className="p-2.5 rounded bg-[#161b22]/90 border border-zinc-800 font-mono text-[11px] text-zinc-200 overflow-x-auto leading-relaxed max-h-56 scrollbar-thin scrollbar-thumb-zinc-700">
                            <code>{sub.source_code}</code>
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
