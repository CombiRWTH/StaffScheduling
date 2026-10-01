'use client';

import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {ArrowRight, Calendar, Wand2, X} from 'lucide-react';
import {useRouter} from 'next/navigation';
import {WorkflowState} from '@/entities/models/workflow.model';

interface WorkflowBannerProps {
    state: WorkflowState;
}

export function WorkflowBanner({state}: WorkflowBannerProps) {
    const router = useRouter();

    if (!state.isWorkflowMode || !state.caseId || !state.startDate || !state.endDate) {
        return null;
    }

    const handleBackToWorkflow = () => {
        router.push('/workflow');
    };

    const handleExitWorkflow = () => {
        // Hard Browser reload to ensure all workflow-related UI is reset, including any client-side state
        window.location.href = '/api/workflow/stop';
    };

    const formatDate = (dateStr: string): string => {
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[0]}.${parts[1]}.${parts[2]}`;
        }
        return dateStr;
    };

    return (
        <Alert className="mb-4 border-blue-200 bg-blue-50 relative">
            <Wand2 className="h-5 w-5 text-blue-600"/>
            <AlertTitle className="text-blue-900 flex items-center gap-2">
                Workflow-Modus aktiv
                <Badge variant="secondary" className="ml-2">
                    Case {state.caseId}
                </Badge>
            </AlertTitle>
            <AlertDescription className="text-blue-800 mt-2">
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4"/>
                            <span className="font-medium">Von:</span>
                            <span>{formatDate(state.startDate)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4"/>
                            <span className="font-medium">Bis:</span>
                            <span>{formatDate(state.endDate)}</span>
                        </div>
                    </div>
                    <div className="flex gap-2 mt-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleBackToWorkflow}
                            className="bg-white"
                        >
                            <ArrowRight className="h-4 w-4 mr-2"/>
                            Zurück zum Workflow
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleExitWorkflow}
                            className="text-blue-900"
                        >
                            <X className="h-4 w-4 mr-2"/>
                            Info: Modus beenden
                        </Button>
                    </div>
                </div>
            </AlertDescription>
        </Alert>
    );
}
