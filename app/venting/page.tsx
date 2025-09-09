"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Sidebar } from "@/components/sidebar"

interface Post {
  id: number
  username: string
  content: string
  timestamp: string
  likes: number
  comments: number
  isLiked: boolean
}

export default function VentingPage() {
  const [posts, setPosts] = useState<Post[]>([
    {
      id: 1,
      username: "StudentA",
      content: "Feeling overwhelmed with midterms coming up. Anyone else struggling with time management?",
      timestamp: "2 hours ago",
      likes: 12,
      comments: 5,
      isLiked: false,
    },
    {
      id: 2,
      username: "Anonymous",
      content: "Just wanted to say that it's okay to not be okay. We're all in this together. 💙",
      timestamp: "4 hours ago",
      likes: 28,
      comments: 8,
      isLiked: true,
    },
    {
      id: 3,
      username: "StudentB",
      content:
        "Had a panic attack during my presentation today. Feeling embarrassed but trying to remind myself that it happens.",
      timestamp: "6 hours ago",
      likes: 15,
      comments: 12,
      isLiked: false,
    },
  ])

  const [newPost, setNewPost] = useState("")
  const [isAnonymous, setIsAnonymous] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (newPost.trim()) {
      const post: Post = {
        id: Date.now(),
        username: isAnonymous ? "Anonymous" : "You",
        content: newPost,
        timestamp: "Just now",
        likes: 0,
        comments: 0,
        isLiked: false,
      }
      setPosts([post, ...posts])
      setNewPost("")
    }
  }

  const toggleLike = (id: number) => {
    setPosts(
      posts.map((post) => {
        if (post.id === id) {
          return {
            ...post,
            isLiked: !post.isLiked,
            likes: post.isLiked ? post.likes - 1 : post.likes + 1,
          }
        }
        return post
      }),
    )
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 p-6 ml-64">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Venting Hall 🌐</h1>
              <p className="text-muted-foreground">A safe space to share your thoughts and feelings</p>
            </div>
            <Button>+ Share Your Thoughts</Button>
          </div>

          {/* Crisis Banner */}
          <Card className="mb-6 border-destructive/20 bg-destructive/5">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-destructive mb-1">🚨 Remember: You Are Not Alone</p>
                  <p className="text-sm text-muted-foreground">
                    If you're in crisis, please reach out for immediate support
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">
                    Call 988
                  </Button>
                  <Button size="sm" variant="outline">
                    Chat Now
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* New Post Form */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Share Your Thoughts</CardTitle>
              <CardDescription>Express yourself freely in this supportive community</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Textarea
                  placeholder="What's on your mind? Remember, this is a safe space..."
                  value={newPost}
                  onChange={(e) => setNewPost(e.target.value)}
                  rows={4}
                  className="resize-none"
                />
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      checked={isAnonymous}
                      onChange={(e) => setIsAnonymous(e.target.checked)}
                      className="rounded"
                    />
                    <span>Post anonymously</span>
                  </label>
                  <Button type="submit" disabled={!newPost.trim()}>
                    Share
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Posts Feed */}
          <div className="space-y-4">
            {posts.map((post) => (
              <Card key={post.id} className="hover:border-primary/30 transition-colors">
                <CardContent className="pt-4">
                  <div className="flex items-start space-x-3">
                    <Avatar>
                      <AvatarFallback>{post.username === "Anonymous" ? "?" : post.username[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-medium text-foreground">{post.username}</span>
                        <span className="text-sm text-muted-foreground">{post.timestamp}</span>
                      </div>
                      <p className="text-foreground mb-4 text-pretty">{post.content}</p>
                      <div className="flex items-center space-x-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleLike(post.id)}
                          className={post.isLiked ? "text-red-500" : ""}
                        >
                          ❤️ {post.likes}
                        </Button>
                        <Button variant="ghost" size="sm">
                          💬 {post.comments}
                        </Button>
                        <Button variant="ghost" size="sm">
                          🤝 Support
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Floating Emergency Button */}
          <Button
            className="fixed bottom-6 right-6 rounded-full w-14 h-14 shadow-lg bg-destructive hover:bg-destructive/90"
            size="sm"
          >
            🚨
          </Button>
        </div>
      </main>
    </div>
  )
}
