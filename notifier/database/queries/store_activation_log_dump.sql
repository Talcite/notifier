INSERT INTO
  activation_log_dump
  (
    start_timestamp,
    config_start_timestamp,
    config_end_timestamp,
    getpost_start_timestamp,
    getpost_end_timestamp,
    notify_start_timestamp,
    notify_end_timestamp,
    end_timestamp,
    sites_count,
    user_count,
    downloaded_post_count,
    downloaded_thread_count
  )
  VALUES
  (
    %(start_timestamp)s,
    %(config_start_timestamp)s,
    %(config_end_timestamp)s,
    %(getpost_start_timestamp)s,
    %(getpost_end_timestamp)s,
    %(notify_start_timestamp)s,
    %(notify_end_timestamp)s,
    %(end_timestamp)s,
    %(sites_count)s,
    %(user_count)s,
    %(downloaded_post_count)s,
    %(downloaded_thread_count)s
  )
