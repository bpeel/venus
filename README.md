## Blogoj

Ĉi tiu deponejo estas forko de [Planet
Venus](https://github.com/rubys/venus) kun ekstraj dosieroj por regi
la retejon de [Blogaro](http://blogoj.gemelo.org/).

La ĉefa dosiero estas [blogoj.ini](blogoj.ini) kiu enhavas la liston
de blogoj. Anakaŭ estas [etoso](themes/esperanto). Ĝi simple estas la
defaŭlta etoso kun traduko al Esperanto kaj ligiloj al la sociaj
retoj.

Oni povas rekrei la retejon per la jena komando:

    python2 planet.py blogoj.ini

Por testado, antaŭ ol ruli tiun komandon estus bone ŝanĝi la
`output_dir` en `blogoj.ini`.

La deponejo ankaŭ havas la skripton
[forward-blogs.py](forward-blogs.py) kiu plusendas ligilojn al la
artikoloj al Telegram, Mastodon kaj Twitter. Ĝi ankaŭ havas kodon por
Facebook sed ĝi ne tre bone funkcias do ĝi estas malŝaltita.

## Planet

Planet is a flexible feed aggregator. It downloads news feeds published by
web sites and aggregates their content together into a single combined feed,
latest news first.  This version of Planet is named Venus as it is the
second major version.  The first version is still in wide use and is
also actively being maintained.

It uses Mark Pilgrim's Universal Feed Parser to read from CDF, RDF, RSS and
Atom feeds; Leonard Richardson's Beautiful Soup to correct markup issues;
and either Tomas Styblo's templating engine or Daniel Viellard's implementation
of XSLT to output static files in any format you can dream up.

To get started, check out the documentation in the docs directory.  If you have
any questions or comments, please don't hesitate to use the planet mailing list:

  http://lists.planetplanet.org/mailman/listinfo/devel

Keywords: feed, blog, aggregator, RSS, RDF, Atom, OPML, Python
