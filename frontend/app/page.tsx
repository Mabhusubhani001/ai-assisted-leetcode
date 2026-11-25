import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

interface ProblemRow {
  title: string;
  slug: string;
  difficulty: "Easy" | "Medium" | "Hard";
  category: string;
  acceptance: string;
}

const PROBLEMS: ProblemRow[] = [
  {
    title: "Two Sum",
    slug: "two-sum",
    difficulty: "Easy",
    category: "Hash Table / Array",
    acceptance: "49.2%",
  },
  {
    title: "Valid Parentheses",
    slug: "valid-parentheses",
    difficulty: "Easy",
    category: "Stack / String",
    acceptance: "40.8%",
  },
  {
    title: "Reverse Linked List",
    slug: "reverse-linked-list",
    difficulty: "Easy",
    category: "Pointers / Linked List",
    acceptance: "74.1%",
  },
];

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-10 w-full flex-1 flex flex-col">
      {/* Header Section */}
      <div className="mb-8">
        <h1 className="text-xl font-bold tracking-tight text-white mb-1.5 text-balance">
          Assessment Problem Catalog
        </h1>
        <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
          The code editor remains locked until you explain your algorithmic approach, data structure, and complexity to the AI coach. Each problem includes a strict 2,000-token guardrail and isolated test evaluation.
        </p>
      </div>

      {/* Clean Problems Directory Table */}
      <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-950">
        <div className="grid grid-cols-12 px-4 py-2.5 bg-zinc-900/50 border-b border-zinc-800 text-[11px] font-medium text-zinc-400">
          <span className="col-span-1">Status</span>
          <span className="col-span-6">Title</span>
          <span className="col-span-2">Category</span>
          <span className="col-span-2">Difficulty</span>
          <span className="col-span-1 text-right">Acceptance</span>
        </div>

        <div className="divide-y divide-zinc-800/80 text-xs">
          {PROBLEMS.map((problem, idx) => (
            <Link
              key={problem.slug}
              href={`/problems/${problem.slug}`}
              className="grid grid-cols-12 px-4 py-3 items-center hover:bg-zinc-900/60 transition-colors group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
            >
              <div className="col-span-1 text-zinc-600 group-hover:text-zinc-400 transition-colors">
                <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="col-span-6 font-medium text-zinc-200 group-hover:text-white flex items-center gap-2">
                <span>{idx + 1}.</span>
                <span>{problem.title}</span>
              </div>
              <div className="col-span-2 text-zinc-400 text-[11px]">
                {problem.category}
              </div>
              <div className="col-span-2">
                <span className="inline-block text-[11px] px-2 py-0.5 rounded font-mono font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20">
                  {problem.difficulty}
                </span>
              </div>
              <div className="col-span-1 text-right text-zinc-500 font-mono text-[11px] tabular-nums">
                {problem.acceptance}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
