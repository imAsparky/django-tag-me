import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChangelogEntry:
    """
    Represents a single entry in the changelog.

    Attributes:
        type: The type of change (e.g., 'feat', 'fix', 'docs').
        scope: The scope of the change (e.g., 'ui', 'api', 'core').
        description: A brief description of the change.
        pr: The pull request number associated with the change.
        docs_hint: An optional hint about documentation updates.
        author: The author of the change (optional).
        commit_hash: The commit hash of the change (optional).
        breaking: Indicates if the change is a breaking change.

    Methods:
        format: Returns a formatted string representation of the entry.
    """

    type: str
    scope: str
    description: str
    pr: str
    docs_hint: str = ""
    author: str = ""
    commit_hash: str = ""
    breaking: bool = False

    def format(self) -> str:
        """\
        Formats the changelog entry as a Markdown string.

        Returns:
            str: The formatted entry.
        """
        repo = os.getenv("GITHUB_REPOSITORY", "")
        entry = f"- {'BREAKING: ' if self.breaking else ''}{self.description} ({self.scope}) [#{self.pr}](https://github.com/{repo}/pull/{self.pr})"
        if self.author:
            entry += f" by @{self.author}"
        if self.commit_hash:
            entry += f" ([{self.commit_hash}](https://github.com/{repo}/commit/{self.commit_hash}))"
        if self.docs_hint:
            entry += f"\n  > {self.docs_hint}"
        return entry


