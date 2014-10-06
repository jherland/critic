import subprocess

import api

import configuration
import gitutils

class Repository(object):
    def __init__(self, repository_id, name, path):
        self.id = repository_id
        self.name = name
        self.path = path
        self.__internal = None

    def getInternal(self, critic):
        if not self.__internal:
            self.__internal = gitutils.Repository.fromId(
                db=critic.getDatabase(),
                repository_id=self.id)
        return self.__internal

    def getURL(self, critic):
        return gitutils.Repository.constructURL(
            critic.getDatabase(),
            critic.effective_user._impl.getInternal(critic),
            self.path)

    def run(self, *args):
        argv = [configuration.executables.GIT] + list(args)
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.path)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise api.repository.GitCommandError(
                argv, process.returncode, stdout, stderr)
        return stdout

    def resolveRef(self, ref, expect, short):
        command_line = ["rev-parse", "--verify", "--quiet"]
        if short:
            if isinstance(short, int):
                command_line.append("--short=%d" % short)
            else:
                command_line.append("--short")
        if expect is not None:
            ref += "^{%s}" % expect
        command_line.append(ref)
        try:
            return self.run(*command_line).strip()
        except api.repository.GitCommandError:
            raise api.repository.InvalidRef(ref)

    def listCommits(self, repository, include, exclude, args, paths):
        args = ['rev-list'] + args
        args.extend(commit.sha1 for commit in include)
        args.extend("^" + commit.sha1 for commit in exclude)
        if paths:
            args.append("--")
            args.extend(paths)
        return [api.commit.fetch(repository, sha1=sha1)
                for sha1 in self.run(*args).split()]

    def wrap(self, critic):
        return api.repository.Repository(critic, self)

def make(critic, repository_id, name, path):
    def callback():
        return Repository(repository_id, name, path).wrap(critic)
    return critic._impl.cached(
        api.repository.Repository, repository_id, callback)

def fetch(critic, repository_id, name, path):
    cursor = critic.getDatabaseCursor()
    if repository_id is not None:
        cursor.execute("""SELECT id, name, path
                            FROM repositories
                           WHERE id=%s""",
                       (repository_id,))
    elif name is not None:
        cursor.execute("""SELECT id, name, path
                            FROM repositories
                           WHERE name=%s""",
                       (name,))
    else:
        cursor.execute("""SELECT id, name, path
                            FROM repositories
                           WHERE path=%s""",
                       (path,))
    row = cursor.fetchone()
    if not row:
        if repository_id is not None:
            raise api.repository.InvalidRepositoryId(repository_id)
        elif name is not None:
            raise api.repository.InvalidRepositoryName(name)
        else:
            raise api.repository.InvalidRepositoryPath(path)
    return make(critic, *row)

def fetchAll(critic):
    cursor = critic.getDatabaseCursor()
    cursor.execute("""SELECT id, name, path
                        FROM repositories
                    ORDER BY name""")
    return [make(critic, *row) for row in cursor]

def fetchHighlighted(critic, user):
    highlighted = set()

    cursor = critic.getDatabaseCursor()

    cursor.execute("""SELECT DISTINCT repository
                        FROM filters
                       WHERE uid=%s""",
                   (user.id,))
    highlighted.update(repository_id for (repository_id,) in cursor)

    cursor.execute("""SELECT DISTINCT repository
                        FROM branches
                        JOIN reviews ON (reviews.branch=branches.id)
                        JOIN reviewusers ON (reviewusers.review=reviews.id)
                       WHERE reviewusers.uid=%s
                         AND reviewusers.owner""",
                   (user.id,))
    highlighted.update(repository_id for (repository_id,) in cursor)

    cursor.execute("""SELECT id, name, path
                        FROM repositories
                       WHERE id=ANY (%s)
                    ORDER BY name""",
                   (list(highlighted),))
    return [make(critic, *row) for row in cursor]
