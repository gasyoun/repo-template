#!/usr/bin/env python
# repo-template base layer — TEST-ONLY mirror of the estate policy matcher.
# Source of truth: https://github.com/gasyoun/claude-config/blob/main/hooks/agent_policy.py
# Ported by H5770 (08-10-2026) from SUPPORTED_SCHEMA_VERSION '1'.
# Trimmed on purpose: no hook_config clause parsing (the raw-text fallback of
# _shell_haystack applies, which is the noisier/never-quieter direction), no
# --check CLI. If the estate schema evolves, re-port + re-run: the base tests
# pin the starter pack to the estate contract, byte drift here is a review item.
"""Policy matcher mirror (test-only) for repo-template base layer.

Loads + validates a `.agent_policy.json` pack and answers: does this tool call
hit a rule? Semantics match the estate guard: rules in order, first match wins;
shell commands also match `paths` against their target tokens; a rule's literal
override marker carried by the command bypasses THAT rule only.
"""
import json
import os
import re

POLICY_FILENAME = '.agent_policy.json'

ALLOWED_TOOLS = ('Bash', 'PowerShell', 'Write', 'Edit', 'Read', 'Grep', 'Glob')
SHELL_TOOLS = ('Bash', 'PowerShell')
FILE_TOOLS = ('Write', 'Edit', 'Read', 'Grep', 'Glob')
SEARCH_TOOLS = ('Grep', 'Glob')

ACTIONS = ('block', 'confirm', 'audit')
TOP_KEYS = ('schema_version', 'rules')
RULE_KEYS = ('id', 'match', 'action', 'reason', 'overrides')
MATCH_KEYS = ('paths', 'command_regex', 'tools')
SUPPORTED_SCHEMA_VERSION = '1'
PROSE_FLAGS = frozenset((
    '-b', '--body', '-t', '--title', '-m', '--message', '--notes'))


class PolicyError(ValueError):
    """The policy file exists but cannot be understood — consumers fail CLOSED."""


def _fail(path, where, why):
    raise PolicyError('%s: %s: %s' % (path, where, why))


def _unknown(obj, allowed):
    return sorted(k for k in set(obj) - set(allowed) if not k.startswith('_'))


def _str_list(path, where, value, what, required=True):
    if value is None:
        if required:
            _fail(path, where, '%s must be a non-empty list of strings' % what)
        return []
    if not isinstance(value, list) or not value:
        _fail(path, where, '%s must be a non-empty list of strings' % what)
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _fail(path, where, '%s entries must be non-empty strings' % what)
    return list(value)


def _compile(pattern, path, where):
    try:
        return re.compile(pattern)
    except re.error as exc:
        _fail(path, where, 'command_regex %r does not compile (%s)'
              % (pattern, exc))


def glob_to_regex(pattern):
    """Glob → regex: `**/` optional dirs, `**` cross-segment, `*`/`?` within one;
    a bare name fences the whole subtree; case-insensitive; unanchored (callers
    apply fullmatch or the boundary-suffix search in path_hit)."""
    out = []
    pattern = pattern.lower()
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == '*':
            if pattern[i:i + 3] == '**/':
                out.append('(?:.*/)?')
                i += 3
            elif (pattern[i:i + 2] == '**' and i + 2 == n and out
                    and out[-1] == '/'):
                out.pop()
                out.append('(?:/.*)?')
                i += 2
            elif pattern[i:i + 2] == '**':
                out.append('.*')
                i += 2
            else:
                out.append('[^/]*')
                i += 1
        elif c == '?':
            out.append('[^/]')
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    body = ''.join(out)
    if not any(ch in pattern for ch in '*?'):
        body += '(?:/.*)?'
    return re.compile(body)


def norm_path(text):
    return (text or '').replace('\\', '/').strip().lower()


def path_hit(regex, text):
    t = norm_path(text)
    if not t:
        return False
    if regex.fullmatch(t):
        return True
    return re.search(r'(?:^|/)' + regex.pattern + r'$', t) is not None


