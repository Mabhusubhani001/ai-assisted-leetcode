import Link from "next/link";
import { Sparkles, ArrowRight, ShieldCheck, Cpu, Code2 } from "lucide-react";

const PROBLEMS = [
  {
    title: "Two Sum",
    slug: "two-sum",
    difficulty: "Easy",
    difficultyColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description: "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
    category: "Hash Table / Array",
  },
  {
    title: "Valid Parentheses",
    slug: "valid-parentheses",
    difficulty: "Easy",
    difficultyColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description: "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
    category: "Stack / String",
  },
  {
    title: "Reverse Linked List",
    slug: "reverse-linked-list",
    difficulty: "Easy",
    difficultyColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description: "Given the head of a singly linked list, reverse the list, and return the reversed list.",
    category: "Pointers / Linked List",
  },
];

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12 flex-1 flex flex-col">
      {/* Hero Section */}
      <div className="text-center max-w-2xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Strict 2,000-Token Algorithmic Guardrails</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
          Explain First. <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
            Code Later.
          </span>
        </h1>
        <p className="text-zinc-400 text-base leading-relaxed">
          The code editor stays locked until you explain your data structure, pattern, and complexity to the AI Coach. No brute-force guessing. No boilerplate copy-pasting.
        </p>
      </div>

      {/* Feature Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-14">
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40">
          <ShieldCheck className="w-5 h-5 text-emerald-400 mb-2" />
          <h3 className="font-semibold text-white text-sm mb-1">Approach Verification</h3>
          <p className="text-xs text-zinc-400">Explain your time and space complexity to unlock starter code.</p>
        </div>
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40">
          <Cpu className="w-5 h-5 text-cyan-400 mb-2" />
          <h3 className="font-semibold text-white text-sm mb-1">Atomic 2,000 Tokens</h3>
          <p className="text-xs text-zinc-400">Strict Redis-backed token budget per question prevents prompt abuse.</p>
        </div>
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40">
          <Code2 className="w-5 h-5 text-indigo-400 mb-2" />
          <h3 className="font-semibold text-white text-sm mb-1">Sandboxed Evaluation</h3>
          <p className="text-xs text-zinc-400">10 comprehensive test cases (3 visible, 7 confidential edge cases).</p>
        </div>
      </div>

      {/* Problem Catalog */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center justify-between">
          <span>Practice Problem Catalog</span>
          <span className="text-xs font-normal text-zinc-400">{PROBLEMS.length} Problems Ready</span>
        </h2>

        <div className="space-y-3">
          {PROBLEMS.map((problem) => (
            <Link
              key={problem.slug}
              href={`/problems/${problem.slug}`}
              className="group block p-5 rounded-xl border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700 transition-all shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-1.5">
                    <h3 className="font-semibold text-white text-base group-hover:text-emerald-400 transition-colors">
                      {problem.title}
                    </h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${problem.difficultyColor}`}>
                      {problem.difficulty}
                    </span>
                    <span className="text-xs text-zinc-400">
                      {problem.category}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-400 line-clamp-2">
                    {problem.description}
                  </p>
                </div>

                <div className="flex items-center gap-1 text-sm font-medium text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <span>Solve</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
