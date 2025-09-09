"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Sidebar } from "@/components/sidebar"

interface Message {
  id: number
  text: string
  sender: "user" | "bot"
  timestamp: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm here to listen and support you. How are you feeling today?",
      sender: "bot",
      timestamp: "Just now",
    },
  ])

  const [inputMessage, setInputMessage] = useState("")

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputMessage.trim()) {
      // Add user message
      const userMessage: Message = {
        id: Date.now(),
        text: inputMessage,
        sender: "user",
        timestamp: "Just now",
      }

      setMessages((prev) => [...prev, userMessage])

      // Auto-reply from bot
      setTimeout(() => {
        const botMessage: Message = {
          id: Date.now() + 1,
          text: "We hear you. You're not alone. Thank you for sharing with us. Is there anything specific you'd like to talk about or any way I can help you right now?",
          sender: "bot",
          timestamp: "Just now",
        }
        setMessages((prev) => [...prev, botMessage])
      }, 1000)

      setInputMessage("")
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-2xl mx-auto h-[calc(100vh-3rem)] flex flex-col">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-foreground mb-2">Chat Support 💬</h1>
            <p className="text-muted-foreground">Immediate support when you need someone to talk to</p>
          </div>

          {/* Crisis Banner */}
          <Card className="mb-6 border-destructive/20 bg-destructive/5">
            <CardContent className="pt-4 pb-4">
              <div className="text-center">
                <p className="font-medium text-destructive mb-2">🚨 In Crisis? Get Immediate Help</p>
                <div className="flex justify-center gap-2">
                  <Button size="sm" variant="outline">
                    Call 988
                  </Button>
                  <Button size="sm" variant="outline">
                    Text Crisis Line
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Chat Container */}
          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">💚 Support Chat</CardTitle>
              <CardDescription>This is a safe space. Share what's on your mind.</CardDescription>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 max-h-96">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      <p className="text-sm text-pretty">{message.text}</p>
                      <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Input Form */}
              <form onSubmit={sendMessage} className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type your message here..."
                  className="flex-1"
                />
                <Button type="submit" disabled={!inputMessage.trim()}>
                  Send
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Support Info */}
          <Card className="mt-4">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">
                  💙 Remember: You are valued, you matter, and help is always available.
                </p>
                <p className="text-xs text-muted-foreground">
                  For professional counseling, visit our Consultation page.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
