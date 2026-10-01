'use client';

import Link from 'next/link';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {
    ArrowRight,
    Calendar,
    // CalendarRangeIcon,
    ClockFading,
    Users,
    Wand2,
} from 'lucide-react';

interface HomePageClientProps {
    caseSearch: string;
    isWorkflowMode: boolean;
}

export function HomePageClient({caseSearch, isWorkflowMode}: HomePageClientProps) {

    const databases = [
        {
            title: 'Mitarbeiter',
            description: 'Verwalte alle Mitarbeiter und ihre Informationen',
            icon: Users,
            href: `/employees${caseSearch}`,
            color: 'text-blue-500',
            bgColor: 'bg-blue-50',
        },
        // {
        //     title: 'Globale Wünsche & Blockierungen',
        //     description: 'Verwalte allgemeine Wünsche und Blockierungen für alle Mitarbeiter',
        //     icon: CalendarRangeIcon,
        //     href: `/global-wishes-and-blocked${caseSearch}`,
        //     color: 'text-indigo-500',
        //     bgColor: 'bg-indigo-50',
        // },
        {
            title: 'Wünsche & Blockierungen',
            description: 'Verwalte Mitarbeiterwünsche und Blockierungen',
            icon: Calendar,
            href: `/wishes-and-blocked${caseSearch}`,
            color: 'text-purple-500',
            bgColor: 'bg-purple-50',
        },
        {
            title: 'Dienstplan',
            description: 'Analysiere und visualisiere Mitarbeiter-Schichtpläne',
            icon: ClockFading,
            href: `/schedule${caseSearch}`,
            color: 'text-green-500',
            bgColor: 'bg-green-50',
        },
    ];

    return (
        <div className="py-10">
            <div className="mb-6">
                <h1 className="text-4xl font-bold mb-2">Schichtplan Datenbank Manager</h1>
                <p className="text-muted-foreground text-lg">
                    Zentrale Verwaltung aller Datenbanken für die Schichtplanung
                </p>
            </div>

            {!isWorkflowMode && (
                <Alert className="mb-6 border-blue-200 bg-blue-50">
                    <Wand2 className="h-5 w-5 text-blue-600"/>
                    <AlertTitle className="text-blue-900">TimeOffice Integration</AlertTitle>
                    <AlertDescription className="text-blue-800">
                        Wenn Sie diese Anwendung über den Zauberstab-Button in TimeOffice starten,
                        werden Sie automatisch zum strukturierten Workflow weitergeleitet,
                        wo Sie Schritt für Schritt Ihren Dienstplan erstellen können.
                    </AlertDescription>
                </Alert>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {databases.map((db) => {
                    const Icon = db.icon;
                    return (
                        <Link key={db.href} href={db.href}>
                            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className={`p-3 rounded-lg ${db.bgColor}`}>
                                            <Icon className={`h-6 w-6 ${db.color}`}/>
                                        </div>
                                        <ArrowRight className="h-5 w-5 text-muted-foreground"/>
                                    </div>
                                    <CardTitle className="mt-4">{db.title}</CardTitle>
                                    <CardDescription>{db.description}</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <Button variant="outline" className="w-full">
                                        Verwalten
                                    </Button>
                                </CardContent>
                            </Card>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}
