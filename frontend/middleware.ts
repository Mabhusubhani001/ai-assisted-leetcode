import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default function middleware(req: any, evt: any) {
  // If Clerk publishable key is missing or placeholder, allow traffic without crashing Next.js
  if (!publishableKey || !publishableKey.startsWith("pk_") || publishableKey.includes("placeholder")) {
    return NextResponse.next();
  }
  return clerkMiddleware()(req, evt);
}

export const config = {
  matcher: [
    // Skip Next.js internals and all static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
