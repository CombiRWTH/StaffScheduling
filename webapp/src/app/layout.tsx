import { NavigationWrapper } from "@/components/app-navigation";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body>
        <NavigationWrapper />
        <main className="min-h-screen p-4 md:ml-72">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
        <Toaster />
      </body>
    </html>
  );
}
