import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/sidebar";
import { Badge } from "@/components/ui/badge";
import { useNetwork } from "@/hooks/use-network";
import { CHAIN_NAMES } from "@/lib/format";

export function AppShell() {
  const { data: net, isError } = useNetwork();

  return (
    <div className="flex min-h-svh">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-end gap-2 border-b px-6">
          {net ? (
            <>
              <Badge variant="outline">
                {CHAIN_NAMES[net.chain_id] ?? net.network} · {net.chain_id}
              </Badge>
              <Badge variant={net.erc8183_enabled ? "default" : "secondary"}>
                ERC-8183 {net.erc8183_enabled ? "on" : "off (x402)"}
              </Badge>
            </>
          ) : (
            <Badge variant="secondary">{isError ? "API offline" : "…"}</Badge>
          )}
        </header>
        <main className="flex-1 space-y-6 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
