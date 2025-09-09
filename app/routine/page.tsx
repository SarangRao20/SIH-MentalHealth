"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Sidebar } from "@/components/sidebar"

interface Task {
  id: number
  title: string
  startTime: string
  endTime: string
  notes: string
  completed: boolean
}

export default function RoutinePage() {
  const [tasks, setTasks] = useState<Task[]>([
    { id: 1, title: "Morning Exercise", startTime: "07:00", endTime: "08:00", notes: "30 min walk", completed: true },
    { id: 2, title: "Study Session", startTime: "09:00", endTime: "11:00", notes: "Math homework", completed: false },
    { id: 3, title: "Lunch Break", startTime: "12:00", endTime: "13:00", notes: "", completed: false },
  ])

  const [newTask, setNewTask] = useState({
    title: "",
    startTime: "",
    endTime: "",
    notes: "",
  })

  const [showMotivation, setShowMotivation] = useState(false)

  const motivationalQuotes = [
    "Great job! Every completed task is a step toward your goals! 🌟",
    "You're doing amazing! Keep up the momentum! 💪",
    "Fantastic work! You're building great habits! 🎯",
    "Well done! Your consistency is inspiring! ✨",
    "Excellent! You're taking control of your day! 🚀",
  ]

  const addTask = (e: React.FormEvent) => {
    e.preventDefault()
    if (newTask.title && newTask.startTime && newTask.endTime) {
      const task: Task = {
        id: Date.now(),
        ...newTask,
        completed: false,
      }
      setTasks([...tasks, task].sort((a, b) => a.startTime.localeCompare(b.startTime)))
      setNewTask({ title: "", startTime: "", endTime: "", notes: "" })
    }
  }

  const toggleTask = (id: number) => {
    setTasks(
      tasks.map((task) => {
        if (task.id === id) {
          const updatedTask = { ...task, completed: !task.completed }
          if (updatedTask.completed) {
            setShowMotivation(true)
            setTimeout(() => setShowMotivation(false), 3000)
          }
          return updatedTask
        }
        return task
      }),
    )
  }

  const completedTasks = tasks.filter((task) => task.completed).length

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-foreground mb-2">Daily Routine 📅</h1>
          <p className="text-muted-foreground mb-8">Plan your day and track your progress</p>

          {/* Progress Overview */}
          <Card className="mb-8 bg-gradient-to-r from-primary/10 to-accent/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">Today's Progress</h3>
                  <p className="text-muted-foreground">
                    {completedTasks} of {tasks.length} tasks completed
                  </p>
                </div>
                <div className="text-3xl font-bold text-primary">
                  {tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0}%
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Add New Task */}
            <Card>
              <CardHeader>
                <CardTitle>Add New Task</CardTitle>
                <CardDescription>Schedule a new activity for your day</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={addTask} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Task Title</Label>
                    <Input
                      id="title"
                      placeholder="What do you want to do?"
                      value={newTask.title}
                      onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="startTime">Start Time</Label>
                      <Input
                        id="startTime"
                        type="time"
                        value={newTask.startTime}
                        onChange={(e) => setNewTask({ ...newTask, startTime: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="endTime">End Time</Label>
                      <Input
                        id="endTime"
                        type="time"
                        value={newTask.endTime}
                        onChange={(e) => setNewTask({ ...newTask, endTime: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes (Optional)</Label>
                    <Textarea
                      id="notes"
                      placeholder="Any additional details..."
                      value={newTask.notes}
                      onChange={(e) => setNewTask({ ...newTask, notes: e.target.value })}
                      rows={3}
                    />
                  </div>

                  <Button type="submit" className="w-full">
                    Add Task
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Task List */}
            <Card>
              <CardHeader>
                <CardTitle>Today's Schedule</CardTitle>
                <CardDescription>
                  {tasks.length === 0
                    ? "No tasks scheduled yet. Start by adding one small task!"
                    : "Check off tasks as you complete them"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {tasks.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">📝</div>
                    <p className="text-muted-foreground">No tasks scheduled yet. Start by adding one small task!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                      <div
                        key={task.id}
                        className={`flex items-start space-x-3 p-3 rounded-lg border ${
                          task.completed ? "bg-accent/20 border-accent/50" : "bg-card border-border"
                        }`}
                      >
                        <Checkbox
                          checked={task.completed}
                          onCheckedChange={() => toggleTask(task.id)}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4
                              className={`font-medium ${
                                task.completed ? "line-through text-muted-foreground" : "text-foreground"
                              }`}
                            >
                              {task.title}
                            </h4>
                            <span className="text-sm text-muted-foreground">
                              {task.startTime} - {task.endTime}
                            </span>
                          </div>
                          {task.notes && (
                            <p
                              className={`text-sm ${
                                task.completed ? "text-muted-foreground" : "text-muted-foreground"
                              }`}
                            >
                              {task.notes}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Motivational Popup */}
          {showMotivation && (
            <div className="fixed bottom-6 right-6 z-50">
              <Card className="border-2 border-accent bg-accent/10 gentle-pulse">
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm font-medium text-foreground">
                    {motivationalQuotes[Math.floor(Math.random() * motivationalQuotes.length)]}
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
