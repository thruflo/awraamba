This is work in progress towards an interactive documentary website for the
[Awra Amba Experience][].

It's a unix Python [WSGI][] application, using [weblayer][] to handle requests
and [SQLAlchemy][] to interact with a [PostgreSQL][] database.  You'll need to
have [Sass][], [CoffeeScript][] and [UglifyJS][] installed to build the static
files (which include [Popcorn.js][] and [Ember.js][] submodules) and you'll need
to build the static files in order to extract and compile the localised
message catalogs, which you need to run the application ;)

To get started, clone the repo and pull down the submodules:

    git clone git@github.com:thruflo/awraamba.git
    cd awraamba
    git submodule init
    git submodule update

Edit `./etc/paste.ini` (or create your own config file) to override the
database and email account access details.  (You need to have a PostgreSQL
database running.  You may also need to make sure the thumbnails and locale
directories in your config exist).

I'd recommend you create and activate a clean [virtualenv][]:

    virtualenv --no-site-packages .
    source bin/activate

Develop the egg:

    python setup.py develop

Run [assetgen][] to compile the static files, e.g.:

    assetgen --profile=dev

Use [bolt][] to run [babel][] to compile the message catalogs:

    bolt extract
    bolt compile

Run the application using, e.g.:

    paster serve etc/paste.ini --reload

And point your browser to e.g.: [localhost:8080][].

In production, you'll want to put it behind a front end like [Nginx][] and / or
override the `[server:main]` section of the paste config.  As it stands, the 
PostgreSQL driver supports threading but not pre-forking or green threads.

[assetgen]: http://pypi.python.org/pypi/assetgen/
[awra amba experience]: http://www.awraamba.com/interactive-project/
[babel]: http://babel.edgewall.org/
[bolt]: http://pypi.python.org/pypi/bolt
[coffeescript]: http://jashkenas.github.com/coffee-script/
[ember.js]: http://www.emberjs.com/
[localhost:8080]: http://localhost:8080
[nginx]: http://nginx.org/
[pil]: http://www.pythonware.com/products/pil/
[popcorn.js]: http://popcornjs.org/
[postgresql]: http://www.postgresql.org/
[sass]: http://sass-lang.com/
[sqlalchemy]: http://www.sqlalchemy.org/
[uglifyjs]: https://github.com/mishoo/UglifyJS
[virtualenv]: http://www.virtualenv.org/en/latest/index.html#what-it-does
[weblayer]: http://packages.python.org/weblayer/
[wsgi]: http://www.wsgi.org
