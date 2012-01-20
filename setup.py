from os.path import abspath, dirname, join as join_path
from setuptools import setup, find_packages

here = abspath(dirname(__file__))
def read(filename):
    path = join_path(here, filename)
    sock = open(path)
    text = sock.read()
    sock.close()
    return text


setup(
    name='awraamba',
    version='0.1',
    description='awraamba',
    long_description=read('README.md') + '\n\n' + read('CHANGES.md'),
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='James Arthur',
    author_email='username: thruflo, domain: gmail.com',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='awraamba',
    install_requires = [
        'pyramid',
        'SQLAlchemy',
        'transaction',
        'pyramid_assetgen',
        'pyramid_debugtoolbar',
        'pyramid_tm',
        'pyramid_weblayer',
        'zope.sqlalchemy',
        'waitress',
        # Imaging, e.g.: http://dist.repoze.org/PIL-1.1.6.tar.gz
        'assetgen',
        'formencode',
        'passlib',
        'PyCrypto',
        'pyDNS',
        'psycopg2',
        'python-dateutil',
        'setuptools-git',
    ],
    entry_points = """\
        [setuptools.file_finders]
        foo = setuptools_git:gitlsfiles
        [paste.app_factory]
        main = awraamba.app:factory
        [console_scripts]
        reset_db = awraamba.scripts.db:reset
        create_admin = awraamba.scripts.db:create_admin
        populate_db = awraamba.scripts.db:populate
        bootstrap_db = awraamba.scripts.db:bootstrap
    """,
)
