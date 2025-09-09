import type React from "react"
import type { Metadata } from "next"
import { Playfair_Display, Source_Sans_3 } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { Suspense } from "react"
import {Sidebar} from "@/components/sidebar"


import "./globals.css"

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
})

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-source-sans",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Eirenic - Supporting Students, Strengthening Success",
  description: "A compassionate mental health support platform designed specifically for students",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body
        className={`font-sans ${playfair.variable} ${sourceSans.variable} antialiased`}
      >
        <Suspense fallback={<div>Loading...</div>}>
          <div className="flex min-h-screen">
            {/* Sidebar */}
            <Sidebar />

            {/* Main content */}
            <main className="flex-1 min-w-0 bg-red-200">
              {children}
            </main>
          </div>

          <Analytics />
        </Suspense>
      </body>
    </html>
  )
}
