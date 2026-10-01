import { NavigationWrapper } from "@/components/app-navigation";
import { WorkflowBanner } from "@/components/workflow-banner";
import { Toaster } from "@/components/ui/sonner";
import { getWorkflowSession } from "@/infrastructure/services/workflow-session.service";
import "./globals.css";

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const workflowState = await getWorkflowSession();

  return (
    <html lang="de">
      <body>
        <NavigationWrapper
          isLocked={workflowState.isWorkflowMode}
          lockedCaseId={workflowState.caseId}
          lockedMonthYear={workflowState.monthYear}
        />
        <main className="min-h-screen p-4 md:ml-72">
          <div className="mx-auto max-w-7xl">
            <WorkflowBanner state={workflowState} />
            {children}
          </div>
        </main>
        <Toaster />
      </body>
    </html>
  );
}
