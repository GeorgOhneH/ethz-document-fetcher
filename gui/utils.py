
def format_bytes(size):
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti', 5: "Pi"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels[n] + 'B'}"
