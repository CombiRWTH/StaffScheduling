import Link from 'next/link';
import {Button} from '@/components/ui/button';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center gap-4 py-20">
            <h2 className="text-2xl font-bold">Seite nicht gefunden</h2>
            <p className="text-muted-foreground">
                Die angeforderte Seite konnte nicht gefunden werden.
            </p>
            <Button asChild>
                <Link href="/">Zurück zur Startseite</Link>
            </Button>
        </div>
    );
}
