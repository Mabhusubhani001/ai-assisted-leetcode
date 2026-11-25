"use client";

import React, { useState, useRef } from "react";
import { QuestionDetail } from "@/types/problem";
import { ProblemPane } from "./ProblemPane";
import { EditorPane } from "./EditorPane";
import { AICoachPane } from "./AICoachPane";

interface PracticeWorkspaceProps {
  problem: QuestionDetail;
}

export function PracticeWorkspace({ problem }: PracticeWorkspaceProps) {
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(
    problem.starter_code?.[language] ||
      `# Explain your algorithmic approach in the AI Coach pane to generate and load starter code.`
  );
  const [tokensUsed, setTokensUsed] = useState(0);

  // Panel widths in percentage (28% Problem | 44% Code Editor | 28% AI Coach)
  const [leftWidth, setLeftWidth] = useState(28);
  const [rightWidth, setRightWidth] = useState(28);

  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingLeft = useRef(false);
  const isDraggingRight = useRef(false);

  const handlePointerDownLeft = (e: React.PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    isDraggingLeft.current = true;
  };

  const handlePointerDownRight = (e: React.PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    isDraggingRight.current = true;
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();

    if (isDraggingLeft.current) {
      const newPct = ((e.clientX - rect.left) / rect.width) * 100;
      if (newPct >= 18 && newPct <= 50) {
        setLeftWidth(newPct);
      }
    } else if (isDraggingRight.current) {
      const newPct = ((rect.right - e.clientX) / rect.width) * 100;
      if (newPct >= 18 && newPct <= 45) {
        setRightWidth(newPct);
      }
    }
  };

  const handlePointerUp = () => {
    isDraggingLeft.current = false;
    isDraggingRight.current = false;
  };

  const handlePushToEditor = (starterCode: string) => {
    setCode(starterCode);
    setIsUnlocked(true);
  };

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    if (isUnlocked && problem.starter_code?.[newLang]) {
      setCode(problem.starter_code[newLang]);
    }
  };

  return (
    <div
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      className="flex-1 flex h-[calc(100vh-3rem)] overflow-hidden bg-[#090a0f] p-2 select-none"
    >
      {/* Left Pane: Problem Description */}
      <div
        style={{ width: `${leftWidth}%` }}
        className="flex flex-col min-w-[260px] self-stretch min-h-0 rounded-lg overflow-hidden border border-[#232738] bg-[#0d1117] shadow-sm"
      >
        <ProblemPane problem={problem} />
      </div>

      {/* Resize Gutter 1 */}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize problem description and code editor"
        tabIndex={0}
        onPointerDown={handlePointerDownLeft}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") setLeftWidth((w) => Math.max(18, w - 2));
          if (e.key === "ArrowRight") setLeftWidth((w) => Math.min(50, w + 2));
        }}
        className="w-2 hover:w-2.5 bg-transparent hover:bg-zinc-800/80 active:bg-zinc-700 cursor-col-resize transition-all flex items-center justify-center shrink-0 group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
      >
        <div className="w-0.5 h-6 bg-zinc-800 group-hover:bg-zinc-500 rounded-full" />
      </div>

      {/* Middle Pane: Monaco Editor & Submission Runner */}
      <div className="flex-1 flex flex-col min-w-[320px] self-stretch min-h-0 rounded-lg overflow-hidden border border-[#232738] bg-[#0d1117] shadow-sm relative">
        <EditorPane
          questionId={problem.id}
          isUnlocked={isUnlocked}
          code={code}
          language={language}
          onCodeChange={setCode}
          onLanguageChange={handleLanguageChange}
        />
      </div>

      {/* Resize Gutter 2 */}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize code editor and AI coach"
        tabIndex={0}
        onPointerDown={handlePointerDownRight}
        onKeyDown={(e) => {
          if (e.key === "ArrowRight") setRightWidth((w) => Math.max(18, w - 2));
          if (e.key === "ArrowLeft") setRightWidth((w) => Math.min(45, w + 2));
        }}
        className="w-2 hover:w-2.5 bg-transparent hover:bg-zinc-800/80 active:bg-zinc-700 cursor-col-resize transition-all flex items-center justify-center shrink-0 group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
      >
        <div className="w-0.5 h-6 bg-zinc-800 group-hover:bg-zinc-500 rounded-full" />
      </div>

      {/* Right Pane: AI Coach */}
      <div
        style={{ width: `${rightWidth}%` }}
        className="flex flex-col min-w-[280px] self-stretch min-h-0 rounded-lg overflow-hidden border border-[#232738] bg-[#0d1117] shadow-sm"
      >
        <AICoachPane
          questionId={problem.id}
          questionTitle={problem.title}
          language={language}
          isUnlocked={isUnlocked}
          tokensUsed={tokensUsed}
          onPushToEditor={handlePushToEditor}
          onTokenUpdate={setTokensUsed}
        />
      </div>
    </div>
  );
}
