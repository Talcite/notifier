from typing import cast

import pytest

import notifier.newposts
from notifier.database.drivers.base import BaseDatabaseDriver
from notifier.wikiconnection import Connection


@pytest.mark.usefixtures("sample_database")
def test_get_new_posts_from_local_rss(sample_database: BaseDatabaseDriver):
    """Test that 'new' posts can be correctly 'downloaded' from a local RSS
    feed XML file."""

    notifier.newposts.new_posts_rss = "./sample_new_posts_feed.xml"

    fake_connection = lambda: None
    # The fake connection will not lookup any actual posts
    setattr(fake_connection, "thread", lambda w, t, p: [])

    notifier.newposts.fetch_posts_with_context(
        "local", sample_database, cast(Connection, fake_connection)
    )