def validate_policy(doc, path='<policy>'):
    """Validate one parsed policy document → normalized rule list."""
    if not isinstance(doc, dict):
        _fail(path, 'document', 'must be a JSON object')
    version = doc.get('schema_version', SUPPORTED_SCHEMA_VERSION)
    if version != SUPPORTED_SCHEMA_VERSION:
        _fail(path, 'schema_version',
              'unsupported schema_version: found %r, supported: %r'
              % (version, SUPPORTED_SCHEMA_VERSION))
    unknown_top = _unknown(doc, TOP_KEYS)
    if unknown_top:
        _fail(path, 'document', 'unknown key(s) %s (allowed: %s)'
              % (', '.join(unknown_top), ', '.join(TOP_KEYS)))
    if 'rules' not in doc:
        _fail(path, 'document', 'missing required key "rules"')
    if not isinstance(doc['rules'], list):
        _fail(path, 'document', '"rules" must be a list')
    rules = []
    seen_ids = set()
    for idx, raw in enumerate(doc['rules']):
        where = 'rules[%d]' % idx
        if not isinstance(raw, dict):
            _fail(path, where, 'must be an object')
        unknown = _unknown(raw, RULE_KEYS)
        if unknown:
            _fail(path, where, 'unknown key(s) %s' % ', '.join(unknown))
        rid = raw.get('id')
        if not isinstance(rid, str) or not rid.strip():
            _fail(path, where, '"id" must be a non-empty string')
        if rid in seen_ids:
            _fail(path, where, 'duplicate rule id %r' % rid)
        seen_ids.add(rid)
        action = raw.get('action')
        if action not in ACTIONS:
            _fail(path, where, '"action" must be one of %s (got %r)'
                  % (', '.join(ACTIONS), action))
        reason = raw.get('reason')
        if not isinstance(reason, str) or not reason.strip():
            _fail(path, where, '"reason" must be a non-empty string')
        match = raw.get('match')
        if not isinstance(match, dict):
            _fail(path, where, '"match" must be an object')
        unknown = _unknown(match, MATCH_KEYS)
        if unknown:
            _fail(path, where + '.match', 'unknown key(s) %s' % ', '.join(unknown))
        if not any(k in match for k in MATCH_KEYS):
            _fail(path, where, 'match must declare at least one of %s'
                  % ', '.join(MATCH_KEYS))
        paths = [glob_to_regex(p) for p in _str_list(
            path, where + '.paths', match.get('paths'), 'paths', required=False)]
        regexes = [_compile(p, path, where + '.command_regex') for p in _str_list(
            path, where + '.command_regex', match.get('command_regex'),
            'command_regex', required=False)]
        tools = _str_list(path, where + '.tools', match.get('tools'), 'tools',
                          required=False)
        bad = [t for t in tools if t not in ALLOWED_TOOLS]
        if bad:
            _fail(path, where + '.tools', 'unknown tool(s) %s' % ', '.join(bad))
        declared = raw.get('overrides')
        overrides = _str_list(
            path, where + '.overrides', None if declared == [] else declared,
            'overrides', required=False)
        rules.append({'id': rid, 'action': action, 'reason': reason,
                      'paths': paths, 'command_regex': regexes,
                      'tools': tools, 'overrides': overrides})
    return rules


def load_policy(path):
    """None when absent (designed pass-through); PolicyError when unusable."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise PolicyError('%s: unreadable: %s' % (path, exc)) from exc
    return validate_policy(doc, path=path)


def _shell_haystack(cmd, cwd):
    """Raw-text fallback tokens (no clause parser in the mirror): the command
    minus quoted strings, plus quoted strings that look like paths."""
    stripped = re.sub(r'"[^"]*"|\'[^\']*\'', ' ', cmd)
    tokens = stripped.split()
    tokens += [q for q in re.findall(r'"[^"]*"|\'[^\']*\'', cmd)
               if ('/' in q or '\\' in q)]
    if cwd:
        tokens.append(cwd)
    return tokens


def _file_targets(tool_input):
    tin = tool_input if isinstance(tool_input, dict) else {}
    for key in ('file_path', 'path', 'notebook_path'):
        val = tin.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ''


def evaluate(rules, tool_name, tool_input, cwd, repo_root):
    """First matching rule, or None (estate semantics, raw-text fallback)."""
    tin = tool_input if isinstance(tool_input, dict) else {}
    cmd = tin.get('command', '') if tool_name in SHELL_TOOLS else ''
    file_target = _file_targets(tin) if tool_name in FILE_TOOLS else ''
    if not file_target and tool_name in SEARCH_TOOLS:
        file_target = cwd or ''
    regex_texts = [file_target] + [
        tin[k] for k in ('pattern', 'glob')
        if tool_name in SEARCH_TOOLS and isinstance(tin.get(k), str)
        and (tool_name == 'Glob' or k == 'glob')]
    rel_target = ''
    if file_target and repo_root:
        try:
            rel_target = os.path.relpath(file_target, repo_root)
        except ValueError:
            rel_target = ''
    for rule in rules:
        if rule['tools'] and tool_name not in rule['tools']:
            continue
        if cmd:
            if any(marker in cmd for marker in rule['overrides']):
                continue
            hit = any(rx.search(cmd) for rx in rule['command_regex'])
            if not hit:
                tokens = _shell_haystack(cmd, cwd)
                hit = any(path_hit(pat, tok)
                          for pat in rule['paths'] for tok in tokens)
            if hit:
                return rule
            continue
        if file_target:
            hit = any(path_hit(pat, file_target) or
                      (rel_target and path_hit(pat, rel_target))
                      for pat in rule['paths'])
            if not hit:
                hit = any(rx.search(text) for rx in rule['command_regex']
                          for text in regex_texts)
            if hit:
                return rule
    return None
