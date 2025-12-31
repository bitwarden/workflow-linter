"""Tests src/bitwarden_workflow_linter/actions.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.bitwarden_workflow_linter.actions import ActionsCmd
from src.bitwarden_workflow_linter.utils import Action, Settings


@pytest.fixture(name="mock_settings")
def fixture_mock_settings():
    """Create a mock Settings object with minimal approved actions."""
    settings = Settings()
    settings.approved_actions = {
        "actions/checkout": Action(
            name="actions/checkout",
            version="v4.2.2",
            sha="11bd71901bbe5b1630ceea73d27597364c9af683",
        ),
        "docker/build-push-action": Action(
            name="docker/build-push-action",
            version="v6.12.0",
            sha="67a2d409c0a876cbe6b11854e3e25193efe4e62d",
        ),
        "oxsecurity/megalinter/flavors/dotnetweb": Action(
            name="oxsecurity/megalinter/flavors/dotnetweb",
            version="v9.2.0",
            sha="55a59b24a441e0e1943080d4a512d827710d4a9d",
        ),
    }
    return settings


@pytest.fixture(name="mock_github_api_response")
def fixture_mock_github_api_response():
    """Create a mock GitHub API response."""

    def create_response(status, data):
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.data = json.dumps(data).encode()
        return mock_response

    return create_response


class TestActionsAdd:
    """Tests for the ActionsCmd.add method."""

    def test_add_action_two_segments(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test adding an action with 2 path segments (owner/repo)."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        # Mock API responses for a 2-segment action
        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock exists check (repo check)
            # Mock get_latest_version (release check)
            # Mock get_latest_version (tag ref check)
            mock_api.side_effect = [
                mock_github_api_response(200, {}),  # exists check
                mock_github_api_response(200, {"tag_name": "v1.0.0"}),  # release check
                mock_github_api_response(
                    200, {"object": {"type": "commit", "sha": "abc123"}}
                ),  # tag ref
            ]

            result = actions_cmd.add("actions/setup-node", str(output_file))

            assert result == 0
            assert output_file.exists()

            # Verify the action was added with full path
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert "actions/setup-node" in actions
                assert actions["actions/setup-node"]["name"] == "actions/setup-node"
                assert actions["actions/setup-node"]["version"] == "v1.0.0"
                assert actions["actions/setup-node"]["sha"] == "abc123"

    def test_add_action_multiple_segments(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test adding an action with >2 path segments (owner/repo/path/to/action)."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        # Mock API responses for a multi-segment action
        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # All API calls should use owner/repo (first 2 segments)
            mock_api.side_effect = [
                mock_github_api_response(200, {}),  # exists check for owner/repo
                mock_github_api_response(
                    200, {"tag_name": "v2.5.0"}
                ),  # release check for owner/repo
                mock_github_api_response(
                    200, {"object": {"type": "commit", "sha": "def456"}}
                ),  # tag ref
            ]

            result = actions_cmd.add(
                "oxsecurity/megalinter/flavors/javascript", str(output_file)
            )

            assert result == 0
            assert output_file.exists()

            # Verify the action was added with FULL path, not truncated
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert "oxsecurity/megalinter/flavors/javascript" in actions
                assert (
                    actions["oxsecurity/megalinter/flavors/javascript"]["name"]
                    == "oxsecurity/megalinter/flavors/javascript"
                )
                assert (
                    actions["oxsecurity/megalinter/flavors/javascript"]["version"]
                    == "v2.5.0"
                )
                assert (
                    actions["oxsecurity/megalinter/flavors/javascript"]["sha"]
                    == "def456"
                )

    def test_add_action_annotated_tag(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test adding an action with an annotated tag."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock annotated tag response (requires following URL)
            mock_api.side_effect = [
                mock_github_api_response(200, {}),  # exists check
                mock_github_api_response(200, {"tag_name": "v1.5.0"}),  # release check
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "tag",
                            "url": (
                                "https://api.github.com/repos/test/action"
                                "/git/tags/abc"
                            ),
                        }
                    },
                ),  # tag ref (annotated)
                mock_github_api_response(
                    200, {"object": {"sha": "ghi789"}}
                ),  # follow URL
            ]

            result = actions_cmd.add("test/action", str(output_file))

            assert result == 0
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert actions["test/action"]["sha"] == "ghi789"

    def test_add_action_not_found(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test adding an action that doesn't exist."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            mock_api.return_value = mock_github_api_response(404, {})

            result = actions_cmd.add("nonexistent/action", str(output_file))

            assert result == 0  # Still returns 0 but doesn't add the action
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert "nonexistent/action" not in actions

    def test_add_action_no_release_uses_tags(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test adding an action that has no releases, falls back to tags."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            mock_api.side_effect = [
                mock_github_api_response(200, {}),  # exists check
                mock_github_api_response(404, {}),  # no releases
                mock_github_api_response(
                    200,
                    [
                        {
                            "name": "v1.2.3",
                            "commit": {"sha": "xyz987"},
                        }
                    ],
                ),  # tags endpoint
            ]

            result = actions_cmd.add("test/no-releases", str(output_file))

            assert result == 0
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert actions["test/no-releases"]["version"] == "v1.2.3"
                assert actions["test/no-releases"]["sha"] == "xyz987"


class TestActionsUpdate:
    """Tests for the ActionsCmd.update method."""

    def test_update_two_segment_actions(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test updating actions with 2 path segments."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock responses for actions/checkout (unchanged)
            # Mock responses for docker/build-push-action (updated)
            mock_api.side_effect = [
                # actions/checkout (no update)
                mock_github_api_response(200, {}),  # exists
                mock_github_api_response(200, {"tag_name": "v4.2.2"}),  # release
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
                        }
                    },
                ),  # tag ref
                # docker/build-push-action (updated)
                mock_github_api_response(200, {}),  # exists
                mock_github_api_response(200, {"tag_name": "v6.13.0"}),  # release
                mock_github_api_response(
                    200, {"object": {"type": "commit", "sha": "newsha123"}}
                ),  # tag ref
                # oxsecurity (multi-segment)
                mock_github_api_response(200, {}),  # exists
                mock_github_api_response(200, {"tag_name": "v9.2.0"}),  # release
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "55a59b24a441e0e1943080d4a512d827710d4a9d",
                        }
                    },
                ),  # tag ref
            ]

            result = actions_cmd.update(str(output_file))

            assert result == 0
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)

                # Verify actions/checkout unchanged
                assert actions["actions/checkout"]["version"] == "v4.2.2"
                assert (
                    actions["actions/checkout"]["sha"]
                    == "11bd71901bbe5b1630ceea73d27597364c9af683"
                )

                # Verify docker/build-push-action updated
                assert actions["docker/build-push-action"]["version"] == "v6.13.0"
                assert actions["docker/build-push-action"]["sha"] == "newsha123"

    def test_update_multi_segment_actions(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test updating actions with >2 path segments."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # We have 3 actions, need responses for all
            mock_api.side_effect = [
                # actions/checkout
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v4.2.2"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
                        }
                    },
                ),
                # docker/build-push-action
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v6.12.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "67a2d409c0a876cbe6b11854e3e25193efe4e62d",
                        }
                    },
                ),
                # oxsecurity/megalinter/flavors/dotnetweb (updated)
                mock_github_api_response(
                    200, {}
                ),  # exists check for oxsecurity/megalinter
                mock_github_api_response(200, {"tag_name": "v9.3.0"}),  # new version
                mock_github_api_response(
                    200, {"object": {"type": "commit", "sha": "updatedsha999"}}
                ),
            ]

            result = actions_cmd.update(str(output_file))

            assert result == 0
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)

                # Verify multi-segment action preserved full path and updated
                assert "oxsecurity/megalinter/flavors/dotnetweb" in actions
                assert (
                    actions["oxsecurity/megalinter/flavors/dotnetweb"]["name"]
                    == "oxsecurity/megalinter/flavors/dotnetweb"
                )
                assert (
                    actions["oxsecurity/megalinter/flavors/dotnetweb"]["version"]
                    == "v9.3.0"
                )
                assert (
                    actions["oxsecurity/megalinter/flavors/dotnetweb"]["sha"]
                    == "updatedsha999"
                )

    def test_update_preserves_all_actions(
        self, mock_settings, mock_github_api_response, tmp_path
    ):
        """Test that update preserves all actions in the list."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock responses for all 3 actions
            mock_api.side_effect = [
                # actions/checkout
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v4.2.2"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
                        }
                    },
                ),
                # docker/build-push-action
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v6.12.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "67a2d409c0a876cbe6b11854e3e25193efe4e62d",
                        }
                    },
                ),
                # oxsecurity/megalinter/flavors/dotnetweb
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v9.2.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "55a59b24a441e0e1943080d4a512d827710d4a9d",
                        }
                    },
                ),
            ]

            result = actions_cmd.update(str(output_file))

            assert result == 0
            with open(output_file, encoding="utf-8") as f:
                actions = json.load(f)
                assert len(actions) == 3
                assert "actions/checkout" in actions
                assert "docker/build-push-action" in actions
                assert "oxsecurity/megalinter/flavors/dotnetweb" in actions

    def test_update_multi_segment_unchanged_shows_ok(
        self, mock_settings, mock_github_api_response, tmp_path, capsys
    ):
        """Test that multi-segment actions show 'ok' when unchanged, not 'changed'."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock responses: multi-segment action with IDENTICAL version/sha
            mock_api.side_effect = [
                # actions/checkout (unchanged)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v4.2.2"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
                        }
                    },
                ),
                # docker/build-push-action (unchanged)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v6.12.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "67a2d409c0a876cbe6b11854e3e25193efe4e62d",
                        }
                    },
                ),
                # oxsecurity/megalinter/flavors/dotnetweb (UNCHANGED - same version/sha)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v9.2.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "55a59b24a441e0e1943080d4a512d827710d4a9d",
                        }
                    },
                ),
            ]

            result = actions_cmd.update(str(output_file))
            captured = capsys.readouterr()

            assert result == 0

            # Verify the multi-segment action shows as 'ok', not 'changed'
            # This is the bug test: with the current bug, this would show 'changed'
            assert "oxsecurity/megalinter/flavors/dotnetweb" in captured.out
            assert "ok" in captured.out.lower()

            # Should NOT show 'changed' for this action since version/sha are identical
            lines = captured.out.split("\n")
            megalinter_line = [
                line
                for line in lines
                if "oxsecurity/megalinter/flavors/dotnetweb" in line
            ][0]
            assert "changed" not in megalinter_line.lower()

    def test_update_multi_segment_changed_shows_changed(
        self, mock_settings, mock_github_api_response, tmp_path, capsys
    ):
        """Test that multi-segment actions show 'changed' when actually updated."""
        actions_cmd = ActionsCmd(settings=mock_settings)
        output_file = tmp_path / "actions.json"

        with patch.object(actions_cmd, "get_github_api_response") as mock_api:
            # Mock responses: multi-segment action with DIFFERENT version/sha
            mock_api.side_effect = [
                # actions/checkout (unchanged)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v4.2.2"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
                        }
                    },
                ),
                # docker/build-push-action (unchanged)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v6.12.0"}),
                mock_github_api_response(
                    200,
                    {
                        "object": {
                            "type": "commit",
                            "sha": "67a2d409c0a876cbe6b11854e3e25193efe4e62d",
                        }
                    },
                ),
                # oxsecurity/megalinter/flavors/dotnetweb (CHANGED - new version/sha)
                mock_github_api_response(200, {}),
                mock_github_api_response(200, {"tag_name": "v10.0.0"}),
                mock_github_api_response(
                    200, {"object": {"type": "commit", "sha": "newsha12345"}}
                ),
            ]

            result = actions_cmd.update(str(output_file))
            captured = capsys.readouterr()

            assert result == 0

            # Verify the multi-segment action shows as 'changed' when actually different
            assert "oxsecurity/megalinter/flavors/dotnetweb" in captured.out
            lines = captured.out.split("\n")
            megalinter_line = [
                line
                for line in lines
                if "oxsecurity/megalinter/flavors/dotnetweb" in line
            ][0]
            assert "changed" in megalinter_line.lower()

            # Should show the old and new version/sha
            assert "v9.2.0" in megalinter_line
            assert "v10.0.0" in megalinter_line
            assert "55a59b24a441e0e1943080d4a512d827710d4a9d" in megalinter_line
            assert "newsha12345" in megalinter_line
