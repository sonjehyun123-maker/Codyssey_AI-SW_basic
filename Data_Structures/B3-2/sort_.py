def merge_sort(items, compare):
    "병합 정렬 구현: 주어진 비교 함수를 사용해 리스트를 정렬한다."
    if len(items) <= 1:
        return items

    mid = len(items) // 2
    left = merge_sort(items[:mid], compare)
    right = merge_sort(items[mid:], compare)
    return _merge(left, right, compare)


def _merge(left, right, compare):
    "두 정렬된 리스트를 병합하여 하나의 정렬된 리스트를 반환"
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
    "커밋의 타임스탬프를 비교하여 정렬 순서를 결정함"
    if commit_a.timestamp < commit_b.timestamp:
        return -1
    if commit_a.timestamp > commit_b.timestamp:
        return 1
    return 0


def compare_by_author(commit_a, commit_b):
    "커밋 작성자 이름을 비교하여 정렬 순서를 결정함"
    if commit_a.author < commit_b.author:
        return -1
    if commit_a.author > commit_b.author:
        return 1
    return 0


def sort_by_date(commits):
    "커밋 리스트를 날짜 기준으로 정렬하여 반환"
    return merge_sort(commits, compare_by_date)


def sort_by_author(commits):
    "커밋 리스트를 작성자 기준으로 정렬하여 반환"
    return merge_sort(commits, compare_by_author)