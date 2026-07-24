def merge_sort(items, compare):
    if len(items) <= 1:
        return items

    mid = len(items) // 2
    left = merge_sort(items[:mid], compare)
    right = merge_sort(items[mid:], compare)
    return _merge(left, right, compare)


def _merge(left, right, compare):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if compare(left[i], right[j]) <= 0:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def compare_by_date(commit_a, commit_b):
    if commit_a.timestamp < commit_b.timestamp:
        return -1
    if commit_a.timestamp > commit_b.timestamp:
        return 1
    return 0


def compare_by_author(commit_a, commit_b):
    if commit_a.author < commit_b.author:
        return -1
    if commit_a.author > commit_b.author:
        return 1
    return 0


def sort_by_date(commits):
    return merge_sort(commits, compare_by_date)


def sort_by_author(commits):
    return merge_sort(commits, compare_by_author)