"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock login - redirect to dashboard
    router.push("/dashboard")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-accent/20 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <span className="text-3xl">🌿</span>
            <span className="text-2xl font-bold text-foreground">Eirenic</span>
          </Link>
          <p className="text-muted-foreground mt-2">Welcome back</p>
        </div>

        <Card className="border-2">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Sign In</CardTitle>
            <CardDescription>Enter your credentials to access your account</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email or Username</Label>
                <Input
                  id="email"
                  type="text"
                  placeholder="Enter your email or username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12"
                />
              </div>

              <Button type="submit" className="w-full h-12 text-lg">
                Sign In
              </Button>
            </form>

            <div className="mt-6 text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{" "}
                <Link href="/register" className="text-primary hover:text-accent font-medium">
                  Register here
                </Link>
              </p>
              <p className="text-xs text-muted-foreground">
                Forgot your password?{" "}
                <Link href="#" className="text-primary hover:text-accent">
                  Reset it here
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Crisis Support */}
        <Card className="mt-6 border-destructive/20 bg-destructive/5">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm font-medium text-destructive mb-2">🚨 Need immediate help?</p>
              <p className="text-xs text-muted-foreground mb-3">If you're in crisis, please reach out immediately</p>
              <div className="flex flex-col gap-2">
                <Button variant="outline" size="sm" className="text-xs bg-transparent">
                  Crisis Hotline: 988
                </Button>
                <Button variant="outline" size="sm" className="text-xs bg-transparent">
                  Campus Counseling
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
