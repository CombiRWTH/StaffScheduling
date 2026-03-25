# Staff Scheduling Documentation

The Staff Scheduling documentation is organized into two main sections: the [**User View**](./user-view) and the [**Developer View**](./developer-view).

The [User View](./user-view) focuses on practical usage of the automatic staff scheduling system and limits technical depth where possible. The [Developer View](./developer-view) provides the technical background required for contribution and further development.

Both sections are designed to be complementary: user-focused guides can be used as entry points into technical details, and developer-focused guides can be paired with general conceptual material.

## Usage
Automatic staff schedule generation can be explored through the Getting Started guides. Two versions of the application are available: one with database access and one without.

- Without database access: [Getting Started Guide (Light)](./user-view/getting-started-light-version)
- With database access: [Getting Started Guide](./developer-view/getting-started-dev)

## Web Interface

A modern, browser-based frontend for the Staff Scheduling solver is available as a separate project: **[StaffSchedulingWeb](https://julian466.github.io/StaffSchedulingWeb/)**. It offers a full graphical interface for data management, solver control, solution inspection, and TimeOffice integration, with no command-line interaction required. See the [Web Interface documentation](./developer-view/web-interface) for details.

## Getting an Overview
The following guides provide an overview of the codebase and the underlying scheduling problem:

- [Problem Definition](./user-view/problem-definition)
- [Codebase Overview](./developer-view/codebase-overview)
