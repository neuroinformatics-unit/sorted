"""Display memory measurements after the allocation tests."""


def pytest_terminal_summary(terminalreporter):
    """Compare estimates with traced peak allocations in MiB, not process RSS."""
    rows = []
    for reports in terminalreporter.stats.values():
        for report in reports:
            if getattr(report, "when", None) != "call":
                continue
            properties = dict(report.user_properties)
            if "estimated_bytes" in properties:
                rows.append((report.nodeid.split("::")[-1], properties))

    if rows:
        terminalreporter.section("Memory estimates vs traced peak allocations (MiB)")
        terminalreporter.write_line(
            f"{'Test case':<75} {'Estimated':>12} {'Measured':>12}"
        )
        for name, properties in rows:
            estimated = properties["estimated_bytes"] / 1024**2
            measured = properties["measured_peak_bytes"] / 1024**2
            terminalreporter.write_line(
                f"{name:<75} {estimated:>12.2f} {measured:>12.2f}"
            )
