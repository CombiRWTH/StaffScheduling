import { NavigationWrapper } from "@/components/app-navigation";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="md:flex">
        <NavigationWrapper />
        <main className="min-h-screen min-w-0 flex-1 p-4">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </body>
    </html>
  );
}
