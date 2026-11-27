"use client";

import React from "react";
import { SignInButton, SignUpButton, Show, UserButton } from "@clerk/nextjs";

export function HeaderAuth() {
  return (
    <div className="flex items-center gap-3">
      <Show when="signed-out">
        <SignInButton mode="modal">
          <button
            type="button"
            className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none rounded"
          >
            Sign In
          </button>
        </SignInButton>
        <SignUpButton mode="modal">
          <button
            type="button"
            className="px-3 py-1 text-xs font-medium bg-zinc-100 text-zinc-950 hover:bg-white transition-colors rounded shadow-sm focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
          >
            Register
          </button>
        </SignUpButton>
      </Show>

      <Show when="signed-in">
        <UserButton
          appearance={{
            elements: {
              avatarBox: "w-7 h-7 rounded-full border border-zinc-800",
            },
          }}
        />
      </Show>
    </div>
  );
}
