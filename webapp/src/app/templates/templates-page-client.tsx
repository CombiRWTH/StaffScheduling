'use client';

import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {ArrowRight, CalendarCheck, FileText, Heart, Scale, UserCog} from 'lucide-react';
import Link from 'next/link';

interface TemplatesPageClientProps {
    caseId: number;
    monthYear: string;
}

export function TemplatesPageClient({caseId, monthYear}: TemplatesPageClientProps) {
    const searchStr = `?caseId=${caseId}&monthYear=${monthYear}`;

    const templateTypes = [
        {
            type: 'weights',
            title: 'Gewichtungs-Templates',
            description: 'Verwalten Sie gespeicherte Solver-Gewichtungskonfigurationen',
            icon: Scale,
            href: `/templates/weights${searchStr}`,
            available: true,
        },
        {
            type: 'global-wishes',
            title: 'Globale Wünsche-Templates',
            description: 'Wiederverwendbare globale Wunsch- und Blockierungskonfigurationen mit intelligentem Mitarbeiter-Matching',
            icon: Heart,
            href: `/templates/global-wishes${searchStr}`,
            available: true,
        },
        {
            type: 'minimal-staff',
            title: 'Mindestbesetzungs-Templates',
            description: 'Wiederverwendbare Mindestbesetzungskonfigurationen pro Kategorie, Wochentag und Schicht',
            icon: UserCog,
            href: `/templates/minimal-staff${searchStr}`,
            available: true,
        },
        {
            type: 'availability',
            title: 'Availability-Templates',
            description: 'Wiederverwendbare globale Availability-Konfigurationen',
            icon: CalendarCheck,
            href: `/templates/availability${searchStr}`,
            available: true,
        },
    ];

    return (
        <div className="py-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Template-Verwaltung</h1>
                <p className="text-muted-foreground">
                    Verwalten Sie wiederverwendbare Konfigurationen für verschiedene Bereiche des Systems.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                {templateTypes.map((template) => {
                    const Icon = template.icon;
                    return (
                        <Card
                            key={template.type}
                            className={template.available ? 'hover:bg-accent/5 transition-colors' : 'opacity-60'}
                        >
                            <CardHeader>
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2 bg-primary/10 rounded-lg">
                                        <Icon className="h-6 w-6 text-primary"/>
                                    </div>
                                    <CardTitle>{template.title}</CardTitle>
                                </div>
                                <CardDescription>{template.description}</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {template.available ? (
                                    <Link href={template.href}>
                                        <Button className="w-full">
                                            Templates verwalten
                                            <ArrowRight className="ml-2 h-4 w-4"/>
                                        </Button>
                                    </Link>
                                ) : (
                                    <Button className="w-full" disabled>
                                        Bald verfügbar
                                    </Button>
                                )}
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            <Card className="bg-muted/50">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-muted-foreground"/>
                        <CardTitle className="text-lg">Was sind Templates?</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                    <p>
                        Templates ermöglichen es Ihnen, häufig verwendete Konfigurationen zu speichern und
                        wiederzuverwenden. Dies spart Zeit und stellt Konsistenz sicher.
                    </p>
                    <div className="space-y-2">
                        <div className="flex items-start gap-2">
                            <div className="mt-0.5">✓</div>
                            <div>
                                <strong className="text-foreground">Speichern:</strong> Aktuelle Konfiguration als
                                Template speichern
                            </div>
                        </div>
                        <div className="flex items-start gap-2">
                            <div className="mt-0.5">✓</div>
                            <div>
                                <strong className="text-foreground">Laden:</strong> Gespeicherte Templates schnell
                                anwenden
                            </div>
                        </div>
                        <div className="flex items-start gap-2">
                            <div className="mt-0.5">✓</div>
                            <div>
                                <strong className="text-foreground">Verwalten:</strong> Beschreibungen bearbeiten
                                und Templates organisieren
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
