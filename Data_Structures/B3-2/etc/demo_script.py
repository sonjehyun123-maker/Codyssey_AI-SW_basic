import sys
sys.path.insert(0, '..')
from Repository import Repository
import main as m


def show(line):
    print(f"mini-git> {line}")


repo = Repository()

show('init son')
m.handle_init(repo, ['son'])

show('commit "1"')
m.handle_commit(repo, ['1'])

show('branch feature')
m.handle_branch(repo, ['feature'])

show('switch feature')
m.handle_switch(repo, ['feature'])

show('commit "2"')
m.handle_commit(repo, ['2'])
feature_tip = repo.branches['feature']

show('switch main')
m.handle_switch(repo, ['main'])

show('branch fea')
m.handle_branch(repo, ['fea'])

show('switch fea')
m.handle_switch(repo, ['fea'])

show('commit "3"')
m.handle_commit(repo, ['3'])
fea_tip = repo.branches['fea']

show('switch main')
m.handle_switch(repo, ['main'])

show('commit "4"')
m.handle_commit(repo, ['4'])

show('init kim')
m.handle_init(repo, ['kim'])

show('commit "5"')
m.handle_commit(repo, ['5'])
main_tip = repo.branches['main']

show('log')
m.handle_log(repo, [])

show('log --sort-by=date')
m.handle_log(repo, ['--sort-by=date'])

show('log --sort-by=author')
m.handle_log(repo, ['--sort-by=author'])

show('search 1')
m.handle_search(repo, ['1'])

show('search --author=son')
m.handle_search(repo, ['--author=son'])

feature_short = m.short_hash(feature_tip)
fea_short = m.short_hash(fea_tip)
show(f'path {feature_short} {fea_short}')
m.handle_path(repo, [feature_short, fea_short])

main_short = m.short_hash(main_tip)
show(f'ancestors {main_short}')
m.handle_ancestors(repo, [main_short])

show('--- 에러 케이스 ---')

show('commit')
m.handle_commit(repo, [])

show('switch nonexistent')
m.handle_switch(repo, ['nonexistent'])

show('branch main')
m.handle_branch(repo, ['main'])

show('path zzzz ' + main_short)
m.handle_path(repo, ['zzzz', main_short])

show('ancestors zzzz')
m.handle_ancestors(repo, ['zzzz'])

# Ambiguous commit 재현: 앞 4자리가 겹치는 커밋 2개를 강제로 만듦
from entry import Commit
dup_a = Commit('dup_a', 'son', [])
dup_b = Commit('dup_b', 'son', [])
dup_a.hash = '1234' + 'a' * 36
dup_b.hash = '1234' + 'b' * 36
repo.hashmap.put(dup_a)
repo.hashmap.put(dup_b)
show('ancestors 1234')
m.handle_ancestors(repo, ['1234'])

show('exit')
