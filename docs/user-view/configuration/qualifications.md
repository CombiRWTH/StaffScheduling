--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Mapping of Qualifications

In our application, qualifications are mapped to specific employee types to ensure proper categorization and management of personnel. This mapping is stored in the file located at `cases/{course_id}/employee_types.json`.

The structure of this JSON file is as follows:

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

In this configuration, each employee type—such as Azubi, Fachkraft, and Hilfskraft—is associated with relevant qualifications.
