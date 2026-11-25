"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import {
  Lock,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  Code2,
  Trophy,
  AlertCircle,
  X,
  Loader2,
} from "lucide-react";
import { SubmissionResponse } from "@/types/problem";

// Dynamically import Monaco Editor on client side only to isolate from Node.js SSR
const MonacoWorkspaceEditor = dynamic(
  () => import("./MonacoWorkspaceEditor"),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 w-full h-full flex flex-col items-center justify-center gap-2.5 text-zinc-500 font-mono text-xs bg-[#0d1117]">
        <Code2 className="w-5 h-5 animate-pulse text-zinc-400" />
        <span>Initializing Monaco Engine…</span>
      </div>
    ),
  }
);

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
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!isUnlocked || isSubmitting) return;

    setIsSubmitting(true);
    setSubmissionResult(null);
    setSubmissionError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/v1/submissions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev_user_student42",
        },
        body: JSON.stringify({
          question_id: questionId,
          language_id: language === "cpp" ? 54 : language === "java" ? 62 : language === "javascript" ? 63 : 71,
          source_code: code,
        }),
      });

      if (!res.ok) {
        throw new Error(`Submission server returned HTTP ${res.status}`);
      }

      const result: SubmissionResponse = await res.json();
      setSubmissionResult(result);
    } catch (err: any) {
      setSubmissionError(err.message || "Unable to reach submission runner");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col w-full min-h-0 bg-[#0d1117] overflow-hidden relative">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 px-3 h-10 bg-[#161b22]/70 shrink-0 gap-2">
        <div className="flex items-center gap-2.5 min-w-0 shrink-0">
          <label htmlFor="language-select" className="sr-only">Programming Language</label>
          <select
            id="language-select"
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="bg-[#0d1117] border border-zinc-700/80 rounded px-2.5 py-1 text-xs text-zinc-200 font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 shrink-0 cursor-pointer"
          >
            <option value="python">Python 3</option>
            <option value="cpp">C++ (GCC 13)</option>
            <option value="java">Java 17</option>
            <option value="javascript">JavaScript</option>
          </select>

          <span className="text-[10px] font-mono text-zinc-500 hidden sm:inline-flex items-center gap-1.5 shrink-0 whitespace-nowrap">
            {isUnlocked ? (
              <span className="text-emerald-400 font-medium">● Ready to edit</span>
            ) : (
              <span className="text-zinc-500">○ Locked</span>
            )}
          </span>

          {/* Quick Header Status Pill */}
          {submissionResult && (
            <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium border animate-fadeIn">
              {submissionResult.status === "ACCEPTED" ? (
                <span className="text-emerald-400 border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                  ✔ Accepted
                </span>
              ) : (
                <span className="text-rose-400 border-rose-500/30 bg-rose-500/10 px-1.5 py-0.5 rounded">
                  ✕ {submissionResult.status.replace(/_/g, " ")}
                </span>
              )}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!isUnlocked || isSubmitting}
            className="flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium bg-white hover:bg-zinc-200 text-zinc-950 disabled:opacity-30 disabled:hover:bg-white transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 cursor-pointer disabled:cursor-not-allowed whitespace-nowrap shrink-0"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current shrink-0" aria-hidden="true" />
            )}
            <span className="whitespace-nowrap">{isSubmitting ? "Evaluating…" : "Submit Solution"}</span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 w-full min-h-0 relative bg-[#0d1117] overflow-hidden">
        {/* Pinned to all 4 edges of the relative flex container: guaranteed non-zero pixel height */}
        <div className="absolute inset-0">
          <MonacoWorkspaceEditor
            code={code}
            language={language}
            isUnlocked={isUnlocked}
            onCodeChange={onCodeChange}
          />
        </div>

        {/* Floating Lock Badge Overlay (Shows syntax code underneath with clean floating modal) */}
        {!isUnlocked && (
          <div className="absolute inset-0 bg-[#0d1117]/60 backdrop-blur-[1px] flex flex-col items-center justify-center p-6 text-center z-20 select-none pointer-events-auto">
            <div className="p-5 rounded-xl bg-zinc-900/95 border border-zinc-700/80 shadow-2xl flex flex-col items-center max-w-sm">
              <div className="w-10 h-10 rounded-full bg-zinc-800 border border-zinc-600/80 flex items-center justify-center text-amber-400 mb-2.5 shadow-inner">
                <Lock className="w-5 h-5" aria-hidden="true" />
              </div>
              <h2 className="text-white font-semibold text-sm mb-1.5">Code Editor Locked</h2>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Explain your algorithmic strategy in the AI Coach pane on the right. Once verified, click <strong className="text-emerald-400">Push to Code Editor & Unlock</strong> to begin coding.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Submission Error Banner */}
      {submissionError && (
        <div className="border-t border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>Submission error: {submissionError}. Verify FastAPI backend is running.</span>
          </div>
          <button
            type="button"
            onClick={() => setSubmissionError(null)}
            className="p-1 text-rose-400 hover:text-white rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* High-Visibility LeetCode-Grade Submission Result Drawer */}
      {submissionResult && (
        <div className="border-t border-zinc-700/80 bg-[#12161f] p-4 text-xs shrink-0 select-text max-h-[50%] overflow-y-auto shadow-2xl z-20">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
            {/* Status Title Banner */}
            <div className="flex items-center gap-2">
              {submissionResult.status === "ACCEPTED" ? (
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm font-mono">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  <span>ACCEPTED</span>
                </div>
              ) : submissionResult.status === "WRONG_ANSWER" ? (
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm font-mono">
                  <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
                  <span>WRONG ANSWER</span>
                </div>
              ) : submissionResult.status === "TIME_LIMIT_EXCEEDED" ? (
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm font-mono">
                  <Clock className="w-5 h-5 text-amber-400 shrink-0" />
                  <span>TIME LIMIT EXCEEDED</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm font-mono">
                  <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                  <span>{submissionResult.status.replace(/_/g, " ")}</span>
                </div>
              )}
            </div>

            {/* Metrics Pills & Close Button */}
            <div className="flex items-center gap-2 sm:gap-3 text-[11px] font-mono text-zinc-300">
              <span className="flex items-center gap-1 bg-zinc-800/80 px-2 py-0.5 rounded border border-zinc-700/60">
                <Clock className="w-3 h-3 text-zinc-400" />
                <span className="tabular-nums">{(submissionResult.execution_time_sec ?? 0).toFixed(3)}s</span>
              </span>
              <span className="flex items-center gap-1 bg-zinc-800/80 px-2 py-0.5 rounded border border-zinc-700/60">
                <Cpu className="w-3 h-3 text-zinc-400" />
                <span className="tabular-nums">{((submissionResult.memory_used_kb ?? 0) / 1024).toFixed(1)} MB</span>
              </span>
              <span className="px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300 border border-zinc-700/60 font-semibold">
                {submissionResult.passed_test_cases} / {submissionResult.total_test_cases} passed
              </span>
              <button
                type="button"
                onClick={() => setSubmissionResult(null)}
                aria-label="Close results panel"
                className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors ml-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Celebratory Banner for Accepted */}
          {submissionResult.status === "ACCEPTED" && (
            <div className="mt-3 p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-800/50 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-emerald-900/60 border border-emerald-700/60 flex items-center justify-center shrink-0">
                <Trophy className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-emerald-300 text-xs">All {submissionResult.total_test_cases} Test Cases Passed!</h3>
                <p className="text-[11px] text-emerald-400/80 mt-0.5 leading-relaxed">
                  Excellent work! Your algorithmic solution satisfies all public and hidden evaluation constraints.
                </p>
              </div>
            </div>
          )}

          {/* Detailed Test Case Failure Inspector for Wrong Answer */}
          {submissionResult.status === "WRONG_ANSWER" && submissionResult.failed_test_case_info && (
            <div className="mt-3 space-y-2">
              <div className="text-[11px] font-mono font-medium text-rose-300">
                Failed on Test Case #{submissionResult.failed_test_case_info.test_case_number}:
              </div>
              {submissionResult.failed_test_case_info.is_hidden ? (
                <div className="p-3 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-xs leading-relaxed">
                  {submissionResult.failed_test_case_info.message || "Failed on a hidden edge case. Consider negative numbers, empty inputs, or duplicate values."}
                </div>
              ) : (
                <div className="space-y-2 font-mono text-[11px]">
                  <div>
                    <span className="text-[10px] uppercase text-zinc-500 tracking-wider block mb-0.5">Input</span>
                    <pre className="p-2 rounded bg-zinc-900 border border-zinc-800 text-zinc-200 overflow-x-auto whitespace-pre-wrap">
                      {submissionResult.failed_test_case_info.stdin}
                    </pre>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div>
                      <span className="text-[10px] uppercase text-zinc-500 tracking-wider block mb-0.5">Your Output</span>
                      <pre className="p-2 rounded bg-rose-950/30 border border-rose-900/60 text-rose-300 overflow-x-auto whitespace-pre-wrap">
                        {submissionResult.failed_test_case_info.actual_stdout || "null"}
                      </pre>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-zinc-500 tracking-wider block mb-0.5">Expected Output</span>
                      <pre className="p-2 rounded bg-emerald-950/30 border border-emerald-900/60 text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                        {submissionResult.failed_test_case_info.expected_stdout}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Runtime Error Stderr */}
          {submissionResult.stderr && (
            <div className="mt-3">
              <span className="text-[10px] uppercase text-rose-400 tracking-wider font-mono block mb-1">Standard Error Output</span>
              <pre className="p-2.5 rounded bg-rose-950/40 border border-rose-900/70 text-rose-300 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {submissionResult.stderr}
              </pre>
            </div>
          )}

          {/* Compiler Output */}
          {submissionResult.compile_output && (
            <div className="mt-3">
              <span className="text-[10px] uppercase text-amber-400 tracking-wider font-mono block mb-1">Compiler Output</span>
              <pre className="p-2.5 rounded bg-amber-950/40 border border-amber-900/70 text-amber-300 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {submissionResult.compile_output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
