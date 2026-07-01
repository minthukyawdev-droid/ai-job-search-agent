import type { Metadata } from "next";
import { BriefcaseBusiness, Bookmark, LayoutDashboard, Search, UserRound } from "lucide-react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Job Search System",
  description: "AI-powered job matching, recommendations, and application tracking"
};

const links = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/recommendations", label: "Recommendations", icon: LayoutDashboard },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/saved", label: "Saved", icon: Bookmark }
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 antialiased">
        <div className="shell">
          <header className="topbar">
            <nav className="nav" aria-label="Main navigation">
              <Link className="brand" href="/">
                <span className="brand-mark">
                  <BriefcaseBusiness size={19} aria-hidden />
                </span>
                AI Job Search
              </Link>
              <div className="nav-links">
                {links.map(({ href, label, icon: Icon }) => (
                  <Link href={href} key={href}>
                    <Icon size={16} aria-hidden />
                    {label}
                  </Link>
                ))}
              </div>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
