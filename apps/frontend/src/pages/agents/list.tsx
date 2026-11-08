import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { QueryState } from "@/components/query-state";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatAtomic, shortAddress } from "@/lib/format";

export function AgentsListPage() {
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.agents.list });

  return (
    <>
      <PageHeader
        title="Agents"
        description="Agent của bạn: config, ví Turnkey, ERC-8004 identity."
        actions={
          <Button asChild>
            <Link to="/agents/new">
              <Plus /> Tạo agent
            </Link>
          </Button>
        }
      />
      <Card>
        <CardContent>
          <QueryState query={agents} feature="GET /agents">
            {(rows) =>
              rows.length === 0 ? (
                <p className="text-muted-foreground p-6 text-center text-sm">Chưa có agent nào.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tên</TableHead>
                      <TableHead>Slug</TableHead>
                      <TableHead>Trạng thái</TableHead>
                      <TableHead>Settlement</TableHead>
                      <TableHead>Giá (USDC)</TableHead>
                      <TableHead>Ví</TableHead>
                      <TableHead>ERC-8004 ID</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <Link to={`/agents/${a.id}`} className="font-medium hover:underline">
                            {a.name}
                          </Link>
                        </TableCell>
                        <TableCell className="font-mono text-xs">{a.slug}</TableCell>
                        <TableCell>
                          <StatusBadge status={a.status} />
                        </TableCell>
                        <TableCell>{a.settlement_mode}</TableCell>
                        <TableCell>{formatAtomic(a.price_atomic)}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {shortAddress(a.wallet_address)}
                        </TableCell>
                        <TableCell>{a.erc8004_agent_id ?? "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )
            }
          </QueryState>
        </CardContent>
      </Card>
    </>
  );
}
