import xml.etree.ElementTree as ET
import sys
from datetime import datetime
import configparser
import re


def get_minimum_coverage_from_tox():
    """Extract minimum coverage requirement from tox.ini pytest addopts."""
    try:
        config = configparser.ConfigParser()
        config.read("tox.ini")

        # Look for coverage threshold in different possible locations
        locations = [
            ("testenv", "pytest_addopts"),
            ("pytest", "addopts"),
            ("tool:pytest", "addopts"),
        ]

        for section, key in locations:
            if section in config and key in config[section]:
                match = re.search(r"--cov-fail-under[= ](\d+)", config[section][key])
                if match:
                    return int(match.group(1))

        # Fallback to default if not found
        print(
            "Warning: Could not find --cov-fail-under in tox.ini, using default value of 50"
        )
        return 50

    except Exception as e:
        print(f"Warning: Error reading tox.ini: {e}, using default value of 50")
        return 50


def generate_coverage_badge(coverage_percentage):
    """Generate a coverage badge in markdown format."""
    if coverage_percentage >= 90:
        color = "brightgreen"
    elif coverage_percentage >= 75:
        color = "green"
    elif coverage_percentage >= 50:
        color = "yellow"
    else:
        color = "red"

    return f"![Code Coverage](https://img.shields.io/badge/coverage-{coverage_percentage:.1f}%25-{color})"


def parse_coverage_file(coverage_file="coverage.xml"):
    """Parse coverage.xml and return detailed metrics."""
    tree = ET.parse(coverage_file)
    root = tree.getroot()

    # Get overall coverage
    line_rate = float(root.attrib["line-rate"]) * 100

    # Collect package metrics
    packages = []
    for package in root.findall(".//package"):
        package_name = package.attrib["name"]
        package_line_rate = float(package.attrib["line-rate"]) * 100
        packages.append((package_name, package_line_rate))

    return line_rate, packages


def generate_markdown_report(coverage_percentage, package_metrics, minimum_coverage):
    """Generate a formatted markdown report."""
    report = []

    # Add header with badge
    report.append("# Code Coverage Report")
    report.append(f"\n{generate_coverage_badge(coverage_percentage)}")

    # Add summary section
    report.append("\n## Summary")
    report.append(f"- **Overall Coverage**: {coverage_percentage:.1f}%")
    report.append(f"- **Minimum Required**: {minimum_coverage}%")
    report.append(
        f"- **Status**: {'✅ PASSED' if coverage_percentage >= minimum_coverage else '❌ FAILED'}"
    )

    # Add timestamp
    report.append(
        f"\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
    )

    # Add package details
    if package_metrics:
        report.append("\n## Package Details")
        report.append("\n| Package | Coverage |")
        report.append("|---------|-----------|")
        for package_name, package_coverage in sorted(
            package_metrics, key=lambda x: x[1], reverse=True
        ):
            status_emoji = "🟢" if package_coverage >= minimum_coverage else "🔴"
            report.append(
                f"| {package_name} | {status_emoji} {package_coverage:.1f}% |"
            )

    return "\n".join(report)


def main():
    try:
        # Get minimum coverage from tox.ini
        minimum_coverage = get_minimum_coverage_from_tox()

        overall_coverage, package_metrics = parse_coverage_file()
        report = generate_markdown_report(
            overall_coverage, package_metrics, minimum_coverage
        )

        # Write report to file
        with open("coverage_report.md", "w") as f:
            f.write(report)

        # Exit with error if coverage is below minimum
        if overall_coverage < minimum_coverage:
            print(
                f"\n❌ Coverage {overall_coverage:.2f}% is below minimum {minimum_coverage}%"
            )
            sys.exit(1)

        print("\n✅ Coverage check passed!")

    except Exception as e:
        print(f"Error processing coverage report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
