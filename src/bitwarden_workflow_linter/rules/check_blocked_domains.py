"""A Rule to check for blocked/malicious domains in workflow content."""

import re
from typing import List, Optional, Tuple, Union

from ..models.job import Job
from ..models.step import Step
from ..models.workflow import Workflow
from ..rule import Rule
from ..utils import LintLevels, Settings


class RuleCheckBlockedDomains(Rule):
    """Rule to detect blocked or malicious domains in workflow content.
    
    This rule scans workflow content (URLs, scripts, commands) for domains
    that have been flagged as blocked or potentially malicious. It helps
    prevent supply chain attacks and unauthorized external dependencies.
    """

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.ERROR) -> None:
        """Constructor for RuleCheckBlockedDomains.

        Args:
          settings:
            A Settings object that contains any default, overridden, or custom settings
            required anywhere in the application.
          lint_level:
            The LintLevels enum value to determine the severity of the rule.
        """
        self.on_fail = lint_level
        self.compatibility = [Workflow, Job, Step]
        self.settings = settings
        
        # Get blocked domains from settings, use defaults if none provided
        self.blocked_domains = settings.blocked_domains if settings else []

    def extract_domains_from_text(self, text: str) -> List[str]:
        """Extract domain names from text content.
        
        Args:
            text: The text to scan for domains
            
        Returns:
            List of domain names found in the text
        """
        if not text:
            return []
            
        # Pattern to match domain names in various contexts
        # Breaking down the regex:
        # (?:https?://)?           - Optional protocol (http:// or https://)
        # (?:www\.)?               - Optional www. prefix
        # ([a-zA-Z0-9]             - Start of capturing group: first character (alphanumeric)
        #   (?:[a-zA-Z0-9-]{0,61}  - Non-capturing group: 0-61 alphanumeric or hyphen chars
        #   [a-zA-Z0-9])?          - End with alphanumeric (ensures no trailing hyphen)
        # \.)+                     - Followed by dot, repeated (for subdomains)
        # [a-zA-Z]{2,}             - Top-level domain (2+ letters)
        # (?:/[^\s]*)?             - Optional path (slash followed by non-whitespace chars)
        domain_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:/[^\s]*)?'
        
        domains = set()
        
        # Find all matches and extract the domain part
        for match in re.finditer(domain_pattern, text, re.IGNORECASE):
            full_match = match.group(0)
            # Clean up the domain (remove protocol, www, path)
            domain = re.sub(r'^https?://', '', full_match)
            domain = re.sub(r'^www\.', '', domain)
            domain = re.sub(r'/.*$', '', domain)  # Remove path
            domain = domain.lower().strip()
            
            if domain and '.' in domain:
                domains.add(domain)
        
        return list(domains)

    def check_blocked_domains(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains any blocked domains.
        
        Args:
            text: The text to check for blocked domains
            
        Returns:
            Tuple of (is_clean, list_of_found_blocked_domains)
        """
        if not text:
            return True, []
            
        domains = self.extract_domains_from_text(text)
        blocked_found = []
        
        for domain in domains:
            for blocked_domain in self.blocked_domains:
                blocked_domain_lc = blocked_domain.lower().strip()
                domain_lc = domain.lower().strip()
                # Check for exact match or subdomain match
                if domain_lc == blocked_domain_lc or domain_lc.endswith('.' + blocked_domain_lc):
                    blocked_found.append(domain)
                    
        return len(blocked_found) == 0, blocked_found

    def fn(self, obj: Union[Workflow, Job, Step]) -> Tuple[bool, str]:
        """Check the workflow object for blocked domains.

        Args:
          obj: The workflow object (Workflow, Job, or Step) to check

        Returns:
          Tuple of (success, error_message)
        """
        blocked_domains_found = []
        
        if isinstance(obj, Workflow):
            # Check workflow-level content
            if obj.name:
                is_clean, domains = self.check_blocked_domains(obj.name)
                if not is_clean:
                    blocked_domains_found.extend([(f"workflow name", domain) for domain in domains])
                    
        elif isinstance(obj, Job):
            # Check job-level content
            if obj.name:
                is_clean, domains = self.check_blocked_domains(obj.name)
                if not is_clean:
                    blocked_domains_found.extend([(f"job name", domain) for domain in domains])
                    
            if obj.uses:
                is_clean, domains = self.check_blocked_domains(obj.uses)
                if not is_clean:
                    blocked_domains_found.extend([(f"job uses", domain) for domain in domains])
                    
            # Check environment variables
            if obj.env:
                for key, value in obj.env.items():
                    if isinstance(value, str):
                        is_clean, domains = self.check_blocked_domains(value)
                        if not is_clean:
                            blocked_domains_found.extend([(f"job env '{key}'", domain) for domain in domains])
                            
        elif isinstance(obj, Step):
            # Check step-level content
            if obj.name:
                is_clean, domains = self.check_blocked_domains(obj.name)
                if not is_clean:
                    blocked_domains_found.extend([(f"step name", domain) for domain in domains])
                    
            if obj.uses:
                is_clean, domains = self.check_blocked_domains(obj.uses)
                if not is_clean:
                    blocked_domains_found.extend([(f"step uses", domain) for domain in domains])
                    
            if obj.run:
                is_clean, domains = self.check_blocked_domains(obj.run)
                if not is_clean:
                    blocked_domains_found.extend([(f"step run command", domain) for domain in domains])
                    
            # Check environment variables
            if obj.env:
                for key, value in obj.env.items():
                    if isinstance(value, str):
                        is_clean, domains = self.check_blocked_domains(value)
                        if not is_clean:
                            blocked_domains_found.extend([(f"step env '{key}'", domain) for domain in domains])
                            
            # Check step with parameters
            if obj.uses_with:
                for key, value in obj.uses_with.items():
                    if isinstance(value, str):
                        is_clean, domains = self.check_blocked_domains(value)
                        if not is_clean:
                            blocked_domains_found.extend([(f"step with '{key}'", domain) for domain in domains])

        if blocked_domains_found:
            error_details = []
            for location, domain in blocked_domains_found:
                error_details.append(f"Found blocked domain '{domain}' in {location}")
            return False, "; ".join(error_details)
            
        return True, ""
