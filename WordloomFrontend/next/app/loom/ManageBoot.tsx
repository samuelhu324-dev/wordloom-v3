"use client";
import { useEffect } from "react";
import { sources } from "@/modules/loom/services/sources";
import { entries } from "@/modules/loom/services/entries";

/** Tiny bootstrapper that triggers first-load fetches for Loom Management tab. */
export default function ManageBoot() {
  useEffect(() => {
    sources.list().then((data) => {
      console.debug("[loom] sources.list ->", data);
    }).catch((e) => console.error("[loom] sources.list error", e));

    entries.search({ q: "", limit: 10 }).then((data) => {
      console.debug("[loom] entries.search ->", data);
    }).catch((e) => console.error("[loom] entries.search error", e));
  }, []);
  return null;
}
