"use client";

import React, { useState } from "react";
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
      `# Explain your approach to the AI Coach to unlock the editor and receive starter code.`
  );
  const [tokensUsed, setTokensUsed] = useState(0);

  const handleUnlock = (starterCode: string) => {
    setIsUnlocked(true);
    if (starterCode) {
      setCode(starterCode);
    } else if (problem.starter_code?.[language]) {
      setCode(problem.starter_code[language]);
    }
  };

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    if (problem.starter_code?.[newLang]) {
      setCode(problem.starter_code[newLang]);
    }
  };

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 p-3 h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Left Column: Problem Statement (4 Cols) */}
      <div className="lg:col-span-4 h-full overflow-hidden">
        <ProblemPane problem={problem} />
      </div>

      {/* Middle Column: Monaco Code Editor (5 Cols) */}
      <div className="lg:col-span-5 h-full overflow-hidden">
        <EditorPane
          questionId={problem.id}
          isUnlocked={isUnlocked}
          code={code}
          language={language}
          onCodeChange={setCode}
          onLanguageChange={handleLanguageChange}
        />
      </div>

      {/* Right Column: AI Coach Chat & Token Meter (3 Cols) */}
      <div className="lg:col-span-3 h-full overflow-hidden">
        <AICoachPane
          questionId={problem.id}
          questionTitle={problem.title}
          isUnlocked={isUnlocked}
          tokensUsed={tokensUsed}
          onUnlock={handleUnlock}
          onTokenUpdate={setTokensUsed}
        />
      </div>
    </div>
  );
}
