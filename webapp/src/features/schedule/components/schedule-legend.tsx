'use client';

import {Card} from '@/components/ui/card';

/**
 * Displays a legend explaining the visual indicators used in the schedule table.
 */
export function ScheduleLegend() {
    return (
        <Card className="border-border/50 p-6">
            <h3 className="mb-4 text-sm font-semibold text-foreground">Legende</h3>
            <div className="grid gap-6">
                {/* Background Meaning Section */}
                <div>
                    <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Hintergrundfarben</h4>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="flex items-start gap-3">
                            <div className="mt-1 h-4 w-4 rounded bg-amber-400/20 border border-amber-400/40"/>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Freiwunsch erfüllt</p>
                                <p className="text-xs text-muted-foreground">Mitarbeiter hat gewünschten freien Tag
                                    erhalten</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-1 h-4 w-4 rounded bg-emerald-400/20 border border-emerald-400/40"/>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Schichtwunsch erfüllt</p>
                                <p className="text-xs text-muted-foreground">Unerwünschte Schicht wurde vermieden</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-1 h-4 w-4 rounded bg-muted"/>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Wochenende</p>
                                <p className="text-xs text-muted-foreground">Samstag oder Sonntag</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-1 h-4 w-4 rounded bg-rose-400/10 border border-destructive/40"/>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Blockierter Tag</p>
                                <p className="text-xs text-muted-foreground">Mitarbeiter kann an diesem Tag nicht
                                    eingeteilt werden</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-1 h-4 w-4 rounded bg-rose-400/50 border border-destructive/40"/>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Stundenziel verfehlt</p>
                                <p className="text-xs text-muted-foreground">Mitarbeiter weicht mehr als 7,67 Stunden
                                    von seinen Zielstunden ab</p>
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
                            <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center"
                                 style={{background: "#a8d51f"}}>Früh
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Frühschicht (F)</p>
                                <p className="text-xs text-muted-foreground">Standard Frühschicht</p>
                            </div>
                        </div>
                        {/* Intermediate */}
                        <div className="flex items-start gap-3">
                            <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center"
                                 style={{background: "#3a9ea1"}}>Zwischen
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Zwischenschicht (Z)</p>
                                <p className="text-xs text-muted-foreground">Standard Zwischenschicht</p>
                            </div>
                        </div>
                        {/* Late */}
                        <div className="flex items-start gap-3">
                            <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center"
                                 style={{background: "#f69e17"}}>Spät
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Spätschicht (S)</p>
                                <p className="text-xs text-muted-foreground">Standard Spätschicht</p>
                            </div>
                        </div>
                        {/* Night */}
                        <div className="flex items-start gap-3">
                            <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center"
                                 style={{background: "#225e62", color: "white"}}>Nacht
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Nachtschicht (N)</p>
                                <p className="text-xs text-muted-foreground">Standard Nachtschicht</p>
                            </div>
                        </div>
                        {/* Management */}
                        <div className="flex items-start gap-3">
                            <div className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center"
                                 style={{background: "oklch(82.1% 0.087 285.6)"}}>Z60
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Leitungsschicht (Z60)</p>
                                <p className="text-xs text-muted-foreground">Exklusive Schicht für Leitungsaufgaben</p>
                            </div>
                        </div>
                        {/* Alternative Shifts Grouped */}
                        <div className="flex items-start gap-3">
                            <div
                                className="min-w-[64px] h-6 rounded text-xs flex items-center justify-center bg-[#dadada]">F2_
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Alternative Schichten</p>
                                <p className="text-xs text-muted-foreground">F2_, S2_, N5 - zählen nicht zur
                                    Mindestbesetzung</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Icons */}
                <div>
                    <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Symbole</h4>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {/* Unavailable shift circles */}
                        <div className="flex items-start gap-3">
                            <div className="mt-1 flex items-center gap-1">
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#a8d51f"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#3a9ea1"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#f69e17"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#225e62"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#bfbdfb"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#dadada"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#dadada"}}/>
                                <div className="w-3 h-3 rounded-full" style={{backgroundColor: "#dadada"}}/>
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
                                    style={{backgroundColor: "#a8d51f", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#3a9ea1", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#f69e17", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#225e62", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#bfbdfb", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#dadada", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#dadada", transform: "rotate(45deg)"}}
                                />
                                <div
                                    className="w-3 h-3"
                                    style={{backgroundColor: "#dadada", transform: "rotate(45deg)"}}
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
    );
}
