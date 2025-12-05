"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CalendarDays, Maximize2, Upload } from "lucide-react"
import { ScheduleTable } from "@/components/schedule-table"
import { StatsGrid } from "@/components/stats-grid"
import { parseSolutionFile, type SolutionData } from "@/lib/solution-parser"
import { cn } from "@/lib/utils"

export default function ScheduleDashboard() {
  const [solutionData, setSolutionData] = useState<SolutionData | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [error, setError] = useState<string>("")
  const tableRef = useRef<HTMLDivElement>(null)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError("")
    setFileName(file.name)

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target?.result as string)
        const parsed = parseSolutionFile(jsonData)
        setSolutionData(parsed)
      } catch (err) {
        setError("Failed to parse solution file. Please check the file format.")
        console.error(err)
      }
    }
    reader.readAsText(file)
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement && tableRef.current) {
      tableRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-6 lg:p-8">
      <div className="mx-auto max-w-[1800px] space-y-6">
        {/* Header */}
        <header className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight text-foreground">Staff Scheduling</h1>
              <p className="text-muted-foreground">Analyze and visualize employee shift schedules</p>
            </div>
            {solutionData && (
              <Badge variant="outline" className="gap-2">
                <CalendarDays className="h-4 w-4" />
                {solutionData.days.length} Days
              </Badge>
            )}
          </div>

          {/* Controls */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex-1 max-w-sm space-y-2">
              <label htmlFor="file-upload" className="text-sm font-medium text-foreground">
                Solution File
              </label>
              <div className="flex gap-2">
                <Button
                  onClick={() => document.getElementById("file-upload")?.click()}
                  variant="outline"
                  className="gap-2 w-full justify-start"
                >
                  <Upload className="h-4 w-4" />
                  {fileName || "Upload solution.json"}
                </Button>
                <input id="file-upload" type="file" accept=".json" onChange={handleFileUpload} className="hidden" />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
            <Button onClick={toggleFullscreen} variant="outline" className="gap-2 bg-transparent">
              <Maximize2 className="h-4 w-4" />
              Fullscreen
            </Button>
          </div>
        </header>

        {solutionData ? (
          <>
            {/* Statistics Grid */}
            <StatsGrid stats={solutionData.stats} />

            {/* Schedule Table */}
            <Card
              ref={tableRef}
              className={cn(
                "overflow-hidden border-border/50 shadow-lg",
                isFullscreen && "h-screen w-screen bg-background flex flex-col p-4 rounded-none border-0"
              )}
            >
              <ScheduleTable
                employees={solutionData.employees}
                days={solutionData.days}
                shifts={solutionData.shifts}
                variables={solutionData.variables}
                fulfilledDayOffCells={solutionData.fulfilledDayOffCells}
                fulfilledShiftWishCells={solutionData.fulfilledShiftWishCells}
                allDayOffWishCells={solutionData.allDayOffWishCells}
                allShiftWishColors={solutionData.allShiftWishColors}
                className={isFullscreen ? "h-full max-h-none" : undefined}
              />
            </Card>


            {/* Legend */}
            <Card className="border-border/50 p-6">
              <h3 className="mb-4 text-sm font-semibold text-foreground">Legend</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 h-4 w-4 rounded bg-amber-400/20 border border-amber-400/40" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Day Off Wish Fulfilled</p>
                    <p className="text-xs text-muted-foreground">Employee got requested day off</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 h-4 w-4 rounded bg-emerald-400/20 border border-emerald-400/40" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Shift Wish Fulfilled</p>
                    <p className="text-xs text-muted-foreground">Avoided unwanted shift</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 h-4 w-4 rounded bg-muted" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Weekend</p>
                    <p className="text-xs text-muted-foreground">Saturday or Sunday</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 h-4 w-4 rounded bg-destructive/20 border border-destructive/40" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Overtime</p>
                    <p className="text-xs text-muted-foreground">Exceeded target hours</p>
                  </div>
                </div>
              </div>
            </Card>
          </>
        ) : (
          <Card className="border-border/50 p-12">
            <div className="flex flex-col items-center justify-center text-center space-y-4">
              <div className="rounded-full bg-muted p-6">
                <Upload className="h-12 w-12 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-semibold text-foreground">No Solution Loaded</h3>
                <p className="text-muted-foreground max-w-md">
                  Upload a solution.json file to view the staff scheduling analysis and visualizations.
                </p>
              </div>
              <Button onClick={() => document.getElementById("file-upload")?.click()} className="gap-2">
                <Upload className="h-4 w-4" />
                Upload Solution File
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
