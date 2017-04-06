# Copyright 2017, Aaron Hosford

"""
clone
=====

Clone Git repositories without installing Git.
"""


import getpass
import os
import sys
import urllib.request
import zipfile


# TODO: Support other common sites.
URL_TEMPLATES = {
    'bitbucket': 'https://bitbucket.org/{user}/{repo}/get/master.zip',
    'github': 'https://github.com/{user}/{repo}/archive/master.zip',
}


USAGE = """
Usage:
    clone REPO [USER] [SITE]
""".strip()


def download_file(source_url, save_path=None):
    """
    Download a file from the source URL to the save path.
    
    :param source_url: The URL to download the file from. 
    :param save_path: The path where the file should be saved. Can be the path to
        an existing folder or to a nonexistent file. Defaults to the current
        working directory.
    :return: The full path to the downloaded file.
    """
    if save_path is None:
        save_path = os.path.join(os.getcwd(), os.path.basename(source_url))
    if os.path.isdir(save_path):
        save_path = os.path.join(save_path, os.path.basename(source_url))
    if os.path.isfile(save_path):
        raise FileExistsError(save_path)

    try:
        urllib.request.urlretrieve(source_url, save_path)
        return save_path
    except:
        if os.path.isfile(save_path):
            os.remove(save_path)
        raise


def clone_from_url(source_url, parent=None):
    """
    Clone a repo from a source URL.
    
    :param source_url: The URL where the source zip is located.
    :param parent: The parent folder where the repo should be cloned.
    :return: The path to the root folder of the repo.
    """
    if parent is None:
        parent = os.getcwd()
    elif not os.path.isdir(parent):
        raise NotADirectoryError(parent)

    zip_path = download_file(source_url, parent)

    try:
        with zipfile.ZipFile(zip_path) as repo:
            root = None
            for name in repo.namelist():
                assert name and not name.startswith('/'), "Downloaded repo contained absolute path."
                if name.count('/') == 1 and name.endswith('/'):
                    root = name
                    break
            assert root is not None, "Downloaded repo was empty."

            downloaded_path = os.path.join(parent, root)
            if os.path.isdir(downloaded_path):
                raise IsADirectoryError(downloaded_path)

            repo.extractall(parent)

            if not os.path.isdir(downloaded_path):
                raise NotADirectoryError(downloaded_path)
            return downloaded_path
    finally:
        if os.path.isfile(zip_path):
            os.remove(zip_path)


def clone(repo, user, site, parent=None):
    """
    Clone a repo from the requested site and user.
    
    :param repo: The name of the repo.
    :param user: The name of the user.
    :param site: The site to download from.
    :param parent: The parent folder where the repo will be cloned. By default,
        this is the current working directory.
    :return: The full path to the root directory of the cloned repo.
    """

    if parent is None:
        parent = os.getcwd()
    elif not os.path.isdir(parent):
        raise NotADirectoryError(parent)

    path = os.path.join(parent, repo)
    if os.path.isdir(path):
        raise IsADirectoryError(path)

    site = site.lower()
    if site not in URL_TEMPLATES:
        base = os.path.splitext(site)[0]
        if base not in URL_TEMPLATES:
            raise KeyError(site)
        site = base

    url = URL_TEMPLATES[site].format(user=user, repo=repo)

    # TODO: Download to a temporary folder first, then rename.
    downloaded_path = clone_from_url(url, parent)
    os.rename(downloaded_path, path)

    if not os.path.isdir(path):
        raise NotADirectoryError(path)

    return path


def iter_default_users():
    """Return an iterator over the default user list."""
    candidates = [
        getpass.getuser(),
        os.path.basename(os.path.expanduser('~')),
    ]

    for key in 'USER', 'USERNAME':
        if key in os.environ:
            candidates.append(os.environ[key])

    # noinspection PyBroadException
    try:
        candidates.append(os.getlogin())
    except Exception:
        pass

    covered = set()
    for candidate in candidates:
        if candidate.lower() not in covered:
            yield candidate
            covered.add(candidate.lower())


def search(repos, users=None, sites=None):
    """
    Search across supported sites for cloneable repositories. 
    
    :param repos: The repo(s) to search for.
    :param users: The user(s) to search under. If none is provided, the environment
        is examined for possible user names.
    :param sites: The site(s) to search in. If no sites are provided, all recognized
        sites are searched.
    :return: An iterator over the repo/user/site triples which refer to valid
        cloneable Git repos.
    """
    if isinstance(repos, str):
        repos = [repos]
    else:
        repos = list(repos)

    if users is None:
        users = list(iter_default_users())
    elif isinstance(users, str):
        users = [users]
    else:
        users = list(users)

    if sites is None:
        sites = URL_TEMPLATES
    elif isinstance(sites, str):
        sites = [sites]

    for site in sites:
        site = site.lower()
        if site not in URL_TEMPLATES:
            base = os.path.splitext(site)[0]
            if base not in URL_TEMPLATES:
                raise KeyError(site)
            site = base
        template = URL_TEMPLATES[site]
        for user in users:
            for repo in repos:
                url = template.format(user=user, repo=repo)
                try:
                    urllib.request.urlopen(url)
                except (urllib.request.HTTPError, urllib.request.URLError):
                    continue
                else:
                    yield repo, user, site


def main():
    args = sys.argv[1:]

    if not args:
        print(USAGE)
        return 1
    elif len(args) == 1:
        repo = args[0]
        user = site = None
    elif len(args) == 2:
        repo, user = args
        site = None
    elif len(args) == 3:
        repo, user, site = args
    else:
        print(USAGE)
        return 1

    for matched_repo, matched_user, matched_site in search(repo, user, site):
        path = clone(matched_repo, matched_user, matched_site)
        print("Repo %s cloned to %s." % (matched_repo, path))
        return 0
    else:
        print("Repo %s not found." % repo)
        return 1
