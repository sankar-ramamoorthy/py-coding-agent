---
name: myp1
description: what is today's day of week?
status: approved
allowed_tools: [get_current_datetime]
constraints: [Relies on datetime MCP server for current time]
---

# myp1

Returns the current day of the week (e.g., "Monday") by querying the datetime MCP server.

## Usage

```
/skill myp1
```

## Expected Output

Human-readable day name like "Wednesday" or "Friday".

## Constraints

- Requires access to datetime MCP server
- Returns UTC day of week (not local time)
- No file system/network operations performed