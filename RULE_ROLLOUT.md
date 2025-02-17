# Workflow linter rule rollout process

This document outlines the process for rolling out new workflow linter rules.

## Problem Statement

Releasing new rules in the workflow linter can cause friction by breaking existing workflows. The structured rollout process in this document aims to minimize disruptions and ensure teams have time to adjust before enforcing the new rule.

## Rollout process

### Stage 1: Warning level

Introduce a new rule as a warning level.

During this phase, the rule is introduced without enforcing failures, allowing teams to identify necessary changes without immediate disruption.

A minor version bump of the linter is made to reflect the new functionality by adding the `version:minor` label to the PR that introduces a new rule.

### Stage 2: Announcement

Announce the new rule with its grace period to the engineering organization.

An announcement is made to the `#team-eng` Slack channel and other relevant teams. This announcement includes a description of the rule, its rationale, its expected impact on existing workflows, and the deadline for when it will be enforced as an error.

The grace period should last until the end of the next sprint for the teams to be able to plan the time to comply with the new rule in all the workflows that the team owns.

### Stage 3: Workflow updates

During the grace period, teams need to adapt and update their workflows to the new linter rule standards, which means eliminating any warnings.

Also, the BRE team ensures that all BRE-owned workflows, such as release and deployment pipelines, are updated to comply with the new rule before it is enforced.


> In the future, we may add more developed systems for tracking compliance and sending periodic reminders on Slack before enforcement. BRE will be evaluating the need for such features as we roll out this process.

### Stage 4: Error level

Change the rule to the ERROR level.

At the end of the grace period, the new rule is transitioned to an error-level one by creating a PR in the workflow linter repository.

A major version bump should be released by adding the `version:major` label to the PR. Raising the rule to the error level is a breaking change that requires teams to comply with it to avoid workflow linter check failures.
An announcement is made to the `#team-eng` Slack channel as a follow-up on the same thread where the original announcement was made, with the `Also sent to #team-eng channel` checkbox checked, that the level was changed to an error level.