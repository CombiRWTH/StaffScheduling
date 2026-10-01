import { HomePageClient } from "@/components/home-page-client";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string; stations?: string }>;
}) {
  const { month, stations } = await searchParams;
  const params = new URLSearchParams();
  if (month) params.set("month", month);
  if (stations) params.set("stations", stations);
  return <HomePageClient caseSearch={params.size ? `?${params}` : ""} isWorkflowMode={false} />;
}
