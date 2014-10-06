import api
import api.impl.filters

class Review(object):
    def __init__(self, review_id, repository_id, branch_id, summary, description):
        self.id = review_id
        self.__repository_id = repository_id
        self.__branch_id = branch_id
        self.summary = summary
        self.description = description
        self.__owners = None
        self.__filters = None
        self.__commits = None
        self.__rebases = None

    def getRepository(self, critic):
        return api.repository.fetch(critic, repository_id=self.__repository_id)

    def getBranch(self, critic):
        return api.branch.fetch(critic, branch_id=self.__branch_id)

    def getOwners(self, critic):
        if self.__owners is None:
            cursor = critic.getDatabaseCursor()
            cursor.execute("""SELECT uid
                                FROM reviewusers
                               WHERE review=%s
                                 AND owner""",
                           (self.id,))
            self.__owners = frozenset(api.user.fetchMany(
                critic, (user_id for (user_id,) in cursor)))
        return self.__owners

    def getFilters(self, critic):
        if self.__filters is None:
            cursor = critic.getDatabaseCursor()
            cursor.execute("""SELECT uid, type, path, id, review, creator
                                FROM reviewfilters
                               WHERE review=%s""",
                           (self.id,))
            impls = [api.impl.filters.ReviewFilter(*row) for row in cursor]
            self.__filters = [api.filters.ReviewFilter(critic, impl)
                              for impl in impls]
        return self.__filters

    def getCommits(self, critic):
        if self.__commits is None:
            cursor = critic.getDatabaseCursor()
            # Direct changesets: no merges, no rebase changes.
            cursor.execute(
                """SELECT DISTINCT commits.id, commits.sha1
                     FROM commits
                     JOIN changesets ON (changesets.child=commits.id)
                     JOIN reviewchangesets ON (reviewchangesets.changeset=changesets.id)
                    WHERE reviewchangesets.review=%s
                      AND changesets.type='direct'""",
                (self.id,))
            commit_ids_sha1s = set(cursor)
            # Merge changesets, excluding those added by move rebases.
            cursor.execute(
                """SELECT DISTINCT commits.id, commits.sha1
                     FROM commits
                     JOIN changesets ON (changesets.child=commits.id)
                     JOIN reviewchangesets ON (reviewchangesets.changeset=changesets.id)
          LEFT OUTER JOIN reviewrebases ON (reviewrebases.old_head=commits.id
                                        AND reviewrebases.new_head IS NOT NULL
                                        AND reviewrebases.new_upstream IS NOT NULL)
                    WHERE reviewchangesets.review=%s
                      AND changesets.type='merge'
                      AND reviewrebases.id IS NULL""",
                (self.id,))
            commit_ids_sha1s.update(cursor)
            repository = self.getRepository(critic)
            commits = [api.commit.fetch(repository, commit_id, sha1)
                       for commit_id, sha1 in commit_ids_sha1s]
            self.__commits = api.commitset.create(critic, commits)
        return self.__commits

    def getRebases(self, wrapper):
        if self.__rebases is None:
            critic = wrapper.critic
            cursor = critic.getDatabaseCursor()
            cursor.execute(
                """SELECT id, old_head, new_head, old_upstream, new_upstream, uid
                     FROM reviewrebases
                    WHERE review=%s
                      AND new_head IS NOT NULL
                 ORDER BY id DESC""",
                (self.id,))
            rebases = [api.impl.log.rebase.Rebase(wrapper, *row)
                       for row in cursor]
            self.__rebases = [rebase.wrap(critic) for rebase in rebases]
        return self.__rebases

    def wrap(self, critic):
        return api.review.Review(critic, self)

def fetch(critic, review_id, branch):
    cursor = critic.getDatabaseCursor()
    if review_id is not None:
        cursor.execute("""SELECT reviews.id, branches.repository, branches.id,
                                 summary, description
                            FROM reviews
                            JOIN branches ON (branches.id=reviews.branch)
                           WHERE reviews.id=%s""",
                       (review_id,))
    else:
        cursor.execute("""SELECT reviews.id, branches.repository, branches.id,
                                 summary, description
                            FROM reviews
                            JOIN branches ON (branches.id=reviews.branch)
                           WHERE branches.id=%s""",
                       (int(branch),))
    row = cursor.fetchone()
    if not row:
        if review_id is not None:
            raise api.review.InvalidReviewId(review_id)
        else:
            raise api.review.InvalidReviewBranch(branch)
    review_id, repository_id, branch_id, summary, description = row

    def callback():
        return Review(review_id, repository_id, branch_id,
                      summary, description).wrap(critic)

    return critic._impl.cached(api.review.Review, review_id, callback)
