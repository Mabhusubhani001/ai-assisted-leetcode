import { SignIn } from "@clerk/nextjs";
import { Suspense } from "react";

export default function SignInPage() {
  return (
    <div className="flex-1 flex items-center justify-center py-12 px-4">
      <Suspense fallback={<div className="text-zinc-500 text-sm">Loading sign-in...</div>}>
        <SignIn
          appearance={{
            elements: {
              rootBox: "mx-auto",
              card: "bg-zinc-900 border border-zinc-800 shadow-xl",
              headerTitle: "text-white font-bold",
              headerSubtitle: "text-zinc-400",
              socialButtonsBlockButton: "bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700",
              formFieldLabel: "text-zinc-300",
              formFieldInput: "bg-zinc-950 border-zinc-800 text-white",
              formButtonPrimary: "bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold",
              footerActionLink: "text-emerald-400 hover:text-emerald-300",
            },
          }}
        />
      </Suspense>
    </div>
  );
}
