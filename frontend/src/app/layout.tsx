import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CyBreach Assurance - Autonomous Cybersecurity Platform",
  description: "Compliance Intelligence and Evidence Verification Engine. Map evidence to controls, verify compliance, calculate resilience, and generate audit-ready reports.",
  keywords: ["CyBreach", "Assurance", "GRC", "Compliance", "Cybersecurity", "Risk Management", "ISO 27001", "GDPR", "NIST"],
  authors: [{ name: "CyBreach Security" }],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
  openGraph: {
    title: "CyBreach Assurance",
    description: "Autonomous Cybersecurity Platform - Module 3: Assurance",
    url: "https://cybreach.io",
    siteName: "CyBreach",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CyBreach Assurance",
    description: "Autonomous Cybersecurity Platform - Compliance Intelligence Engine",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
