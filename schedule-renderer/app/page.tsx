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
import { Select, SelectTrigger, SelectContent, SelectValue, SelectItem } from "@/components/ui/select"


export default function ScheduleDashboard() {
  const [solutions, setSolutions] = useState<Record<string, SolutionData>>({})
  const [selectedKey, setSelectedKey] = useState<string>("")
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [error, setError] = useState<string>("")
  const tableRef = useRef<HTMLDivElement>(null)

  const solutionData = selectedKey ? solutions[selectedKey] : null

  const handleFolderUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setError("")
    const newSolutions: Record<string, SolutionData> = {}

    for (const file of Array.from(files)) {
      if (!file.name.endsWith(".json")) continue

      try {
        const text = await file.text()
        const jsonData = JSON.parse(text)
        const parsed = parseSolutionFile(jsonData)
        newSolutions[file.name] = parsed
      } catch (err) {
        console.error("Failed parsing", file.name, err)
        setError(`Fehler beim Parsen: ${file.name}`)
      }
    }

    setSolutions(newSolutions)
    const firstKey = Object.keys(newSolutions)[0]
    if (firstKey) setSelectedKey(firstKey)
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
              <h1 className="text-3xl font-bold tracking-tight text-foreground">Mitarbeiterplanung</h1>
              <p className="text-muted-foreground">Analyse und Visualisierung von Dienstplänen</p>
            </div>

            {solutionData && (
              <Badge variant="outline" className="gap-2">
                <CalendarDays className="h-4 w-4" />
                {solutionData.days.length} Tage
              </Badge>
            )}
          </div>

          {/* Controls */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

            {/* Folder Upload */}
            <div className="flex-1 max-w-sm space-y-2">
              <label htmlFor="folder-upload" className="text-sm font-medium text-foreground">
                Ordner mit JSON-Dateien laden
              </label>
              <div className="flex gap-2">
                <Button
                  onClick={() => document.getElementById("folder-upload")?.click()}
                  variant="outline"
                  className="gap-2 w-full justify-start"
                >
                  <Upload className="h-4 w-4" />
                  Ordner importieren
                </Button>

                {/* Directory upload input */}
                <input
                  id="folder-upload"
                  type="file"
                  accept=".json"
                  onChange={handleFolderUpload}
                  className="hidden"
                  // Important part: allow folder upload
                  webkitdirectory="true"
                />
              </div>

              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>

            {/* Dropdown menu */}
            <div className="max-w-xs w-full">
              <Select
                value={selectedKey}
                onValueChange={setSelectedKey}
                disabled={Object.keys(solutions).length === 0}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Lösung auswählen…" />
                </SelectTrigger>
                <SelectContent>
                  {Object.keys(solutions).map((key) => (
                    <SelectItem key={key} value={key}>{key}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={toggleFullscreen} variant="outline" className="gap-2 bg-transparent">
              <Maximize2 className="h-4 w-4" />
              Vollbild
            </Button>
          </div>
        </header>

        {/* Render selected solution */}
        {solutionData ? (
          <>
            <StatsGrid stats={solutionData.stats} />

            <Card
              ref={tableRef}
              className="overflow-hidden border-border/50 shadow-lg h-screen bg-background flex flex-col p-4 rounded-none border-0"

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
                className="h-full max-h-none"
              />
            </Card>


            {/* Legend */}
            <Card className="border-border/50 p-6">
              <h3 className="mb-4 text-sm font-semibold text-foreground">Legende</h3>
              <div className="grid gap-6">
                {/* Background Meaning Section */}
                <div>
                  <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Hintergrundfarben</h4>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-1 h-4 w-4 rounded bg-amber-400/20 border border-amber-400/40" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Freiwunsch erfüllt</p>
                        <p className="text-xs text-muted-foreground">Mitarbeiter hat gewünschten freien Tag erhalten</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="mt-1 h-4 w-4 rounded bg-emerald-400/20 border border-emerald-400/40" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Schichtwunsch erfüllt</p>
                        <p className="text-xs text-muted-foreground">Unerwünschte Schicht wurde vermieden</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="mt-1 h-4 w-4 rounded bg-muted" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Wochenende</p>
                        <p className="text-xs text-muted-foreground">Samstag oder Sonntag</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="mt-1 h-4 w-4 rounded bg-rose-400/10 border border-destructive/40" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Blockierter Tag</p>
                        <p className="text-xs text-muted-foreground">Mitarbeiter kann an diesem Tag nicht eingeteilt werden</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="mt-1 h-4 w-4 rounded bg-rose-400/50 border border-destructive/40" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Stundenziel verfehlt</p>
                        <p className="text-xs text-muted-foreground">Mitarbeiter weicht mehr als 7,67 Stunden von seinen Zielstunden ab</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Shift Examples */}
                <div>
                  <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Schichten</h4>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {/* Early */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center" style={{ background: "#a8d51f" }}>Früh</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Frühschicht (F)</p>
                        <p className="text-xs text-muted-foreground">Standard Frühschicht</p>
                      </div>
                    </div>
                    {/* Intermediate */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center" style={{ background: "#3a9ea1" }}>Zwischen</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Zwischenschicht (Z)</p>
                        <p className="text-xs text-muted-foreground">Standard Zwischenschicht</p>
                      </div>
                    </div>
                    {/* Late */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center" style={{ background: "#f69e17" }}>Spät</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Spätschicht (S)</p>
                        <p className="text-xs text-muted-foreground">Standard Spätschicht</p>
                      </div>
                    </div>
                    {/* Night */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center" style={{ background: "#225e62", color: "white" }}>Nacht</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Nachtschicht (N)</p>
                        <p className="text-xs text-muted-foreground">Standard Nachtschicht</p>
                      </div>
                    </div>
                    {/* Management */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center" style={{ background: "oklch(82.1% 0.087 285.6)" }}>Z60</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Leitungsschicht (Z60)</p>
                        <p className="text-xs text-muted-foreground">Exklusive Schicht für Leitungsaufgaben</p>
                      </div>
                    </div>
                    {/* Alternative Shifts Grouped */}
                    <div className="flex items-start gap-3">
                      <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center bg-[#dadada]">F2_</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Alternative Schichten</p>
                        <p className="text-xs text-muted-foreground">F2_, S2_, N5 – zählen nicht zur Mindestbesetzung</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Icons */}
                <div>
                  <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Symbole</h4>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {/* Circle */}
                    {/* Unavailable shift circles */}
                    <div className="flex items-start gap-3">
                      <div className="mt-1 flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#a8d51f" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#3a9ea1" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#f69e17" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#225e62" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#bfbdfb" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#dadada" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#dadada" }} />
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#dadada" }} />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Blockierte Schichten</p>
                        <p className="text-xs text-muted-foreground">
                          Mitarbeiter kann zu dieser Schicht nicht eingeteilt werden
                        </p>
                      </div>
                    </div>
                    {/* Diamond */}
                    <div className="flex items-start gap-3">
                      <div className="mt-1 flex items-center gap-2">
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#a8d51f", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#3a9ea1", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#f69e17", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#225e62", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#bfbdfb", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#dadada", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#dadada", transform: "rotate(45deg)" }}
                        />
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: "#dadada", transform: "rotate(45deg)" }}
                        />

                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Wunschschichten</p>
                        <p className="text-xs text-muted-foreground">
                          Mitarbeiter wünscht sich, diese Schicht nicht zu arbeiten
                        </p>
                      </div>
                    </div>
                    {/* Triangle */}
                    <div className="flex items-start gap-3">
                      <div
                        className="mt-1 w-0 h-0 border-l-[5px] border-r-[5px] border-b-[8px]"
                        style={{
                          borderLeftColor: "transparent",
                          borderRightColor: "transparent",
                          borderBottomColor: "#b77c02",
                        }}
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">Freiwunsch</p>
                        <p className="text-xs text-muted-foreground">
                          Mitarbeiter hat sich diesen Tag frei gewünscht
                        </p>
                      </div>
                    </div>
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
                <h3 className="text-xl font-semibold text-foreground">Keine Lösungen geladen</h3>
                <p className="text-muted-foreground max-w-md">
                  Importieren Sie einen Ordner mit mehreren JSON-Lösungsdateien.
                </p>
              </div>
              <Button onClick={() => document.getElementById("folder-upload")?.click()} className="gap-2">
                <Upload className="h-4 w-4" />
                Ordner importieren
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
