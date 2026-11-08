import { Construction } from "lucide-react";

import { cn } from "@/lib/utils";

/** Shown when the backend answers HTTP 501 (route scaffolded, logic not written yet). */
export function ComingSoon({ feature, className }: { feature: string; className?: string }) {
  return (
    <div
      className={cn(
        "text-muted-foreground flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center text-sm",
        className,
      )}
    >
      <Construction className="size-6" />
      <p className="text-foreground font-medium">Chưa implement</p>
      <p>
        <code className="bg-muted rounded px-1 py-0.5 text-xs">{feature}</code> trả về HTTP 501
        (scaffold).
      </p>
    </div>
  );
}
