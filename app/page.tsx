import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card/50 to-primary/5">
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto backdrop-blur-sm bg-background/80 rounded-2xl mx-6 mt-4 border border-border/50">
        <div className="flex items-center space-x-3">
          <div className="text-3xl gentle-pulse">🌿</div>
          <span className="text-2xl font-serif font-bold text-foreground">Eirenic</span>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" className="hover:bg-primary/10 hover:border-primary/50 bg-transparent" asChild>
            <Link href="/login">Sign In</Link>
          </Button>
          <Button className="bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl" asChild>
            <Link href="/register">Register</Link>
          </Button>
        </div>
      </nav>

      <section className="text-center py-24 px-6 max-w-5xl mx-auto">
        <div className="mb-12">
          <div className="text-8xl mb-6 block breathe-animation">🌿</div>
          <h1 className="text-6xl font-serif font-bold text-foreground mb-6 text-balance leading-tight">Eirenic</h1>
          <p className="text-2xl text-muted-foreground mb-12 text-balance font-medium">
            Supporting Students, Strengthening Success
          </p>
        </div>

        <div className="bg-gradient-to-r from-primary/5 via-card to-accent/5 rounded-3xl p-16 mb-16 border border-border/30 shadow-2xl backdrop-blur-sm">
          <h2 className="text-4xl font-serif font-semibold text-foreground mb-8 text-balance">
            Your Safe Space for Mental Wellness
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto text-pretty leading-relaxed">
            A compassionate platform designed specifically for students, offering professional support, self-care tools,
            and a caring community to help you thrive academically and personally.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Button
              size="lg"
              className="text-lg px-12 py-4 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all"
              asChild
            >
              <Link href="/register">Get Started Today</Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="text-lg px-12 py-4 bg-background/50 hover:bg-primary/10 hover:border-primary/50 backdrop-blur-sm"
              asChild
            >
              <Link href="/login">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="py-20 px-6 max-w-7xl mx-auto">
        <h2 className="text-4xl font-serif font-bold text-center text-foreground mb-16 text-balance">
          Why Choose Eirenic?
        </h2>

        <div className="grid md:grid-cols-3 gap-8">
          <Card className="text-center border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 bg-card/80 backdrop-blur-sm float-animation">
            <CardHeader className="pb-4">
              <div className="text-5xl mb-6 gentle-pulse">🛡️</div>
              <CardTitle className="text-2xl text-balance font-serif">Safe Space for Students</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-pretty text-lg leading-relaxed">
                A judgment-free environment where you can express yourself freely, connect with peers, and find the
                support you need without fear or stigma.
              </CardDescription>
            </CardContent>
          </Card>

          <Card
            className="text-center border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 bg-card/80 backdrop-blur-sm float-animation"
            style={{ animationDelay: "2s" }}
          >
            <CardHeader className="pb-4">
              <div className="text-5xl mb-6 gentle-pulse">🔒</div>
              <CardTitle className="text-2xl text-balance font-serif">Confidential Professional Support</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-pretty text-lg leading-relaxed">
                Access to qualified counselors, therapists, and peer supporters who understand student life and are
                committed to your privacy and wellbeing.
              </CardDescription>
            </CardContent>
          </Card>

          <Card
            className="text-center border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 bg-card/80 backdrop-blur-sm float-animation"
            style={{ animationDelay: "4s" }}
          >
            <CardHeader className="pb-4">
              <div className="text-5xl mb-6 gentle-pulse">🧘</div>
              <CardTitle className="text-2xl text-balance font-serif">Self-Care Toolkit</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-pretty text-lg leading-relaxed">
                Comprehensive tools including guided meditation, routine planning, mood assessments, and wellness
                tracking to support your daily mental health.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </section>

      <footer className="bg-gradient-to-r from-card/50 to-primary/5 py-16 px-6 mt-24 border-t border-border/30">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <div className="text-3xl gentle-pulse">🌿</div>
            <span className="text-2xl font-serif font-bold text-foreground">Eirenic</span>
          </div>
          <p className="text-muted-foreground mb-6 text-lg">Supporting Students, Strengthening Success</p>
          <p className="text-sm text-muted-foreground bg-primary/10 rounded-full px-6 py-3 inline-block">
            Remember: You are not alone. Help is always available.
          </p>
        </div>
      </footer>
    </div>
  )
}
