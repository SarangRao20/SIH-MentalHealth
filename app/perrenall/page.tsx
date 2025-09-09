"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

const questions = [
  {
    id: 1,
    question: "How would you describe your current stress level?",
    options: ["Very Low", "Low", "Moderate", "High", "Very High"],
  },
  {
    id: 2,
    question: "How often do you feel overwhelmed by daily tasks?",
    options: ["Never", "Rarely", "Sometimes", "Often", "Always"],
  },
  {
    id: 3,
    question: "What time of day do you feel most energetic?",
    options: ["Early Morning", "Mid Morning", "Afternoon", "Evening", "Night"],
  },
  {
    id: 4,
    question: "How do you prefer to handle challenges?",
    options: ["Head-on", "Step by step", "With support", "Take breaks", "Avoid initially"],
  },
  {
    id: 5,
    question: "What environment helps you feel most calm?",
    options: ["Bright & Sunny", "Dim & Cozy", "Natural & Green", "Minimal & Clean", "Colorful & Vibrant"],
  },
]

const plants = {
  "Resilient Oak": {
    emoji: "🌳",
    description:
      "Strong and steady, the Oak represents resilience and grounding. Perfect for those who face challenges head-on.",
    traits: ["Stability", "Strength", "Endurance"],
    color: "#8B4513",
  },
  "Gentle Fern": {
    emoji: "🌿",
    description: "Delicate yet persistent, the Fern thrives in gentle environments and represents gradual growth.",
    traits: ["Patience", "Adaptability", "Grace"],
    color: "#228B22",
  },
  "Bright Sunflower": {
    emoji: "🌻",
    description: "Always reaching toward the light, the Sunflower embodies optimism and energy.",
    traits: ["Positivity", "Energy", "Growth"],
    color: "#FFD700",
  },
  "Calm Lavender": {
    emoji: "💜",
    description: "Soothing and peaceful, Lavender brings tranquility and helps manage stress naturally.",
    traits: ["Serenity", "Balance", "Healing"],
    color: "#E6E6FA",
  },
  "Vibrant Lotus": {
    emoji: "🪷",
    description: "Rising from muddy waters to bloom beautifully, the Lotus represents transformation and renewal.",
    traits: ["Transformation", "Purity", "Enlightenment"],
    color: "#FF69B4",
  },
}

export default function PerrenAllPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [assignedPlant, setAssignedPlant] = useState<string | null>(null)
  const [plantGrowth, setPlantGrowth] = useState(0)

  const handleAnswer = (answer: string) => {
    const newAnswers = [...answers, answer]
    setAnswers(newAnswers)

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      // Assign plant based on answers
      const plantNames = Object.keys(plants)
      const selectedPlant = plantNames[Math.floor(Math.random() * plantNames.length)]
      setAssignedPlant(selectedPlant)
      setIsComplete(true)

      // Start plant growth animation
      setTimeout(() => setPlantGrowth(25), 500)
      setTimeout(() => setPlantGrowth(50), 1500)
      setTimeout(() => setPlantGrowth(75), 2500)
      setTimeout(() => setPlantGrowth(100), 3500)
    }
  }

  const resetAssessment = () => {
    setCurrentQuestion(0)
    setAnswers([])
    setIsComplete(false)
    setAssignedPlant(null)
    setPlantGrowth(0)
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <main className="ml-64 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-serif font-bold text-foreground mb-4">PerrenAll 🌱</h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Discover your perfect plant companion! Answer a few questions about your daily life and mental health, and
              we'll pair you with a plant that suits your needs and grows alongside your wellness journey.
            </p>
          </div>

          {!isComplete ? (
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <div className="flex justify-between items-center mb-4">
                  <CardTitle className="text-xl">
                    Question {currentQuestion + 1} of {questions.length}
                  </CardTitle>
                  <Progress value={(currentQuestion / questions.length) * 100} className="w-32" />
                </div>
                <CardDescription className="text-lg">{questions[currentQuestion].question}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {questions[currentQuestion].options.map((option, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="w-full justify-start h-auto p-4 text-left hover:bg-accent hover:text-accent-foreground transition-all duration-200 bg-transparent"
                    onClick={() => handleAnswer(option)}
                  >
                    {option}
                  </Button>
                ))}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-8">
              <Card className="max-w-2xl mx-auto text-center">
                <CardHeader>
                  <CardTitle className="text-2xl text-primary mb-4">Meet Your Plant Companion!</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {assignedPlant && (
                    <>
                      <div className="text-8xl plant-grow leaf-sway">
                        {plants[assignedPlant as keyof typeof plants].emoji}
                      </div>
                      <div>
                        <h3 className="text-2xl font-semibold mb-2">{assignedPlant}</h3>
                        <p className="text-muted-foreground mb-4">
                          {plants[assignedPlant as keyof typeof plants].description}
                        </p>
                        <div className="flex justify-center gap-2 mb-6">
                          {plants[assignedPlant as keyof typeof plants].traits.map((trait, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-accent text-accent-foreground rounded-full text-sm"
                            >
                              {trait}
                            </span>
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold">Your Plant's Growth Progress</h4>
                    <Progress value={plantGrowth} className="w-full" />
                    <p className="text-sm text-muted-foreground">
                      Your plant grows as you engage with wellness activities on Eirenic!
                    </p>
                  </div>

                  <div className="flex gap-4 justify-center">
                    <Button onClick={resetAssessment} variant="outline">
                      Take Assessment Again
                    </Button>
                    <Button asChild>
                      <a href="/dashboard">Go to Dashboard</a>
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle className="text-xl">How Your Plant Grows</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">🧘</span>
                      <div>
                        <p className="font-medium">Meditation Sessions</p>
                        <p className="text-sm text-muted-foreground">+5 growth points</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">✅</span>
                      <div>
                        <p className="font-medium">Completed Routines</p>
                        <p className="text-sm text-muted-foreground">+3 growth points</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">📊</span>
                      <div>
                        <p className="font-medium">Assessment Check-ins</p>
                        <p className="text-sm text-muted-foreground">+7 growth points</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">💬</span>
                      <div>
                        <p className="font-medium">Support Interactions</p>
                        <p className="text-sm text-muted-foreground">+4 growth points</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
