"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: "🏠" },
  { name: "Meditation", href: "/meditation", icon: "🧘" },
  { name: "Routine", href: "/routine", icon: "📅" },
  { name: "Chat Support", href: "/chat", icon: "💬" },
  { name: "Assessment", href: "/assessment", icon: "📊" },
  { name: "Consultation", href: "/consultation", icon: "👩‍⚕️" },
  { name: "Venting Hall", href: "/venting", icon: "🌐" },
  { name: "PerrenAll", href: "/perrenall", icon: "🌱" },
]

function HamburgerIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}

function LogoutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 11-6 0v-1m0-10V5a3 3 0 116 0v1"
      />
    </svg>
  )
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  const handleLogout = () => {
    alert("Logout clicked")
  }

  return (
    <div
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 flex flex-col",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex items-center border-b border-sidebar-border p-4 justify-between">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center space-x-2 select-none">
            <span className="text-2xl">🌿</span>
            <span className="text-xl font-bold text-sidebar-foreground">Eirenic</span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed((prev) => !prev)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="text-sidebar-foreground hover:text-accent-foreground focus:outline-none"
        >
          <HamburgerIcon />
        </button>
      </div>

      {/* Nav links */}
      <nav className={cn("flex-1 p-4 space-y-2", collapsed && "flex flex-col items-center")}>
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <Button
                variant={isActive ? "default" : "ghost"}
                className={cn(
                  "w-full justify-start gap-3 h-12 text-left transition-all",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  collapsed && "w-12 justify-center px-0"
                )}
              >
                <span className="text-lg">{item.icon}</span>
                {!collapsed && <span>{item.name}</span>}
              </Button>
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="border-t border-sidebar-border p-4">
        <Button
          variant="ghost"
          className={cn(
            "w-full h-12 gap-3 transition-all",
            collapsed ? "justify-center px-0" : "justify-start"
          )}
          onClick={handleLogout}
        >
          <LogoutIcon className="text-lg" />
          {!collapsed && <span>Logout</span>}
        </Button>
      </div>

      {/* Crisis Support */}
      {!collapsed && (
        <div className="p-4 border-t border-sidebar-border">
          <div className="bg-destructive/10 rounded-lg p-3 text-center">
            <p className="text-xs font-medium text-destructive mb-2">🚨 Need immediate help?</p>
            <Button size="sm" variant="outline" className="w-full text-xs bg-transparent">
              Crisis Support
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
