import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-4 text-center">
      <h2 className="text-4xl font-extrabold text-white mb-2">404</h2>
      <p className="text-zinc-400 text-sm mb-6">Page or problem statement not found.</p>
      <Link
        href="/"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 text-zinc-950 font-semibold text-xs hover:bg-emerald-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Problem Catalog</span>
      </Link>
    </div>
  );
}
