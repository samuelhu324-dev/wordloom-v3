import { APP, AppToken } from "./tokens";

export function resolveAppPath(token: AppToken, params?: Record<string,string>, query?: Record<string, any>) {
  let path = "/";
  switch (token) {
    case APP.LOOM: path = "/loom"; break;
    case APP.LOOM_CREATION: path = "/loom?tab=creation"; break;
    case APP.LOOM_MANAGEMENT: path = "/loom?tab=management"; break;
    default: path = "/";
  }
  if (query && !path.includes("?")) {
    const usp = new URLSearchParams(Object.entries(query).filter(([,v]) => v!=null && v!==""));
    const qs = usp.toString(); if (qs) path += "?" + qs;
  }
  return path;
}
