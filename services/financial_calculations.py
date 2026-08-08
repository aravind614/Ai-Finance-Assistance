def calculate_growth(
    current: float | None,
    previous: float | None,
) -> float | None:
    """
    Calculate percentage growth.

    Returns None when the required values are unavailable
    or when the previous value is zero.
    """

    if current is None or previous is None:
        return None

    if previous == 0:
        return None

    return ((current - previous) / previous) * 100
