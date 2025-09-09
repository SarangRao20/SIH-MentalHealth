"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Sidebar } from "@/components/sidebar"

interface Question {
  id: number
  text: string
  options: { value: string; label: string; score: number }[]
}

interface Assessment {
  id: string
  title: string
  description: string
  icon: string
  questions: Question[]
}

export default function AssessmentPage() {
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [showResults, setShowResults] = useState(false)
  const [results, setResults] = useState<{ score: number; level: string; message: string } | null>(null)

  const assessments: Assessment[] = [
    {
      id: "stress",
      title: "Stress Level Check",
      description: "Assess your current stress levels and get personalized recommendations",
      icon: "😰",
      questions: [
        {
          id: 1,
          text: "How often have you felt overwhelmed in the past week?",
          options: [
            { value: "never", label: "Never", score: 0 },
            { value: "rarely", label: "Rarely", score: 1 },
            { value: "sometimes", label: "Sometimes", score: 2 },
            { value: "often", label: "Often", score: 3 },
            { value: "always", label: "Always", score: 4 },
          ],
        },
        {
          id: 2,
          text: "How well are you sleeping lately?",
          options: [
            { value: "very-well", label: "Very well", score: 0 },
            { value: "well", label: "Well", score: 1 },
            { value: "okay", label: "Okay", score: 2 },
            { value: "poorly", label: "Poorly", score: 3 },
            { value: "very-poorly", label: "Very poorly", score: 4 },
          ],
        },
        {
          id: 3,
          text: "How difficult is it to concentrate on your studies?",
          options: [
            { value: "not-difficult", label: "Not difficult at all", score: 0 },
            { value: "slightly", label: "Slightly difficult", score: 1 },
            { value: "moderately", label: "Moderately difficult", score: 2 },
            { value: "very", label: "Very difficult", score: 3 },
            { value: "extremely", label: "Extremely difficult", score: 4 },
          ],
        },
      ],
    },
    {
      id: "mood",
      title: "Mood Assessment",
      description: "Check in with your emotional wellbeing and mood patterns",
      icon: "😊",
      questions: [
        {
          id: 1,
          text: "How would you describe your mood over the past few days?",
          options: [
            { value: "excellent", label: "Excellent", score: 0 },
            { value: "good", label: "Good", score: 1 },
            { value: "neutral", label: "Neutral", score: 2 },
            { value: "low", label: "Low", score: 3 },
            { value: "very-low", label: "Very low", score: 4 },
          ],
        },
        {
          id: 2,
          text: "How often do you feel hopeful about the future?",
          options: [
            { value: "always", label: "Always", score: 0 },
            { value: "often", label: "Often", score: 1 },
            { value: "sometimes", label: "Sometimes", score: 2 },
            { value: "rarely", label: "Rarely", score: 3 },
            { value: "never", label: "Never", score: 4 },
          ],
        },
      ],
    },
    {
      id: "anxiety",
      title: "Anxiety Check",
      description: "Evaluate anxiety levels and identify coping strategies",
      icon: "😟",
      questions: [
        {
          id: 1,
          text: "How often do you worry about things beyond your control?",
          options: [
            { value: "never", label: "Never", score: 0 },
            { value: "rarely", label: "Rarely", score: 1 },
            { value: "sometimes", label: "Sometimes", score: 2 },
            { value: "often", label: "Often", score: 3 },
            { value: "constantly", label: "Constantly", score: 4 },
          ],
        },
        {
          id: 2,
          text: "Do you experience physical symptoms when anxious (racing heart, sweating, etc.)?",
          options: [
            { value: "never", label: "Never", score: 0 },
            { value: "rarely", label: "Rarely", score: 1 },
            { value: "sometimes", label: "Sometimes", score: 2 },
            { value: "often", label: "Often", score: 3 },
            { value: "always", label: "Always", score: 4 },
          ],
        },
      ],
    },
  ]

  const handleAnswerSelect = (questionId: number, score: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: score }))
  }

  const nextQuestion = () => {
    if (currentQuestion < selectedAssessment!.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      calculateResults()
    }
  }

  const calculateResults = () => {
    const totalScore = Object.values(answers).reduce((sum, score) => sum + score, 0)
    const maxScore = selectedAssessment!.questions.length * 4
    const percentage = (totalScore / maxScore) * 100

    let level: string
    let message: string

    if (percentage <= 25) {
      level = "Low"
      message = "Your levels appear to be in a healthy range. Keep up the good self-care practices!"
    } else if (percentage <= 50) {
      level = "Moderate"
      message = "You're experiencing some challenges. Consider trying our meditation tools or reaching out for support."
    } else if (percentage <= 75) {
      level = "High"
      message =
        "You're dealing with significant stress. We recommend speaking with a counselor and using our support resources."
    } else {
      level = "Very High"
      message =
        "You're experiencing high levels of distress. Please consider reaching out to a professional counselor immediately."
    }

    setResults({ score: totalScore, level, message })
    setShowResults(true)
  }

  const resetAssessment = () => {
    setSelectedAssessment(null)
    setCurrentQuestion(0)
    setAnswers({})
    setShowResults(false)
    setResults(null)
  }

  if (showResults && results) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 p-6 ml-64">
          <div className="max-w-2xl mx-auto">
            <Card className="text-center">
              <CardHeader>
                <div className="text-4xl mb-4">📊</div>
                <CardTitle className="text-2xl">Assessment Results</CardTitle>
                <CardDescription>
                  {selectedAssessment?.title} - {results.level} Level
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary mb-2">{results.level}</div>
                  <Progress
                    value={(results.score / (selectedAssessment!.questions.length * 4)) * 100}
                    className="mb-4"
                  />
                </div>

                <Card className="bg-muted/50">
                  <CardContent className="pt-4">
                    <p className="text-foreground text-pretty">{results.message}</p>
                  </CardContent>
                </Card>

                <div className="space-y-3">
                  <h3 className="font-semibold text-foreground">Recommended Next Steps:</h3>
                  <div className="grid gap-2">
                    <Button variant="outline" className="justify-start bg-transparent">
                      🧘 Try a meditation session
                    </Button>
                    <Button variant="outline" className="justify-start bg-transparent">
                      🌐 Share in the Venting Hall
                    </Button>
                    <Button variant="outline" className="justify-start bg-transparent">
                      👩‍⚕️ Request professional consultation
                    </Button>
                  </div>
                </div>

                <Button onClick={resetAssessment} className="w-full">
                  Take Another Assessment
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    )
  }

  if (selectedAssessment) {
    const question = selectedAssessment.questions[currentQuestion]
    const progress = ((currentQuestion + 1) / selectedAssessment.questions.length) * 100

    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 p-6 ml-64">
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between mb-4">
                  <CardTitle className="flex items-center gap-2">
                    {selectedAssessment.icon} {selectedAssessment.title}
                  </CardTitle>
                  <span className="text-sm text-muted-foreground">
                    {currentQuestion + 1} of {selectedAssessment.questions.length}
                  </span>
                </div>
                <Progress value={progress} className="mb-4" />
              </CardHeader>
              <CardContent className="space-y-6">
                <h3 className="text-lg font-medium text-foreground text-balance">{question.text}</h3>

                <RadioGroup
                  value={answers[question.id]?.toString() || ""}
                  onValueChange={(value) => handleAnswerSelect(question.id, Number.parseInt(value))}
                >
                  {question.options.map((option) => (
                    <div key={option.value} className="flex items-center space-x-2">
                      <RadioGroupItem value={option.score.toString()} id={option.value} />
                      <Label htmlFor={option.value} className="flex-1 cursor-pointer">
                        {option.label}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>

                <div className="flex gap-4">
                  <Button
                    variant="outline"
                    onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
                    disabled={currentQuestion === 0}
                  >
                    Previous
                  </Button>
                  <Button onClick={nextQuestion} disabled={!(question.id in answers)} className="flex-1">
                    {currentQuestion === selectedAssessment.questions.length - 1 ? "Get Results" : "Next"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-foreground mb-2">Mental Health Assessment 📊</h1>
          <p className="text-muted-foreground mb-8">
            Quick, confidential assessments to help you understand your wellbeing
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            {assessments.map((assessment) => (
              <Card
                key={assessment.id}
                className="hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => setSelectedAssessment(assessment)}
              >
                <CardHeader className="text-center">
                  <div className="text-4xl mb-4">{assessment.icon}</div>
                  <CardTitle className="text-xl">{assessment.title}</CardTitle>
                  <CardDescription className="text-pretty">{assessment.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full">Start Assessment</Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Info Section */}
          <Card className="mt-8 bg-gradient-to-r from-primary/10 to-accent/10">
            <CardContent className="pt-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-foreground mb-2">About These Assessments</h3>
                <p className="text-muted-foreground text-pretty">
                  These brief assessments are designed to help you check in with your mental health. They are not
                  diagnostic tools, but can help you understand your current wellbeing and guide you toward appropriate
                  resources and support.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
