import api

class CommitSet(api.APIObject):
    """Representation of a set of Commit objects"""

    def __iter__(self):
        return iter(self._impl)
    def __len__(self):
        return len(self._impl)
    def __contains__(self, item):
        return item in self._impl
    def __hash__(self):
        return hash(self._impl)
    def __eq__(self, other):
        assert isinstance(other, CommitSet)
        return self._impl == other._impl
    def __nonzero__(self):
        return len(self._impl) != 0
    def __repr__(self):
        return "api.commitset.CommitSet(%r)" % list(self.topo_ordered)

    @property
    def date_ordered(self):
        """The commits in the set in (commit) timestamp order

           The return value is a generator producing api.commit.Commit objects.
           Commits are guaranteed to precede their parents, even if the actual
           commit timestamp order is the opposite."""
        return self._impl.getDateOrdered()

    @property
    def topo_ordered(self):
        """The commits in the set in "topological" order

           The return value is a generator producing api.commit.Commit objects.
           Commits are guaranteed to precede their parents, and as far as
           possible immediately precede their parent.

           It is only valid to call this function on commit sets with a single
           head (those whose 'heads' attribute returns a set of length 1.)"""
        assert not self or len(self.heads) == 1
        return self._impl.getTopoOrdered()

    @property
    def heads(self):
        """The head commits of the set

           The return value is a frozenset of Commit objects.

           A "head commit" is defined as any commit in the set that is
           not an immediate parent of another commit in the set."""
        return self._impl.heads

    @property
    def tails(self):
        """The tail commits of the set

           The return value is a frozenset of Commit objects.

           A "tail commit" is defined as any commit that is a parent of
           a commit in the set but isn't itself in the set."""
        return self._impl.tails

    def getChildrenOf(self, commit):
        """Return the commits in the set that are children of the commit

           The return value is a set of Commit objects."""
        assert isinstance(commit, api.commit.Commit)
        return self._impl.getChildrenOf(commit)

    def getParentsOf(self, commit):
        """Return the intersection of the commit's parents and the set

           The return value is a list of Commit objects, in the same
           order as in "commit.parents"."""
        assert isinstance(commit, api.commit.Commit)
        return self._impl.getParentsOf(commit)

    def getDescendantsOf(self, commit, include_self=False):
        """Return the intersection of the commit's descendants and the set

           The return value is another CommitSet object.  If 'include_self' is
           True, the commit itself is included in the returned set.

           The argument can also be a iterable, in which case the returned set
           is the union of the sets that would be returned for each commit in
           the iterable."""
        if isinstance(commit, api.commit.Commit):
            commits = [commit]
        else:
            commits = list(commit)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        assert all(commit in self or commit in self.tails for commit in commits)
        return self._impl.getDescendantsOf(commits, include_self)

    def getAncestorsOf(self, commit, include_self=False):
        """Return the intersection of the commit's ancestors and the set

           The return value is another CommitSet object.  If 'include_self' is
           True, the commit itself is included in the returned set.

           The argument can also be a iterable, in which case the returned set
           is the union of the sets that would be returned for each commit in
           the iterable."""
        if isinstance(commit, api.commit.Commit):
            commits = [commit]
        else:
            commits = list(commit)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        return self._impl.getAncestorsOf(commits, include_self)

    def union(self, commits):
        commits = set(commits)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        return self._impl.union(self.critic, commits)
    def __or__(self, commits):
        return self.union(commits)

    def intersection(self, commits):
        commits = set(commits)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        return self._impl.intersection(self.critic, commits)
    def __and__(self, commits):
        return self.intersection(commits)

    def difference(self, commits):
        commits = set(commits)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        return self._impl.difference(self.critic, commits)
    def __sub__(self, commits):
        return self.difference(commits)

    def symmetric_difference(self, commits):
        commits = set(commits)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
        return self._impl.symmetric_difference(self.critic, commits)
    def __xor__(self, commits):
        return self.symmetric_difference(commits)

def create(critic, commits):
    """Create a CommitSet object from an iterable of Commit objects"""
    import api.impl
    assert isinstance(critic, api.critic.Critic)
    if not isinstance(commits, CommitSet):
        commits = list(commits)
        assert all(isinstance(commit, api.commit.Commit) for commit in commits)
    return api.impl.commitset.create(critic, commits)