class ChangelogUpdater:
    """\
    Updates the CHANGELOG.md file with entries from pull request commits.

    This class retrieves commit messages from a GitHub pull request, parses them
    to extract changelog entries, and updates the CHANGELOG.md file with the new entries.
    """

    CHANGE_TYPES = {
        "chore": "Maintenance",
        "docs": "Documentation",
        "feat": "Features",
        "fix": "Bug Fixes",
        "perf": "Performance",
        "refactor": "Code Refactoring",
        "style": "Formatting, missing semi colons, etc; no code change",
        "test": "Testing",
    }

    def __init__(self):
        """
        Initializes the ChangelogUpdater with GitHub client and PR data.
        """
        self.gh = self._get_github_client()
        self.repo_name, self.pr_number = self._get_pr_data()
        self.repo = self.gh.get_repo(self.repo_name)
        self.changes_made = False
        self.current_version = None

        # Define paths
        self.changelog_path = Path("CHANGELOG.md")
        self.readme_path = Path("README.rst")
        self.project_path = Path("pyproject.toml")
        self.package_path = Path("tag_me/__init__.py")
        self.version_path = Path("version.toml")

        # Verify required files exist
        if not self.changelog_path.exists():
            raise FileNotFoundError("CHANGELOG.md not found")
        if not self.project_path.exists():
            raise FileNotFoundError("pyproject.toml not found")
        if not self.version_path.exists():
            raise FileNotFoundError("version.toml not found")

    @staticmethod
    def _get_github_client() -> Github:
        """\
        Creates a GitHub client using the GITHUB_TOKEN environment variable.

        Returns:
            Github: The authenticated GitHub client.

        Raises:
            ValueError: If GITHUB_TOKEN is not found.
        """
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN not found")
        return Github(token)

    @staticmethod
    def _get_pr_data() -> Tuple[str, int]:
        """\
        Retrieves pull request data from the GitHub event file.

        Returns:
            tuple: A tuple containing the repository name and pull request number.

        Raises:
            ValueError: If GITHUB_EVENT_PATH is not found or if there is an error parsing the event file.
        """
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if not event_path:
            raise ValueError("GITHUB_EVENT_PATH not found")

        try:
            with open(event_path) as f:
                event = json.load(f)
            return (os.getenv("GITHUB_REPOSITORY", ""), event["pull_request"]["number"])
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Error parsing event file: {e}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _get_pr_commits(self) -> List[str]:
        """\
        Retrieves the commit messages from the pull request.

        This method uses the `transient retry` decorator to handle potential 
        transient errors from the GitHub API, such as rate limit issues. 
        It will retry the request up to 3 times with exponential backoff.

        Returns:
            list: A list of commit messages.

        Raises:
            ValueError: If no commits are found in the pull request.
            GithubException: If there is an error communicating with the GitHub API.
        """
        try:
            pr = self.repo.get_pull(self.pr_number)
            commits = list(pr.get_commits())
            if not commits:
                raise ValueError("No commits found in PR")
            return [commit.commit.message for commit in commits]
        except GithubException as e:
            if e.status == 403:  # Rate limit exceeded
                logger.error("GitHub API rate limit exceeded")
                raise
            logger.exception("GitHub API error:")
            raise

    def _parse_commit_message(self, message: str) -> Optional[ChangelogEntry]:
        """\
        Parses a commit message to extract changelog entry information.

        Args:
            message: The commit message.

        Returns:
            ChangelogEntry: The parsed changelog entry, or None if the message is not in the expected format.
        """
        parts = message.strip().split("\n\n", 1)
        title = parts[0]
        body = parts[1] if len(parts) > 1 else ""

        # Log the commit being processed
        logger.info(f"Processing commit message: {title}")

        # title_pattern = r"^(?:BREAKING\s+)?(?P<type>\w+)\((?P<scope>[\w-]+)\):\s+(?P<description>.+?)\s+#(?P<pr>\d+)(?:\s+@(?P<author>\S+))?\s*(?:\[(?P<commit_hash>\w+)\])?$"
        # Allows for 0-3 spaces after the colon.
        title_pattern = r"^(?:BREAKING\s+)?(?P<type>\w+)\((?P<scope>[\w-]+)\):\s{0,3}(?P<description>.+?)\s+#(?P<pr>\d+)(?:\s+@(?P<author>\S+))?\s*(?:\[(?P<commit_hash>\w+)\])?$"
        title_match = re.match(title_pattern, title.strip())

        if not title_match:
            logger.info(f"Commit message does not match expected format: {title}")
            return None

        commit_type = title_match.group("type")
        if commit_type not in self.CHANGE_TYPES:
            logger.info(f"Commit type '{commit_type}' not in CHANGE_TYPES, skipping")
            return None

        logger.info(
            f"Valid commit found - Type: {commit_type}, Scope: {title_match.group('scope')}"
        )

        docs_hint = ""
        if body:
            docs_pattern = r'\[ui-docs\]:\s*"""(.*?)"""'
            docs_match = re.search(docs_pattern, body, re.DOTALL)
            if docs_match:
                docs_hint = docs_match.group(1).strip()

        return ChangelogEntry(
            type=commit_type,
            scope=title_match.group("scope"),
            description=title_match.group("description"),
            pr=title_match.group("pr"),
            docs_hint=docs_hint,
            author=title_match.group("author") or "",
            commit_hash=title_match.group("commit_hash") or "",
            breaking="BREAKING" in title,
        )

    def _get_latest_version(self, content: str) -> Tuple[str, int]:
        """\
        Extracts the latest version number from the changelog content.

        Args:
            content: The content of the CHANGELOG.md file.

        Returns:
            tuple: A tuple containing the latest version date and increment number.
        """
        pattern = r"\[(\d{4}\.\d{2}\.\d{2})\.(\d+)\]"
        matches = re.findall(pattern, content)
        today = datetime.now().strftime("%Y.%m.%d")

        if not matches:
            return today, 1

        # Sort matches to ensure the latest version is used
        matches.sort(key=lambda x: (x[0], int(x[1])), reverse=True)
        latest_date, latest_increment = matches[0]
        if latest_date == today:
            return today, int(latest_increment) + 1
        return today, 1

    def _get_updated_package(self, version: str) -> str:
        """\
        Find and update the package version number.

        Returns:
            string: Formatted package file string.
        """

        try:
            content = self.package_path.read_text().splitlines()
            # Find and replace the version line
            for i, line in enumerate(content):
                if line.startswith('__version__ = "'):
                    content[i] = f'__version__ = "{version}"'
                    break

            return "\n".join(content)
        except Exception:
            logger.exception("Failed to update pyproject.toml version")
            raise

    def _get_updated_pyproject(self, version: str) -> str:
        """\
        Find and update the pyproject version number.

        Returns:
            string: Formatted pyproject file string.
        """

        try:
            content = self.project_path.read_text().splitlines()
            # Find and replace the version line
            for i, line in enumerate(content):
                if line.startswith('version = "'):
                    content[i] = f'version = "{version}"'
                    break

            return "\n".join(content)
        except Exception:
            logger.exception("Failed to update pyproject.toml version")
            raise

    def _get_updated_readme(self, version: str) -> str:
        """\
        Find and update the README version number.

        Returns:
            string: Formatted README file string.
        """

        try:
            content = self.readme_path.read_text().splitlines()
            # Find and replace the version line
            for i, line in enumerate(content):
                if line.startswith("**Version ="):
                    content[i] = f"**Version = {version}**"
                    break

            return "\n".join(content)
        except Exception:
            logger.exception("Failed to update README.rst version")
            raise

    def update_changelog(self) -> bool:
        """
        Updates both CHANGELOG.md and pyproject.toml with new version information.
        """
        try:
            commits = self._get_pr_commits()
            logger.info(f"Found {len(commits)} commits to process")
        except Exception:
            logger.exception("Failed to get commits:")
            raise

        # Read current changelog
        content = self.changelog_path.read_text()

        version_date, increment = self._get_latest_version(content)
        version = f"{version_date}.{increment}"
        self.current_version = version
        logger.info(f"Using version: {version}")

        grouped_changes: Dict[str, List[str]] = {k: [] for k in self.CHANGE_TYPES}
        breaking_changes: List[str] = []

        for commit in commits:
            entry = self._parse_commit_message(commit)
            if entry and entry.type in self.CHANGE_TYPES:
                self.changes_made = True
                formatted_entry = entry.format()
                if entry.breaking:
                    breaking_changes.append(formatted_entry)
                grouped_changes[entry.type].append(formatted_entry)

        if not self.changes_made:
            logger.info("No changes needed in changelog")
            return False

        # Build new version section
        new_version = f"\n## [{version}]\n"

        if breaking_changes:
            new_version += "\n### ⚠ BREAKING CHANGES\n"
            new_version += "\n".join(sorted(breaking_changes)) + "\n"

        for category, title in self.CHANGE_TYPES.items():
            items = grouped_changes[category]
            if items:
                new_version += f"\n### {title}\n"
                new_version += "\n".join(sorted(items)) + "\n"

        updated_content = content.replace(
            "<!--next-version-placeholder-->",
            f"<!--next-version-placeholder-->\n{new_version}",
        )

        version_data = f'[tb.version]\n__version__ = "{version.strip()}"\n'

        if self.changes_made:
            try:
                # Update both files atomically
                self.changelog_path.write_text(updated_content)
                self.package_path.write_text(
                    self._get_updated_package(version=version)
                )  # update __init__.py
                self.project_path.write_text(
                    self._get_updated_pyproject(version=version)
                )
                self.readme_path.write_text(self._get_updated_readme(version=version))
                self.version_path.write_text(version_data)

                logger.info(
                    f"Successfully updated CHANGELOG.md, README.rst, pyproject.toml and version.toml to version {version}"
                )
                return True

            except Exception:
                logger.exception("Error updating files:")
                sys.exit(1)

        return False


if __name__ == "__main__":
    try:
        updater = ChangelogUpdater()
        changes_made = updater.update_changelog()
        sys.exit(0 if changes_made else 2)  # Exit 2 indicates no changes needed
    except Exception:
        logger.exception("Changelog update failed:")
        sys.exit(1)
