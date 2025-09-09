"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Sidebar } from "@/components/sidebar"

export default function MeditationPage() {
  const [isActive, setIsActive] = useState(false)
  const [timeLeft, setTimeLeft] = useState(300) // 5 minutes default
  const [selectedDuration, setSelectedDuration] = useState(5)
  const [showCompletion, setShowCompletion] = useState(false)

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (isActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((timeLeft) => timeLeft - 1)
      }, 1000)
    } else if (timeLeft === 0) {
      setIsActive(false)
      setShowCompletion(true)
      setTimeout(() => setShowCompletion(false), 3000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isActive, timeLeft])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const startMeditation = (duration: number) => {
    setSelectedDuration(duration)
    setTimeLeft(duration * 60)
    setIsActive(true)
  }

  const toggleMeditation = () => {
    setIsActive(!isActive)
  }

  const resetMeditation = () => {
    setIsActive(false)
    setTimeLeft(selectedDuration * 60)
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-foreground mb-2">Meditation 🧘</h1>
          <p className="text-muted-foreground mb-8">Take a moment to breathe, relax, and center yourself</p>

          {!isActive && timeLeft === selectedDuration * 60 ? (
            /* Meditation Options */
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <Card
                className="hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => startMeditation(5)}
              >
                <CardHeader className="text-center">
                  <div className="text-4xl mb-2">🌸</div>
                  <CardTitle>Guided Meditation</CardTitle>
                  <CardDescription>5-minute guided breathing session</CardDescription>
                </CardHeader>
              </Card>

              <Card
                className="hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => startMeditation(10)}
              >
                <CardHeader className="text-center">
                  <div className="text-4xl mb-2">🎵</div>
                  <CardTitle>Calming Music</CardTitle>
                  <CardDescription>10-minute relaxing soundscape</CardDescription>
                </CardHeader>
              </Card>

              <Card
                className="hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => startMeditation(3)}
              >
                <CardHeader className="text-center">
                  <div className="text-4xl mb-2">💨</div>
                  <CardTitle>Breathing Exercise</CardTitle>
                  <CardDescription>3-minute focused breathing</CardDescription>
                </CardHeader>
              </Card>
            </div>
          ) : (
            /* Active Meditation Session */
            <div className="text-center">
              <Card className="max-w-md mx-auto mb-8 bg-gradient-to-br from-primary/10 to-accent/10">
                <CardContent className="pt-8 pb-8">
                  {/* Breathing Animation */}
                  <div className="mb-8">
                    <div className="w-32 h-32 mx-auto bg-gradient-to-br from-primary to-accent rounded-full breathe-animation flex items-center justify-center">
                      <span className="text-white text-2xl">🌸</span>
                    </div>
                  </div>

                  {/* Timer */}
                  <div className="text-4xl font-bold text-foreground mb-4">{formatTime(timeLeft)}</div>

                  {/* Breathing Instructions */}
                  <p className="text-lg text-muted-foreground mb-6">
                    {isActive ? "Breathe In... Breathe Out..." : "Paused"}
                  </p>

                  {/* Controls */}
                  <div className="flex gap-4 justify-center">
                    <Button onClick={toggleMeditation} size="lg">
                      {isActive ? "Pause" : "Resume"}
                    </Button>
                    <Button onClick={resetMeditation} variant="outline" size="lg">
                      Reset
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Completion Overlay */}
          {showCompletion && (
            <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
              <Card className="max-w-sm mx-auto text-center border-2 border-primary">
                <CardContent className="pt-8 pb-8">
                  <div className="text-6xl mb-4">🎉</div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Congratulations!</h2>
                  <p className="text-muted-foreground">You completed your meditation session. Well done!</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Benefits Section */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">💡 Benefits of Meditation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm text-muted-foreground">• Reduces stress and anxiety</p>
                <p className="text-sm text-muted-foreground">• Improves focus and concentration</p>
                <p className="text-sm text-muted-foreground">• Enhances emotional wellbeing</p>
                <p className="text-sm text-muted-foreground">• Promotes better sleep</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">📈 Your Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-primary mb-2">45 minutes</p>
                <p className="text-sm text-muted-foreground mb-4">Total meditation time this week</p>
                <p className="text-sm text-muted-foreground">
                  Keep up the great work! Regular practice leads to lasting benefits.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
