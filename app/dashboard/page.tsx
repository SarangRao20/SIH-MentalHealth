"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import Link from "next/link"


export default function DashboardPage() {
  const [user] = useState({ name: "Alex", meditationMinutes: 45, tasksCompleted: 8 })

  const motivationalQuotes = [
    "You are stronger than you think and more capable than you imagine.",
    "Every small step forward is progress worth celebrating.",
    "Your mental health matters, and taking care of yourself is not selfish.",
    "You have survived 100% of your difficult days so far. You're doing great.",
    "Healing is not linear, and that's perfectly okay.",
  ]

  const todayQuote = motivationalQuotes[Math.floor(Math.random() * motivationalQuotes.length)]

  return (
    <div className="flex min-h-screen bg-background">

      <main className="flex-1 p-6">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back, {user.name} 👋</h1>
          <p className="text-muted-foreground">How are you feeling today? Remember, every step counts.</p>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">🧘 Meditation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary mb-2">{user.meditationMinutes} min</div>
              <p className="text-sm text-muted-foreground">This week</p>
              <Progress value={75} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">✅ Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-accent mb-2">{user.tasksCompleted}/10</div>
              <p className="text-sm text-muted-foreground">Completed today</p>
              <Progress value={80} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">💚 Wellness</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary mb-2">Good</div>
              <p className="text-sm text-muted-foreground">Overall mood</p>
              <div className="flex gap-1 mt-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="w-4 h-2 bg-accent rounded-full" />
                ))}
                <div className="w-4 h-2 bg-muted rounded-full" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Daily Quote */}
        <Card className="mb-8 bg-gradient-to-r from-primary/10 to-accent/10 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">✨ Daily Inspiration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg italic text-foreground text-pretty">"{todayQuote}"</p>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/meditation">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">🧘 Start Meditation</CardTitle>
                <CardDescription>Take a moment to breathe and center yourself</CardDescription>
              </CardHeader>
            </Link>
          </Card>

          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/routine">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">📅 Plan Your Day</CardTitle>
                <CardDescription>Organize your tasks and set achievable goals</CardDescription>
              </CardHeader>
            </Link>
          </Card>

          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/assessment">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">📊 Check Your Mood</CardTitle>
                <CardDescription>Quick assessment to track your wellbeing</CardDescription>
              </CardHeader>
            </Link>
          </Card>

          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/venting">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">🌐 Venting Hall</CardTitle>
                <CardDescription>Share your thoughts with the community</CardDescription>
              </CardHeader>
            </Link>
          </Card>

          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/consultation">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">👩‍⚕️ Get Support</CardTitle>
                <CardDescription>Connect with professional counselors</CardDescription>
              </CardHeader>
            </Link>
          </Card>

          <Card className="hover:border-primary/50 transition-colors cursor-pointer">
            <Link href="/chat">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">💬 Chat Support</CardTitle>
                <CardDescription>Immediate support when you need it</CardDescription>
              </CardHeader>
            </Link>
          </Card>
        </div>
      </main>
    </div>
  )
}
