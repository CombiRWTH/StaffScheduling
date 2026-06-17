from collections.abc import Iterable


def ensure_unique[T](values: Iterable[T], field_name: str) -> frozenset[T]:
    seen: set[T] = set()
    duplicates: set[T] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    if duplicates:
        duplicate_values = ", ".join(sorted(str(value) for value in duplicates))
        raise ValueError(f"Duplicate {field_name} values: {duplicate_values}.")

    return frozenset(seen)
