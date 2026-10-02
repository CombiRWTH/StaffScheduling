# Planning rules

This page explains in plain words which rules a generated schedule keeps and how the application chooses between schedules that keep them. The names in bold are the ones the review shows under **Regelverstöße** and **Technische Details**. The [solver reference](../architecture/solver.md) gives the exact model, and [reasoning and requirements](../validation/reasoning.md) gives the sources.

!!! note "Rules and priorities"

    A **hard rule** is never broken: a schedule that would break one is not offered. A **priority** decides between schedules that keep every hard rule. The independent schedule check tests every hard rule again on the finished schedule, apart from the solver.

## Hard rules

Open an entry for its details.

??? info "Mindestbesetzung: staffing"

    Every shift gets the staff that **Mindestbesetzung** requires for each qualification on that date. If too few employees can work it, the missing places stay open as **Lücken** (gaps) instead of making the whole month fail. A gap is never filled with a placeholder; the review lists it so that guest staff can be requested.

??? info "Zuordnung und Qualifikation: who may work where"

    An employee works only at a station they are a member of on that date, and only with that membership's qualification. Membership at another station is a replacement membership (Ersatz). Jumper pool employees reach the stations this way, and so can station members.

??? info "Ein Dienst pro Tag: one duty per day"

    Nobody gets more than one duty starting on the same date, across all stations.

??? info "Verfügbarkeit: availability"

    Vacation, training, unavailability and free days block every duty touching that date. A night shift the evening before also touches it. "Nur bestimmte Schichten" allows only the listed shifts. Nobody works a night right before an approved vacation or free day.

??? info "Monatskonto: monthly balance"

    Each employee's planned hours plus credited absences end within 7 h 40 min (460 minutes) above or below the monthly target. This holds for employees without any possible duty too, so a month with such an employee has no schedule.

??? info "Arbeitszeit und Pausen: work and breaks"

    A duty has at most 10 hours of work. More than 6 hours need at least 30 minutes of break, and more than 9 hours at least 45 minutes, in parts of at least 15 minutes. Nobody works more than 6 hours without a break. These come from each shift's stored work and break times.

??? info "Durchschnittliche Arbeitszeit: average working time"

    Within the month, an employee works at most 8 hours per working day (Monday to Saturday, not a public holiday). Duties of up to 10 hours are therefore balanced within the same month.

??? info "Ruhezeit: rest"

    At least 11 hours pass between the end of one duty and the start of the next. This includes duties of the neighbouring months.

??? info "Nächte in Folge and Erholung nach Nachtdiensten: nights"

    At most three night duties in a row. After the last night of a run, no duty starts within 48 hours.

??? info "Ersatzruhetag: replacement rest day"

    Whoever works on a Sunday gets a duty-free working day within 13 days before or after it. For a public holiday on a working day, the window is 55 days. The replacement day lies in the same month.

Annual free Sundays (**Freie Sonntage im Jahr**) need the whole year. The check lists them as not assessed; it never reports them as kept.

## Priorities

Among the schedules that keep every hard rule, the solver compares six priorities in this fixed order. They appear in **Technische Details** as **Stufe 1** to **Stufe 6**.

1. **Lücken**: as few open places as possible. A schedule without gaps always wins where one exists.
2. **Gesundheitsereignisse**: as few strain events as possible. Each of these counts as one: six working days in a row, a backward shift change (such as late followed by early, or night followed by late), an isolated workday with free days on both sides, and two worked weekends in a row.
3. **Einsätze anderer Station**: as few duties as possible of station members at another station. The jumper pool covers other stations first. Nobody is moved to another station just to grant a wish.
4. **Wunschkosten (Fairness)**: wishes are granted fairly. Denials are spread over employees: two denied wishes for one person cost more than one for each of two people. Free wishes (free day, free shift) and preferred wishes (preferred day, preferred shift) are counted apart. Every wish counts the same.
5. **Abweichung der Monatskonten**: monthly accounts end as close to their target as possible, inside the hard band.
6. **Überzählige Zwischendienste**: extra intermediate duties beyond the required ones, where they fit.

!!! tip "Why an order instead of weights"

    The solver settles each priority before it looks at the next one. It never accepts one more gap for fewer strain events, and never one more strain event for a granted wish, however large the gain below. Weights would make such trades possible and would need tuning; the order states the priority directly. See ADR 0010 in `docs/adr/` for the decision.

A wish that the inputs rule out is shown as **nicht erfüllbar** and costs nothing. Examples are a preferred shift on a vacation day or at a station without membership. A **nicht erfüllt** wish was possible but was denied in favour of a higher priority or other wishes.

The solver has a time limit. A priority marked _nicht nachgewiesen_ in **Technische Details** may still be improvable; the hard rules hold either way.

## Not part of the planning

These preferences of the earlier reference solver are not modeled:

- **Free days next to weekends.** The problem statement does not ask for it. Penalizing isolated workdays already makes free days cluster.
- **Spreading intermediate duties over the week.** The problem statement's preference is ambiguous. As a hard rule it could make months unsolvable. The last priority still adds intermediate duties where they fit, but in no weekday order.
- **Shorter night runs.** The limit of three nights plus 48 hours of recovery already follows the occupational-health recommendation. Runs of one, two or three nights are not weighed against each other.

Weekend pairs and isolated workdays at a month edge are counted only as far as the neighbouring month's duties are known. [Reasoning and requirements](../validation/reasoning.md#not-modeled) lists these limits.
