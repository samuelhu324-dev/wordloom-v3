export function cn(...args: (string | undefined | false)[]) {
  return args.filter(Boolean).join(" ");
}

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:18080";
