import {DomainError} from './base.errors';

export class SolveInfeasibleError extends DomainError {
    constructor() {
        super(
            'Keine zulässige Lösung gefunden (INFEASIBLE)',
            422
        );
    }
}

export class SolveUnknownError extends DomainError {
    constructor() {
        super(
            'Solver-Ergebnis unbekannt (UNKNOWN)',
            422
        );
    }
}
