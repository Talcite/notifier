SELECT
  user_config.user_id AS user_id, user_config.username, user_config.tags
FROM
  user_config
WHERE
  -- Only users on the given channel
  user_config.frequency = %(frequency)s

  -- Only users with a notification waiting for them
  AND EXISTS (
    SELECT NULL FROM
      post_with_context
    WHERE
      -- Remove posts made by the user
      post_with_context.post_user_id <> user_config.user_id

      -- Only posts posted since the user was last notified
      AND post_with_context.post_posted_timestamp > user_config.notified_timestamp

      -- Only posts matching thread or post subscription criteria
      AND (
        -- Posts in threads started by the user
        post_with_context.first_post_in_thread_user_id = user_config.user_id

        -- Replies to posts made by the user
        OR post_with_context.parent_post_user_id = user_config.user_id

        -- Posts in threads subscribed to and replies to posts subscribed to
        OR EXISTS (
          SELECT NULL FROM
            manual_sub
          WHERE
            manual_sub.user_id = user_config.user_id
            AND manual_sub.thread_id = post_with_context.thread_id
            AND (
              manual_sub.post_id IS NULL  -- Threads
              OR manual_sub.post_id = post_with_context.parent_post_id  -- Post replies
            )
            AND manual_sub.sub = 1
        )
      )

      -- Remove posts/replies in/to threads/posts unsubscribed from
      AND NOT EXISTS (
        SELECT NULL FROM
          manual_sub
        WHERE
          manual_sub.user_id = user_config.user_id
          AND manual_sub.thread_id = post_with_context.thread_id
          AND (
            manual_sub.post_id IS NULL  -- Threads
            OR manual_sub.post_id = post_with_context.parent_post_id  -- Post replies
          )
          AND manual_sub.sub = -1
      )
  )