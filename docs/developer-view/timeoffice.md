!!! hint
    This section is relevant for users who have access to a version of TimeOffice.

Our application is designed to seamlessly integrate with the TimeOffice platform. It can not only fetch data from a TimeOffice database but also write solutions back into the program.

To streamline this process, we have automated the integration using the "Wand" button in TimeOffice. When configured correctly, this button activates a batch script located at `src/run.bat`, allowing for efficient data handling without the need for manual intervention.

```bash title="src/run.bat"
uv run --env-file .env staff-scheduling delete %3 %1 %2
uv run --env-file .env staff-scheduling fetch %3 %1 %2
uv run --env-file .env staff-scheduling solve %3 %1 %2 --timeout 300
uv run --env-file .env staff-scheduling insert %3 %1 %2
```
