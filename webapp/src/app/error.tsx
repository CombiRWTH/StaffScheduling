'use client';

import {useEffect} from 'react';
import {Button} from '@/components/ui/button';

export default function Error({
                                  error,
                                  reset,
                              }: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error(error);
    }, [error]);

    return (
        <div className="flex flex-col items-center justify-center gap-4 py-20">
            <h2 className="text-2xl font-bold">Etwas ist schiefgelaufen!</h2>
            <p className="text-muted-foreground">
                Ein unerwarteter Fehler ist aufgetreten.
            </p>
            <Button onClick={() => reset()}>Erneut versuchen</Button>
        </div>
    );
}
