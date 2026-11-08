import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { ComingSoon } from "@/components/coming-soon";
import { ApiError } from "@/lib/api";

/** Loading / error / 501 handling shared by every data view. */
export function QueryState<T>({
  query,
  feature,
  children,
}: {
  query: UseQueryResult<T>;
  feature: string;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) {
    return (
      <div className="text-muted-foreground flex items-center gap-2 p-6 text-sm">
        <Loader2 className="size-4 animate-spin" /> Đang tải…
      </div>
    );
  }
  if (query.isError) {
    const err = query.error;
    if (err instanceof ApiError && err.notImplemented) return <ComingSoon feature={feature} />;
    return (
      <div className="text-destructive rounded-lg border border-destructive/30 p-6 text-sm">
        Lỗi tải dữ liệu: {err instanceof Error ? err.message : String(err)}
      </div>
    );
  }
  return <>{children(query.data)}</>;
}
