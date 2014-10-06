import api

class CommitSet(object):
    def __init__(self, commits):
        self.commits = frozenset(commits)
        self.__children = {}

        parents = set()
        for commit in self.commits:
            parents.update(commit.parents)
            for parent in commit.parents:
                self.__children.setdefault(parent, set()).add(commit)

        self.heads = frozenset(self.commits - parents)
        self.tails = frozenset(parents - self.commits)

    def __iter__(self):
        return iter(self.commits)
    def __len__(self):
        return len(self.commits)
    def __contains__(self, item):
        return str(item) in self.commits
    def __hash__(self):
        return hash(self.commits)
    def __eq__(self, other):
        return self.commits == other.commits

    def getDateOrdered(self):
        queue = sorted(self.commits,
                       key=lambda commit: commit.committer.timestamp,
                       reverse=True)
        included = set()

        while queue:
            commit = queue.pop(0)
            if commit in included:
                continue
            if commit in self.__children and self.__children[commit] - included:
                # Some descendants of this commit have not yet been emitted; we
                # have to delay this commit.  We can only delay this commit if
                # the queue is non-empty, so assert that it isn't.
                assert queue
                queue.insert(1, commit)
                continue
            yield commit
            included.add(commit)

    def getTopoOrdered(self):
        if not self:
            return

        head = set(self.heads).pop()

        queue = [head]
        included = set()

        while queue:
            commit = queue.pop(0)
            if commit in included:
                continue
            if commit in self.__children and self.__children[commit] - included:
                # Some descendants of this commit have not yet been emitted; we
                # have to delay this commit.  We can only delay this commit if
                # the queue is non-empty, so assert that it isn't.
                assert queue
                queue.append(commit)
                continue
            yield commit
            included.add(commit)
            parents = sorted((parent for parent in commit.parents
                              if parent in self and parent not in included),
                             key=lambda commit: commit.committer.timestamp,
                             reverse=False)
            queue[:0] = parents

    def getChildrenOf(self, commit):
        return set(self.__children.get(commit, []))

    def getParentsOf(self, commit):
        return [parent for parent in commit.parents
                if parent in self]

    def getDescendantsOf(self, commits, include_self):
        descendants = set()
        if include_self:
            descendants.update(commits)
        queue = set()
        for commit in commits:
            queue.update(self.getChildrenOf(commit))
        while queue:
            descendant = queue.pop()
            descendants.add(descendant)
            children = self.__children.get(descendant)
            if children:
                queue.update(children - descendants)
        return create(commits[0].critic, descendants)

    def getAncestorsOf(self, commits, include_self):
        ancestors = set()
        if include_self:
            ancestors.update(commits)
        queue = set()
        for commit in commits:
            queue.update(self.getParentsOf(commit))
        while queue:
            ancestor = queue.pop()
            ancestors.add(ancestor)
            queue.update(set(self.getParentsOf(ancestor)) - ancestors)
        return create(commits[0].critic, ancestors)

    def union(self, critic, commits):
        return create(critic, self.commits.union(commits))
    def intersection(self, critic, commits):
        return create(critic, self.commits.intersection(commits))
    def difference(self, critic, commits):
        return create(critic, self.commits.difference(commits))
    def symmetric_difference(self, critic, commits):
        return create(critic, self.commits.symmetric_difference(commits))

def create(critic, commits):
    if isinstance(commits, api.commitset.CommitSet):
        assert isinstance(commits._impl, CommitSet)
        impl = commits._impl
    else:
        impl = CommitSet(commits)

    return api.commitset.CommitSet(critic, impl)
