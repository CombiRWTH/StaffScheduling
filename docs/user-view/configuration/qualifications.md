# Qualification Mapping in Staff Scheduling

The system uses a JSON configuration file located at:
```
cases/<case_number>/employee_types.json
```

This file maps complex job titles from TimeOffice to three standardized categories. This categories are important for example for the [Minimal-Staff](/user-view/list-of-conditions/#minimum-number-of-staff-per-shift) Constraint which defines how many persons from a personal group are required.

```json
{
  "Azubi": [
    "A-Pflegefachkraft (Krankenpflege) (A-81302-018)",
    "A-Pflegeassistent/in (A-81302-014)"
  ],
  "Fachkraft": [
    "Pflegefachkraft (Krankenpflege) (81302-018)",
    "Gesundheits- und Krankenpfleger/in (81302-005)",
    "Krankenschwester/-pfleger (81302-008)",
    "Altenpfleger/in (82102-002)"
  ],
  "Hilfskraft": [
    "Krankenpflegehelfer/in (1 jährige A.) (81301-006)",
    "Pflegeassistent/in (81302-014)",
    "Helfer/in - stationäre Krankenpflege (81301-002)",
    "Stationshilfe (81301-018)",
    "Bundesfreiwilligendienst (BFD)",
    "Medizinische/r Fachangestellte/r (81102-004)"
  ]
}
```
