import api

class ReviewError(api.APIError):
    """Base exception for all errors related to the Review class."""
    pass

class InvalidReviewId(ReviewError):
    """Raised when an invalid review id is used."""

    def __init__(self, review_id):
        """Constructor"""
        super(InvalidReviewId, self).__init__(
            "Invalid review id: %d" % review_id)

class InvalidReviewBranch(ReviewError):
    """Raised when an invalid review branch is used."""

    def __init__(self, branch):
        """Constructor"""
        super(InvalidReviewBranch, self).__init__(
            "Invalid review branch: %r" % str(branch))

class Review(api.APIObject):
    """Representation of a Critic review"""

    def __int__(self):
        return self.id
    def __hash__(self):
        return hash(int(self))
    def __eq__(self, other):
        return int(self) == int(other)

    @property
    def id(self):
        """The review's unique id"""
        return self._impl.id

    @property
    def summary(self):
        """The review's summary"""
        return self._impl.summary

    @property
    def description(self):
        """The review's description, or None"""
        return self._impl.description

    @property
    def branch(self):
        """The review's branch

           The branch is returned as a api.branch.Branch object."""
        return self._impl.getBranch(self.critic)

    @property
    def owners(self):
        """The review's owners

           The owners are returned as a set of api.user.User objects."""
        return self._impl.getOwners(self.critic)

    @property
    def filters(self):
        """The review's local filters

           The filters are returned as a list of api.filters.ReviewFilter
           objects."""
        return self._impl.getFilters(self.critic)

    @property
    def commits(self):
        """The set of commits that are part of the review

           Note: This set never changes when the review branch is rebased, and
                 commits are never removed from it.  For the set of commits that
                 are actually reachable from the review branch, consult the
                 'commits' attribute on the api.branch.Branch object that is
                 returned by the 'branch' attribute."""
        return self._impl.getCommits(self.critic)

    @property
    def rebases(self):
        """The rebases of the review branch

           The rebases are returned as a list of api.log.rebase.Rebase objects,
           ordered chronologically with the most recent rebase first."""
        return self._impl.getRebases(self)

    @property
    def first_partition(self):
        return api.log.partition.create(
            self.critic, self.commits, self.rebases)

def fetch(critic, review_id=None, branch=None):
    """Fetch a Review object with the given id or branch"""
    import api.impl
    assert isinstance(critic, api.critic.Critic)
    assert (review_id is None) != (branch is None)
    assert branch is None or isinstance(branch, api.branch.Branch)
    return api.impl.review.fetch(critic, review_id, branch)
