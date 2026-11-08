import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/app-shell";
import { AgentDetailPage } from "@/pages/agents/detail";
import { AgentsListPage } from "@/pages/agents/list";
import { NewAgentPage } from "@/pages/agents/new";
import { DashboardPage } from "@/pages/dashboard";
import { JobsPage } from "@/pages/jobs";
import { MarketplacePage } from "@/pages/marketplace";
import { NotFoundPage } from "@/pages/not-found";
import { WalletPage } from "@/pages/wallet";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "agents", element: <AgentsListPage /> },
      { path: "agents/new", element: <NewAgentPage /> },
      { path: "agents/:id", element: <AgentDetailPage /> },
      { path: "marketplace", element: <MarketplacePage /> },
      { path: "wallet", element: <WalletPage /> },
      { path: "jobs", element: <JobsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
