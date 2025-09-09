"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronDown } from "lucide-react"
import { Sidebar } from "@/components/sidebar"

interface Counselor {
  id: number
  name: string
  type: string
  specialization: string
  availability: string
  rating: number
}

interface ConsultationRequest {
  id: number
  counselor: string
  date: string
  status: string
  type: string
}

export default function ConsultationPage() {
  const [counselors] = useState<Counselor[]>([
    {
      id: 1,
      name: "Dr. Sarah Johnson",
      type: "Therapist",
      specialization: "Anxiety & Depression",
      availability: "Mon-Fri, 9AM-5PM",
      rating: 4.9,
    },
    {
      id: 2,
      name: "Dr. Michael Chen",
      type: "Psychiatrist",
      specialization: "ADHD & Learning Disorders",
      availability: "Tue-Thu, 10AM-4PM",
      rating: 4.8,
    },
    {
      id: 3,
      name: "Emma Rodriguez",
      type: "Peer Counselor",
      specialization: "Student Life & Stress",
      availability: "Daily, 2PM-8PM",
      rating: 4.7,
    },
  ])

  const [requests] = useState<ConsultationRequest[]>([
    {
      id: 1,
      counselor: "Dr. Sarah Johnson",
      date: "March 15, 2024",
      status: "Confirmed",
      type: "Video Call",
    },
  ])

  const [openFAQ, setOpenFAQ] = useState<number | null>(null)

  const faqItems = [
    {
      question: "How quickly can I get an appointment?",
      answer:
        "Most appointments can be scheduled within 24-48 hours. Emergency consultations are available immediately.",
    },
    {
      question: "Is my information confidential?",
      answer: "Yes, all consultations are completely confidential and follow strict privacy guidelines.",
    },
    {
      question: "What should I expect in my first session?",
      answer:
        "Your first session will focus on understanding your needs and creating a comfortable environment for ongoing support.",
    },
    {
      question: "Are services free for students?",
      answer: "Yes, all mental health services are provided free of charge to enrolled students.",
    },
  ]

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Professional Consultation 👩‍⚕️</h1>
              <p className="text-muted-foreground">Connect with qualified mental health professionals</p>
            </div>
            <Button>Request Consultation</Button>
          </div>

          {/* Crisis Banner */}
          <Card className="mb-6 border-destructive/20 bg-destructive/5">
            <CardContent className="pt-4 pb-4">
              <div className="text-center">
                <p className="font-medium text-destructive mb-2">🚨 Need Immediate Support?</p>
                <p className="text-sm text-muted-foreground mb-3">Crisis support is available 24/7</p>
                <div className="flex justify-center gap-2">
                  <Button size="sm" variant="outline">
                    Call 988
                  </Button>
                  <Button size="sm" variant="outline">
                    Text HOME to 741741
                  </Button>
                  <Button size="sm" variant="outline">
                    Chat Support
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Available Counselors */}
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-4">Available Professionals</h2>
              <div className="space-y-4">
                {counselors.map((counselor) => (
                  <Card key={counselor.id} className="hover:border-primary/50 transition-colors">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{counselor.name}</CardTitle>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary">{counselor.type}</Badge>
                            <span className="text-sm text-muted-foreground">⭐ {counselor.rating}</span>
                          </div>
                        </div>
                        <Button size="sm">Book Session</Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-2">
                        <strong>Specialization:</strong> {counselor.specialization}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        <strong>Available:</strong> {counselor.availability}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Consultation Requests & Info */}
            <div className="space-y-6">
              {/* Current Requests */}
              <div>
                <h2 className="text-xl font-semibold text-foreground mb-4">Your Consultation Requests</h2>
                {requests.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <div className="text-4xl mb-4">📅</div>
                      <p className="text-muted-foreground">No consultation requests yet.</p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {requests.map((request) => (
                      <Card key={request.id}>
                        <CardContent className="pt-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-foreground">{request.counselor}</p>
                              <p className="text-sm text-muted-foreground">
                                {request.date} • {request.type}
                              </p>
                            </div>
                            <Badge variant={request.status === "Confirmed" ? "default" : "secondary"}>
                              {request.status}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* What to Expect */}
              <Card>
                <CardHeader>
                  <CardTitle>What to Expect</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-3">
                    <span className="text-primary">📞</span>
                    <div>
                      <p className="font-medium text-sm">Response Time</p>
                      <p className="text-xs text-muted-foreground">Most requests are responded to within 2-4 hours</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-primary">🔒</span>
                    <div>
                      <p className="font-medium text-sm">Confidentiality</p>
                      <p className="text-xs text-muted-foreground">
                        All sessions are completely private and confidential
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-primary">🎓</span>
                    <div>
                      <p className="font-medium text-sm">Student-Focused</p>
                      <p className="text-xs text-muted-foreground">
                        Our professionals specialize in student mental health
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* FAQ */}
              <Card>
                <CardHeader>
                  <CardTitle>Frequently Asked Questions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {faqItems.map((item, index) => (
                    <Collapsible
                      key={index}
                      open={openFAQ === index}
                      onOpenChange={() => setOpenFAQ(openFAQ === index ? null : index)}
                    >
                      <CollapsibleTrigger className="flex items-center justify-between w-full p-2 text-left hover:bg-muted/50 rounded">
                        <span className="text-sm font-medium">{item.question}</span>
                        <ChevronDown className="h-4 w-4" />
                      </CollapsibleTrigger>
                      <CollapsibleContent className="px-2 pb-2">
                        <p className="text-sm text-muted-foreground">{item.answer}</p>
                      </CollapsibleContent>
                    </Collapsible>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
