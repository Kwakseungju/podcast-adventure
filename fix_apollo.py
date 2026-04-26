import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BACKSLASH = chr(92)  # avoid escaping issues in source


def escape_control_in_strings(s):
    """Escape newlines/tabs only inside JSON string values."""
    result = []
    in_str = False
    skip_next = False
    for ch in s:
        if skip_next:
            result.append(ch)
            skip_next = False
        elif ch == BACKSLASH and in_str:
            result.append(ch)
            skip_next = True
        elif ch == '"':
            result.append(ch)
            in_str = not in_str
        elif in_str and ch == '\n':
            result.append(BACKSLASH + 'n')
        elif in_str and ch == '\r':
            result.append(BACKSLASH + 'r')
        elif in_str and ch == '\t':
            result.append(BACKSLASH + 't')
        else:
            result.append(ch)
    return ''.join(result)


eps = json.load(open('data/episodes.json', encoding='utf-8'))
fixed_count = 0

for ep in eps:
    if ep.get('key_takeaways'):
        continue
    summary = ep.get('summary', '')
    if not summary.startswith('{'):
        continue
    sanitized = escape_control_in_strings(summary)
    try:
        data = json.loads(sanitized)
    except json.JSONDecodeError as e:
        print(f'Could not parse {ep["title"]}: {e}')
        continue
    ep['one_line_summary'] = data.get('one_line_summary', ep.get('one_line_summary', ''))
    ep['summary']          = data.get('summary', '')
    ep['key_themes']       = data.get('key_themes', [])[:5]
    ep['key_takeaways']    = data.get('key_takeaways', [])[:5]
    ep['market_relevance'] = data.get('market_relevance', '')
    fixed_count += 1
    print(f'Fixed: {ep["title"]}')

with open('data/episodes.json', 'w', encoding='utf-8') as f:
    json.dump(eps, f, indent=2, ensure_ascii=False)

print(f'Done - fixed {fixed_count} episode(s)')
