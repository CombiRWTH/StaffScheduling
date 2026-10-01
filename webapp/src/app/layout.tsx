import { NavigationWrapper } from "@/components/app-navigation";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body>
        <NavigationWrapper />
        <main className="min-h-screen p-4 md:ml-64">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </body>
    </html>
  );
}
