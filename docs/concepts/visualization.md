# Visualization of Shift Scheduling (WebApp)

## Overview

This web application visualizes generated shift plans stored as JSON files in the `found_solutions` directory. It uses Flask as the web server and Bootstrap for a clean and responsive interface.

## Starting the Web Server

The WebApp can be started using:

```bash
uv run .\algorithm\WebApp.py
```

By default, the server runs at [http://localhost:5000](http://localhost:5000).

## File Selection

On startup, the application automatically scans the `found_solutions` directory for files with the pattern:

```
solutions_YYYY-MM-DD_HH-MM-SS.json
```

The most recent file is loaded by default.

### File Dropdown

A dropdown menu at the top of the interface allows you to select a specific solution file. Upon selection, the page reloads with the chosen file.

## Selecting a Solution Within a File

Each file can contain multiple solutions. These can be selected using another dropdown next to the file selection.

### Data Display

* The table shows all employees and their assigned shifts per day.
* Shifts are color-coded:

  * Early shift (`F`): red
  * Late shift (`S`): blue
  * Night shift (`N`): green
* Hovering over an employee's name displays the total number of assigned shifts.

## Exporting Data

Download links are provided for the currently selected solution:

* Export as CSV
* Export as Excel file
