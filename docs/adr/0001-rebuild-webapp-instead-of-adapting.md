# Rebuild the webapp instead of adapting the imported frontend

The imported frontend layered dependency injection, use cases, controllers, repositories and file-based case storage on top of the API, and translated canonical models back into legacy shapes. We rebuilt the webapp as a plain Next.js App Router project: server components read the planning selection from the URL and fetch typed canonical data from the API, and client components only handle interaction. Each area is rebuilt from empty when its slice is implemented; the imported code is a source for look and wording only, not for restoring views or layers.

## Considered Options

- **Adapt the imported views one by one.** Rejected: every view depended on the legacy layers and shapes, so adapting kept both the old and the canonical model alive.
- **Rebuild from scratch, feature by feature.** Chosen: areas that are not rebuilt yet stay visible as greyed sidebar entries without pages.

Update 2026-10-02: the last greyed entries (recurring availability, templates) were removed for good.

## Consequences

Backend routes that existed only to serve legacy shapes were removed with the views; new features add canonical endpoints instead of reviving them.
