import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <p className="text-4xl font-semibold">404</p>
      <p className="text-muted-foreground">Không tìm thấy trang.</p>
      <Button asChild variant="outline">
        <Link to="/">Về Dashboard</Link>
      </Button>
    </div>
  );
}
