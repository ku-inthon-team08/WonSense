"use client";

import { useEffect } from "react";

import { api } from "@/lib/api";

// The backend runs on Render's free plan, which sleeps after 15 idle minutes and takes 30s–1min to wake.
// Ping it as soon as any page opens so it is awake by the time someone takes a photo or searches.
export function BackendWarmUp() {
  useEffect(() => {
    api("/health").catch(() => {});
  }, []);
  return null;
}
