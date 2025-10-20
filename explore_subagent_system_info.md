# Explore Subagent - System Information

This document contains the verbatim system information about the Explore subagent from Claude Code's internal documentation.

## Agent Description

From the Task tool documentation:

```
- Explore: Fast agent specialized for exploring codebases. Use this when you need to
  quickly find files by patterns (eg. "src/components/**/*.tsx"), search code for
  keywords (eg. "API endpoints"), or answer questions about the codebase (eg. "how do
  API endpoints work?"). When calling this agent, specify the desired thoroughness
  level: "quick" for basic searches, "medium" for moderate exploration, or "very
  thorough" for comprehensive analysis across multiple locations and naming conventions.
  (Tools: Glob, Grep, Read, Bash)
```

## When to Use the Task Tool with Explore

From the tool usage policy:

```
- VERY IMPORTANT: When exploring the codebase to gather context or to answer a question
  that is not a needle query for a specific file/class/function, it is CRITICAL that
  you use the Task tool with subagent_type=Explore instead of running search commands
  directly.
```

### Examples of When to Use Explore:

```xml
<example>
user: Where are errors from the client handled?
assistant: [Uses the Task tool with subagent_type=Explore to find the files that handle
client errors instead of using Glob or Grep directly]
</example>

<example>
user: What is the codebase structure?
assistant: [Uses the Task tool with subagent_type=Explore]
</example>
```

## When NOT to Use the Task/Explore Tool

```
When NOT to use the Agent tool:
- If you want to read a specific file path, use the Read or Glob tool instead of the
  Agent tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the Glob
  tool instead, to find the match more quickly
- If you are searching for code within a specific file or set of 2-3 files, use the
  Read tool instead of the Agent tool, to find the match more quickly
- Other tasks that are not related to the agent descriptions above
```

## Available Tools for Explore Subagent

The Explore subagent has access to:
- **Glob**: Fast file pattern matching tool
- **Grep**: Powerful search tool built on ripgrep
- **Read**: Read files from the filesystem
- **Bash**: Execute bash commands for terminal operations

## How the Task Tool Works

```
When using the Task tool, you must specify a subagent_type parameter to select which
agent type to use.

Usage notes:
- Launch multiple agents concurrently whenever possible, to maximize performance; to do
  that, use a single message with multiple tool uses
- When the agent is done, it will return a single message back to you. The result
  returned by the agent is not visible to the user. To show the user the result, you
  should send a text message back to the user with a concise summary of the result.
- Each agent invocation is stateless. You will not be able to send additional messages
  to the agent, nor will the agent be able to communicate with you outside of its final
  report. Therefore, your prompt should contain a highly detailed task description for
  the agent to perform autonomously and you should specify exactly what information the
  agent should return back to you in its final and only message to you.
- The agent's outputs should generally be trusted
- Clearly tell the agent whether you expect it to write code or just to do research
  (search, file reads, web fetches, etc.), since it is not aware of the user's intent
```

## Release Notes Context

From Claude Code version 2.0.17:
```
• Introducing the Explore subagent. Powered by Haiku it'll search through your codebase
  efficiently to save context!
```

From Claude Code version 2.0.17:
```
• Haiku 4.5 automatically uses Sonnet in plan mode, and Haiku for execution (i.e.
  SonnetPlan by default)
```

This means the Explore subagent uses Haiku 4.5, which is faster and more cost-effective than Sonnet for exploratory tasks.
